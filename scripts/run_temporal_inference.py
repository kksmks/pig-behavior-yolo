#!/usr/bin/env python3
"""M5 时序推理脚本 —— 本地 CPU 运行。

用法：
  # 1. 对验证集跑推理（保存 JSON）
  python scripts/run_temporal_inference.py infer --weights results/m5-best.pt \
      --data data/dataset/data.yaml --split val --max-images 50

  # 2. 应用时序平滑
  python scripts/run_temporal_inference.py smooth \
      --pred results/temporal/predictions.json --window 3 --vote-thresh 2

  # 3. 对比单帧 vs 时序结果
  python scripts/run_temporal_inference.py compare \
      --raw results/temporal/predictions.json \
      --smooth results/temporal/smoothed.json
"""

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. 注册 FasterBlock（加载 M5 权重必需）
# ---------------------------------------------------------------------------
import torch
from torch import nn
import ultralytics.nn.tasks as tasks


class FasterBlock(nn.Module):
    """FasterNet Block：PConv + 两个逐点卷积 + 残差。"""
    def __init__(self, dim, n_div=4, expand=1):
        super().__init__()
        self.dim_conv3 = dim // n_div
        self.dim_untouched = dim - self.dim_conv3
        self.pconv = nn.Conv2d(self.dim_conv3, self.dim_conv3, 3, 1, 1, bias=False)
        hidden = dim * expand
        self.pw1 = nn.Conv2d(dim, hidden, 1, bias=False)
        self.bn1 = nn.BatchNorm2d(hidden)
        self.act = nn.ReLU(inplace=True)
        self.pw2 = nn.Conv2d(hidden, dim, 1, bias=False)
        self.bn2 = nn.BatchNorm2d(dim)

    def forward(self, x):
        x1, x2 = torch.split(x, [self.dim_conv3, self.dim_untouched], 1)
        x1 = self.pconv(x1)
        y = torch.cat([x1, x2], 1)
        y = self.act(self.bn1(self.pw1(y)))
        y = self.bn2(self.pw2(y))
        return x + y


tasks.FasterBlock = FasterBlock
print("[OK] FasterBlock 已注册到 ultralytics")

from ultralytics import YOLO

# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------


def parse_frame_info(filename):
    stem = Path(filename).stem
    stem = re.sub(r'\.rf\.[a-f0-9]+$', '', stem)
    stem = re.sub(r'_jpg$', '', stem)
    parts = stem.rsplit('_', 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0], int(parts[1])
    return None, None


def iou(box_a, box_b):
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def match_tracks(prev_tracks, curr_dets, iou_thresh=0.5):
    used_prev = set()
    used_curr = set()
    matches = []
    for i, tr in enumerate(prev_tracks):
        for j, det in enumerate(curr_dets):
            score = iou(tr['last_box'], det['box'])
            if score >= iou_thresh:
                matches.append((score, i, j))
    matches.sort(reverse=True)
    for score, i, j in matches:
        if i not in used_prev and j not in used_curr:
            used_prev.add(i)
            used_curr.add(j)
            prev_tracks[i]['last_box'] = curr_dets[j]['box']
            prev_tracks[i]['class_history'].append(curr_dets[j]['cls'])
            prev_tracks[i]['conf_history'].append(curr_dets[j]['conf'])

    new_tracks = []
    for j, det in enumerate(curr_dets):
        if j not in used_curr:
            new_tracks.append({
                'track_id': len(prev_tracks) + len(new_tracks),
                'last_box': det['box'],
                'class_history': [det['cls']],
                'conf_history': [det['conf']],
            })
    return [prev_tracks[i] for i in used_prev] + new_tracks


def majority_vote(classes, vote_thresh):
    if not classes:
        return None
    counts = defaultdict(int)
    for c in classes:
        counts[c] += 1
    best_cls, best_cnt = max(counts.items(), key=lambda x: x[1])
    return best_cls if best_cnt >= vote_thresh else classes[-1]


def temporal_smooth_predictions(pred_dict, window=3, vote_thresh=2, iou_thresh=0.5):
    smoothed = {}
    for seq_id, frames in pred_dict.items():
        frames_sorted = sorted(frames, key=lambda x: x['frame_num'])
        tracks = []
        frame_outputs = []
        for frame in frames_sorted:
            dets = frame['dets']
            if not dets:
                frame_outputs.append({'frame_num': frame['frame_num'], 'filename': frame['filename'], 'dets': []})
                continue
            tracks = match_tracks(tracks, dets, iou_thresh)
            out_dets = []
            for tr in tracks:
                hist = tr['class_history'][-window:]
                smoothed_cls = majority_vote(hist, vote_thresh)
                out_dets.append({'box': tr['last_box'], 'cls': smoothed_cls, 'conf': tr['conf_history'][-1], 'track_id': tr['track_id']})
            frame_outputs.append({'frame_num': frame['frame_num'], 'filename': frame['filename'], 'dets': out_dets})
        smoothed[seq_id] = frame_outputs
    return smoothed


# 类序必须与 data.yaml 一致（字母序）——曾误用 Roboflow 展示序导致
# compare 报告类名整体错标（计数不错、名字错），2026-08-05 修复。
CLS_NAMES = {
    0: 'active', 1: 'drink', 2: 'eat', 3: 'fight', 4: 'investigating',
    5: 'lying', 6: 'nose-to-nose', 7: 'sitting', 8: 'standing', 9: 'walk'
}

