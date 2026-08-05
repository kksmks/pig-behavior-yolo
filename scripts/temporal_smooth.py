#!/usr/bin/env python3
"""时序平滑模块 —— 基于 IoU 匹配的轻量跟踪 + 行为投票。

用法（两步走）：
  # 1. 用 M5 模型对验证/测试集做推理并保存结果
  python scripts/temporal_smooth.py detect \
      --weights results/m5-fastnet-wsample/weights/best.pt \
      --data data/dataset/data.yaml \
      --split val \
      --out results/m5_predictions.json

  # 2. 对检测结果做时序平滑
  python scripts/temporal_smooth.py smooth \
      --pred results/m5_predictions.json \
      --window 3 \
      --vote-thresh 2 \
      --out results/m5_smoothed.json

  # 3. 评估时序平滑后的指标
  python scripts/temporal_smooth.py eval \
      --pred results/m5_smoothed.json \
      --split val \
      --data data/dataset/data.yaml

核心思想：
  - 不改检测器、不重训模型，纯后处理
  - 按视频序列分组 → 帧间 IoU 匹配建轨迹 → 轨迹内行为投票
  - 对 fight/lying/close-contact 等易混淆行为特别有效
"""

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np


def iou(box_a, box_b):
    """计算两个框的 IoU。输入格式: [x1, y1, x2, y2]"""
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def parse_frame_info(filename):
    """从 YOLO 图像文件名解析视频序列 ID 和帧号。

    例：2019_11_05_000002_0_jpg.rf.xxx.jpg
        → seq_id = '2019_11_05_000002', frame_num = 0
    返回 (seq_id, frame_num) 或 (None, None) 如果解析失败。
    """
    stem = Path(filename).stem
    # 先去掉 roboflow 后缀
    stem = re.sub(r'\.rf\.[a-f0-9]+$', '', stem)
    # 去掉 _jpg 后缀
    stem = re.sub(r'_jpg$', '', stem)
    # 尝试匹配 "前缀_数字" 的帧号
    parts = stem.rsplit('_', 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0], int(parts[1])
    return None, None


def match_tracks(prev_tracks, curr_dets, iou_thresh=0.5):
    """帧间 IoU 匹配。贪心算法，足够轻量。

    prev_tracks: [{track_id, last_box, class_history, conf_history}, ...]
    curr_dets:   [{box, cls, conf}, ...]
    返回: (updated_tracks, unmatched_dets)
    """
    used_prev = set()
    used_curr = set()
    matches = []

    # 计算所有 IoU
    for i, tr in enumerate(prev_tracks):
        for j, det in enumerate(curr_dets):
            score = iou(tr['last_box'], det['box'])
            if score >= iou_thresh:
                matches.append((score, i, j))

    # 按 IoU 降序贪心匹配
    matches.sort(reverse=True)
    for score, i, j in matches:
        if i not in used_prev and j not in used_curr:
            used_prev.add(i)
            used_curr.add(j)
            prev_tracks[i]['last_box'] = curr_dets[j]['box']
            prev_tracks[i]['class_history'].append(curr_dets[j]['cls'])
            prev_tracks[i]['conf_history'].append(curr_dets[j]['conf'])

    # 未匹配到的当前检测 → 新轨迹
    new_tracks = []
    for j, det in enumerate(curr_dets):
        if j not in used_curr:
            new_tracks.append({
                'track_id': len(prev_tracks) + len(new_tracks),
                'last_box': det['box'],
                'class_history': [det['cls']],
                'conf_history': [det['conf']],
            })

    # 保留匹配到的旧轨迹 + 新轨迹
    alive_tracks = [prev_tracks[i] for i in used_prev] + new_tracks
    return alive_tracks


def majority_vote(classes, vote_thresh):
    """最近 N 帧的多数投票。票数 ≥ vote_thresh 才改，否则保持最新帧结果。"""
    if not classes:
        return None
    counts = defaultdict(int)
    for c in classes:
        counts[c] += 1
    best_cls, best_cnt = max(counts.items(), key=lambda x: x[1])
    if best_cnt >= vote_thresh:
        return best_cls
    return classes[-1]  # 保持最新帧结果


