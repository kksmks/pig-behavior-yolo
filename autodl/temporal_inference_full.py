#!/usr/bin/env python3
"""AutoDL 全量时序推理 —— 在云端 GPU 上跑完整验证集（1123 张）+ 时序平滑 + 对比。

用法（在 AutoDL 实例上执行）：
  nohup python autodl/temporal_inference_full.py > temporal.log 2>&1 &

输出：
  /root/autodl-tmp/results/temporal/predictions_full.json   —— 单帧检测结果
  /root/autodl-tmp/results/temporal/smoothed_full.json      —— 时序平滑结果
  /root/autodl-tmp/results/temporal/compare.txt             —— 对比报告

数据要求：
  - 数据集已放在 /root/autodl-tmp/dataset/（YOLO 格式）
  - M5 权重已放在 /root/autodl-tmp/results/m5-fastnet-wsample/weights/best.pt
    或 /root/autodl-tmp/m5-best.pt
"""

import argparse
import json
import re
import time
from collections import defaultdict
from pathlib import Path

import torch
from torch import nn
import ultralytics.nn.tasks as tasks

WORK = Path('/root/autodl-tmp') if Path('/root/autodl-tmp').exists() else Path('.')

# ---------------------------------------------------------------------------
# 注册 FasterBlock
# ---------------------------------------------------------------------------

class FasterBlock(nn.Module):
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
    used_prev, used_curr = set(), set()
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


CLS_NAMES = {
    0: 'nose-to-nose', 1: 'standing', 2: 'investigating',
    3: 'eat', 4: 'active', 5: 'walk', 6: 'drink',
    7: 'sitting', 8: 'fight', 9: 'lying'
}

# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--weights', default=str(WORK / 'results' / 'm5-fastnet-wsample' / 'weights' / 'best.pt'))
    ap.add_argument('--data', default=str(WORK / 'dataset' / 'data.yaml'))
    ap.add_argument('--split', default='val')
    ap.add_argument('--window', type=int, default=3)
    ap.add_argument('--vote-thresh', type=int, default=2)
    ap.add_argument('--out-dir', default=str(WORK / 'results' / 'temporal'))
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- 1. 找图片 ----
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
        print('[错误] 找不到图片目录')
        for c in candidates:
            print(f'  {c}')
        return

    img_paths = sorted(split_dir.glob('*.jpg')) + sorted(split_dir.glob('*.png'))
    print(f'[INFO] 共 {len(img_paths)} 张图，GPU 推理中...')

    # ---- 2. 加载模型（GPU）----
    model = YOLO(args.weights)
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    print(f'[OK] 模型加载: {args.weights} @ {device}')

    # ---- 3. 推理 ----
    t0 = time.time()
    seq_frames = defaultdict(list)
    for idx, p in enumerate(img_paths):
        seq_id, frame_num = parse_frame_info(p.name)
        if seq_id is None:
            seq_id, frame_num = p.stem, 0

        results = model(p, verbose=False, device=device)
        r = results[0]
        dets = []
        if r.boxes is not None:
            for box, cls_id, conf in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
                dets.append({'box': box.tolist(), 'cls': int(cls_id.item()), 'conf': round(float(conf.item()), 4)})

        seq_frames[seq_id].append({'frame_num': frame_num, 'filename': p.name, 'dets': dets})

        if (idx + 1) % 100 == 0 or idx == len(img_paths) - 1:
            elapsed = time.time() - t0
            fps = (idx + 1) / elapsed
            print(f'  [{idx+1}/{len(img_paths)}] {fps:.1f} img/s, 累计 {elapsed:.0f}s')

    pred_path = out_dir / 'predictions_full.json'
    pred_path.write_text(json.dumps(dict(seq_frames), indent=2, ensure_ascii=False), encoding='utf-8')
    total_dets = sum(len(f['dets']) for frames in seq_frames.values() for f in frames)
    print(f'[OK] 单帧预测已保存: {pred_path} ({len(seq_frames)} 序列, {len(img_paths)} 帧, {total_dets} 框)')

    # ---- 4. 时序平滑 ----
    print('[INFO] 时序平滑中...')
    smoothed = temporal_smooth_predictions(dict(seq_frames), window=args.window, vote_thresh=args.vote_thresh)
    smooth_path = out_dir / 'smoothed_full.json'
    smooth_path.write_text(json.dumps(smoothed, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'[OK] 时序平滑已保存: {smooth_path}')

    # ---- 5. 对比报告 ----
    print('[INFO] 生成对比报告...')
    raw_counts, sm_counts, changes = defaultdict(int), defaultdict(int), defaultdict(int)
    for seq_id in seq_frames:
        rf = {f['filename']: f for f in seq_frames[seq_id]}
        sf = {f['filename']: f for f in smoothed.get(seq_id, [])}
        for fname in rf:
            for r, s in zip(rf[fname]['dets'], sf.get(fname, {}).get('dets', [])):
                raw_counts[r['cls']] += 1
                sm_counts[s['cls']] += 1
                if r['cls'] != s['cls']:
                    changes[(r['cls'], s['cls'])] += 1

    lines = []
    lines.append('=' * 60)
    lines.append('单帧 vs 时序平滑 全量验证集对比报告')
    lines.append('=' * 60)
    lines.append(f'{"类别":<15} | {"单帧":>8} | {"时序":>8} | {"变化":>6} | {"变化率":>6}')
    lines.append('-' * 60)
    total_raw = sum(raw_counts.values())
    for cid in sorted(set(list(raw_counts.keys()) + list(sm_counts.keys()))):
        r, s = raw_counts[cid], sm_counts[cid]
        rate = (s - r) / r * 100 if r > 0 else 0
        lines.append(f'{CLS_NAMES.get(cid, str(cid)):<15} | {r:>8} | {s:>8} | {s-r:>+6} | {rate:>+5.1f}%')
    lines.append('=' * 60)

    if changes:
        lines.append('\n标签改变 Top 10:')
        for (fr, to), cnt in sorted(changes.items(), key=lambda x: -x[1])[:10]:
            lines.append(f'  {CLS_NAMES.get(fr, fr)} → {CLS_NAMES.get(to, to)}: {cnt} 次')
        changed = sum(changes.values())
        lines.append(f'\n总计 {changed} / {total_raw} 个框被改变 ({changed/total_raw*100:.1f}%)')
    lines.append('=' * 60)

    report = '\n'.join(lines)
    print('\n' + report)

    report_path = out_dir / 'compare.txt'
    report_path.write_text(report, encoding='utf-8')
    print(f'[OK] 报告已保存: {report_path}')

    # ---- 6. 打包结果 ----
    import shutil
    zip_path = out_dir / 'temporal_results.zip'
    shutil.make_archive(str(zip_path).replace('.zip', ''), 'zip', root_dir=out_dir)
    print(f'[OK] 结果已打包: {zip_path}')
    print(f'[DONE] 总耗时: {time.time()-t0:.0f} 秒')


if __name__ == '__main__':
    main()