# ---------------------------------------------------------------------------
# 子命令: infer
# ---------------------------------------------------------------------------


def cmd_infer(args):
    model = YOLO(args.weights)
    print(f"[OK] 模型加载: {args.weights}")

    data_yaml = Path(args.data)
    split_name = args.split if args.split != 'val' else 'valid'
    candidates = [
        data_yaml.parent / split_name / 'images',
        data_yaml.parent / f'images/{args.split}',
        data_yaml.parent / args.split / 'images',
    ]
    split_dir = None
    for c in candidates:
        if c.exists() and any(c.glob('*.jpg')):
            split_dir = c
            break
    if split_dir is None:
        print("[错误] 找不到图片目录，尝试路径:")
        for c in candidates:
            print(f"  {c} {'(有图)' if c.exists() and any(c.glob('*.jpg')) else '(无)'}")
        return

    print(f"[OK] 图片目录: {split_dir}")
    img_paths = sorted(split_dir.glob('*.jpg')) + sorted(split_dir.glob('*.png'))
    if args.max_images:
        img_paths = img_paths[:args.max_images]
    print(f"[INFO] 共 {len(img_paths)} 张图")

    seq_frames = defaultdict(list)
    for idx, p in enumerate(img_paths):
        seq_id, frame_num = parse_frame_info(p.name)
        if seq_id is None:
            seq_id, frame_num = p.stem, 0

        results = model(p, verbose=False)
        r = results[0]
        dets = []
        if r.boxes is not None:
            for box, cls_id, conf in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
                dets.append({'box': box.tolist(), 'cls': int(cls_id.item()), 'conf': round(float(conf.item()), 4)})

        seq_frames[seq_id].append({'frame_num': frame_num, 'filename': p.name, 'dets': dets})
        if len(img_paths) <= 50 or (idx + 1) % 50 == 0:
            print(f"  [{idx+1}/{len(img_paths)}] {p.name} → {len(dets)} 框")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(seq_frames), indent=2, ensure_ascii=False), encoding='utf-8')
    total = sum(len(f['dets']) for frames in seq_frames.values() for f in frames)
    print(f"[OK] 已保存: {out} ({len(seq_frames)} 序列, {len(img_paths)} 帧, {total} 框)")


# ---------------------------------------------------------------------------
# 子命令: smooth
# ---------------------------------------------------------------------------


def cmd_smooth(args):
    pred = json.loads(Path(args.pred).read_text(encoding='utf-8'))
    smoothed = temporal_smooth_predictions(pred, window=args.window, vote_thresh=args.vote_thresh)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(smoothed, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"[OK] 时序平滑完成: {args.out}")


# ---------------------------------------------------------------------------
# 子命令: compare
# ---------------------------------------------------------------------------


def cmd_compare(args):
    raw = json.loads(Path(args.raw).read_text(encoding='utf-8'))
    sm = json.loads(Path(args.smooth).read_text(encoding='utf-8'))

    raw_counts, sm_counts, changes = defaultdict(int), defaultdict(int), defaultdict(int)
    for seq_id in raw:
        rf = {f['filename']: f for f in raw[seq_id]}
        sf = {f['filename']: f for f in sm.get(seq_id, [])}
        for fname in rf:
            for r, s in zip(rf[fname]['dets'], sf.get(fname, {}).get('dets', [])):
                raw_counts[r['cls']] += 1
                sm_counts[s['cls']] += 1
                if r['cls'] != s['cls']:
                    changes[(r['cls'], s['cls'])] += 1

    print("\n" + "="*60)
    print("单帧 vs 时序平滑 类别分布对比")
    print("="*60)
    print(f"{'类别':<15} | {'单帧':>8} | {'时序':>8} | {'变化':>6}")
    print("-"*60)
    for cid in sorted(set(list(raw_counts.keys()) + list(sm_counts.keys()))):
        r, s = raw_counts[cid], sm_counts[cid]
        print(f"{CLS_NAMES.get(cid, str(cid)):<15} | {r:>8} | {s:>8} | {s-r:>+6}")

    if changes:
        print("\n标签改变 top10:")
        for (fr, to), cnt in sorted(changes.items(), key=lambda x: -x[1])[:10]:
            print(f"  {CLS_NAMES.get(fr, fr)} → {CLS_NAMES.get(to, to)}: {cnt} 次")
    print("="*60)


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("infer", help="推理并保存 JSON")
    p.add_argument("--weights", required=True)
    p.add_argument("--data", required=True)
    p.add_argument("--split", default="val")
    p.add_argument("--max-images", type=int, default=None)
    p.add_argument("--out", default="results/temporal/predictions.json")
    p.set_defaults(func=cmd_infer)

    p = sub.add_parser("smooth", help="时序平滑")
    p.add_argument("--pred", required=True)
    p.add_argument("--window", type=int, default=3)
    p.add_argument("--vote-thresh", type=int, default=2)
    p.add_argument("--out", default="results/temporal/smoothed.json")
    p.set_defaults(func=cmd_smooth)

    p = sub.add_parser("compare", help="对比单帧 vs 时序")
    p.add_argument("--raw", required=True)
    p.add_argument("--smooth", required=True)
    p.set_defaults(func=cmd_compare)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