def temporal_smooth_predictions(pred_dict, window=3, vote_thresh=2, iou_thresh=0.5):
    """对预测结果做时序平滑。

    pred_dict: {seq_id: [{frame_num, filename, dets: [{box, cls, conf}]}]}
    返回: 同样结构，但每帧的 det['cls'] 被投票修正。
    """
    smoothed = {}
    for seq_id, frames in pred_dict.items():
        # 按帧号排序
        frames_sorted = sorted(frames, key=lambda x: x['frame_num'])
        tracks = []
        frame_outputs = []

        for frame in frames_sorted:
            dets = frame['dets']
            if not dets:
                frame_outputs.append({
                    'frame_num': frame['frame_num'],
                    'filename': frame['filename'],
                    'dets': []
                })
                continue

            # IoU 匹配更新轨迹
            tracks = match_tracks(tracks, dets, iou_thresh)

            # 对每个轨迹做投票
            out_dets = []
            for tr in tracks:
                hist = tr['class_history'][-window:]  # 最近 N 帧
                smoothed_cls = majority_vote(hist, vote_thresh)
                # 用该轨迹最新位置、最新置信度，但类可能被投票改变
                out_dets.append({
                    'box': tr['last_box'],
                    'cls': smoothed_cls,
                    'conf': tr['conf_history'][-1],
                    'track_id': tr['track_id'],
                })

            frame_outputs.append({
                'frame_num': frame['frame_num'],
                'filename': frame['filename'],
                'dets': out_dets,
            })

        smoothed[seq_id] = frame_outputs
    return smoothed


# ---------------------------------------------------------------------------
# 子命令: detect —— 运行检测并保存 JSON
# ---------------------------------------------------------------------------

def cmd_detect(args):
    from ultralytics import YOLO

    model = YOLO(args.weights)
    # 用 model() 或 model.predict() 对数据集的某个 split 推理
    # Ultralytics 的 model.val() 有 save_json 选项
    print(f"正在推理: {args.weights} @ {args.split}")
    results = model.val(data=args.data, split=args.split, save_json=True,
                        imgsz=args.imgsz, device=args.device)

    # Ultralytics 默认把 JSON 存到 runs/detect/val/predictions.json
    # 我们复制到用户指定路径
    default_json = Path("runs/detect/val/predictions.json")
    if not default_json.exists():
        # 尝试找其他路径
        candidates = list(Path("runs").rglob("predictions.json"))
        if candidates:
            default_json = candidates[0]
        else:
            print("[错误] 找不到 predictions.json，请检查 runs/ 目录")
            return

    pred_dict = json.loads(default_json.read_text(encoding="utf-8"))
    out_path = Path(args.out)
    out_path.write_text(json.dumps(pred_dict, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    print(f"检测结果已保存: {out_path}")


# ---------------------------------------------------------------------------
# 子命令: smooth —— 对已有检测结果做时序平滑
# ---------------------------------------------------------------------------

def cmd_smooth(args):
    pred_dict = json.loads(Path(args.pred).read_text(encoding="utf-8"))

    # 如果 pred_dict 是 COCO 格式（images/annotations），先转成我们的格式
    if "images" in pred_dict and "annotations" in pred_dict:
        pred_dict = convert_coco_to_seq(pred_dict)

    smoothed = temporal_smooth_predictions(
        pred_dict, window=args.window, vote_thresh=args.vote_thresh,
        iou_thresh=args.iou_thresh)

    out_path = Path(args.out)
    out_path.write_text(json.dumps(smoothed, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    print(f"时序平滑完成: window={args.window}, vote_thresh={args.vote_thresh}")
    print(f"结果保存: {out_path}")


def convert_coco_to_seq(coco_dict):
    """把 COCO 格式的 predictions.json 转成 seq_id → frames 结构。"""
    id2img = {img['id']: img for img in coco_dict['images']}
    seq_frames = defaultdict(list)

    for ann in coco_dict['annotations']:
        img = id2img[ann['image_id']]
        filename = img['file_name']
        seq_id, frame_num = parse_frame_info(filename)
        if seq_id is None:
            seq_id = filename
            frame_num = 0

        x, y, w, h = ann['bbox']
        box = [x, y, x + w, y + h]
        # 找对应 frame_num 的 slot
        frames = seq_frames[seq_id]
        found = False
        for f in frames:
            if f['frame_num'] == frame_num:
                f['dets'].append({'box': box, 'cls': ann['category_id'], 'conf': ann.get('score', 1.0)})
                found = True
                break
        if not found:
            frames.append({
                'frame_num': frame_num,
                'filename': filename,
                'dets': [{'box': box, 'cls': ann['category_id'], 'conf': ann.get('score', 1.0)}]
            })

    return {k: sorted(v, key=lambda x: x['frame_num']) for k, v in seq_frames.items()}


# ---------------------------------------------------------------------------
# 子命令: eval —— 对比单帧 vs. 时序平滑后的每类 AP（需要标注真值）
# ---------------------------------------------------------------------------

def cmd_eval(args):
    """简化版评估：统计时序平滑前后各类别的变化。"""
    import yaml

    # 读取类别名
    data_yaml = yaml.safe_load(Path(args.data).read_text(encoding="utf-8"))
    names = data_yaml.get("names", {})
    if isinstance(names, dict):
        names = {int(k): v for k, v in names.items()}
    else:
        names = {i: v for i, v in enumerate(names)}

    pred_dict = json.loads(Path(args.pred).read_text(encoding="utf-8"))

    # 统计每类的检测数量和占比（简化指标，完整 mAP 需用官方 val）
    cls_counts = defaultdict(int)
    total = 0
    for seq_id, frames in pred_dict.items():
        for frame in frames:
            for det in frame['dets']:
                cls_counts[det['cls']] += 1
                total += 1

    print(f"\n时序平滑后预测统计 (总计 {total} 框):")
    print(f"{'类别ID':>6} | {'类别名':<15} | {'数量':>6} | {'占比':>6}")
    print("-" * 45)
    for cls_id in sorted(cls_counts.keys()):
        cnt = cls_counts[cls_id]
        name = names.get(cls_id, f"class_{cls_id}")
        print(f"{cls_id:>6} | {name:<15} | {cnt:>6} | {cnt/total*100:>5.1f}%")

    print("\n[提示] 完整的 mAP50 对比请用 scripts/train.py 的 val 功能")
    print("      或 ultralytics 官方 val(save_json=True) 后计算。")


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    # detect
    p = sub.add_parser("detect", help="运行检测并保存结果为 JSON")
    p.add_argument("--weights", required=True, help="best.pt 路径")
    p.add_argument("--data", required=True, help="data.yaml 路径")
    p.add_argument("--split", default="val", choices=["train", "val", "test"])
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--device", default="0")
    p.add_argument("--out", default="results/temporal/predictions.json")
    p.set_defaults(func=cmd_detect)

    # smooth
    p = sub.add_parser("smooth", help="对检测结果做时序平滑")
    p.add_argument("--pred", required=True, help="预测 JSON 路径")
    p.add_argument("--window", type=int, default=3, help="投票窗口帧数")
    p.add_argument("--vote-thresh", type=int, default=2, help="多数票阈值")
    p.add_argument("--iou-thresh", type=float, default=0.5, help="IoU 匹配阈值")
    p.add_argument("--out", default="results/temporal/smoothed.json")
    p.set_defaults(func=cmd_smooth)

    # eval
    p = sub.add_parser("eval", help="统计时序平滑后的类别分布")
    p.add_argument("--pred", required=True, help="平滑后的 JSON 路径")
    p.add_argument("--data", required=True, help="data.yaml 路径")
    p.add_argument("--split", default="val")
    p.set_defaults(func=cmd_eval)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
