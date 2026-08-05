#!/usr/bin/env python3
"""时序平滑 mAP 评估器 —— 官方协议口径（IoU 0.5:0.05:0.95，10 阈值）。

对比"单帧检测"与"IoU 跟踪 + 轨迹投票平滑"两组预测在验证集上的
mAP50 / mAP50-95 / 每类 AP50，判决时序平滑模块是否有效。

用法：
  python scripts/eval_temporal_map.py \
      --raw results/temporal/predictions_full.json \
      --smooth results/temporal/smoothed_full.json \
      --labels data/dataset/valid/labels \
      --out results/temporal/map_eval.txt

口径说明（诚实声明）：
  - 匹配与 AP 计算复刻 ultralytics 官方 val 协议（box_iou + ap_per_class，
    101 点插值），保证与 EXPERIMENT_LOG 中训练指标可比。
  - 但输入预测是在 conf=0.25 下截断的（推理时默认值），低于官方 val 的
    conf=0.001 → 绝对数值会低于正式 val 指标（召回曲线被截断）。
    两组预测同源同截断，相对比较公平；论文若引用绝对值需按官方协议重测。
  - 图片已统一 640x640，预测框为像素坐标，GT 由归一化 cxcywh 换算。
"""

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from ultralytics.utils.metrics import ap_per_class, box_iou

# data.yaml 类序（字母序，训练/评估的唯一事实来源）
NAMES = ['active', 'drink', 'eat', 'fight', 'investigating',
         'lying', 'nose-to-nose', 'sitting', 'standing', 'walk']
NC = len(NAMES)
IOUV = np.linspace(0.5, 0.95, 10)  # 官方 10 个 IoU 阈值
IMG_SIZE = 640.0


def load_gt(labels_dir):
    """读取全部 YOLO 标注 → {stem: (cls array, boxes xyxy 像素)}"""
    gt = {}
    for txt in sorted(Path(labels_dir).glob('*.txt')):
        cls_list, box_list = [], []
        for line in txt.read_text(encoding='utf-8').splitlines():
            parts = line.split()
            if len(parts) < 5:
                continue
            c, cx, cy, w, h = int(parts[0]), *map(float, parts[1:5])
            cls_list.append(c)
            x1 = (cx - w / 2) * IMG_SIZE
            y1 = (cy - h / 2) * IMG_SIZE
            box_list.append([x1, y1, (cx + w / 2) * IMG_SIZE, (cy + h / 2) * IMG_SIZE])
        gt[txt.stem] = (np.array(cls_list, dtype=int),
                        np.array(box_list, dtype=float).reshape(-1, 4))
    return gt


def load_preds(pred_json):
    """seq_frames 结构 → {stem: (cls, conf, boxes)}"""
    data = json.loads(Path(pred_json).read_text(encoding='utf-8'))
    out = {}
    for frames in data.values():
        for f in frames:
            stem = Path(f['filename']).stem
            dets = f['dets']
            if dets:
                cls = np.array([d['cls'] for d in dets], dtype=int)
                conf = np.array([d['conf'] for d in dets], dtype=float)
                boxes = np.array([d['box'] for d in dets], dtype=float)
            else:
                cls = np.zeros(0, dtype=int)
                conf = np.zeros(0, dtype=float)
                boxes = np.zeros((0, 4), dtype=float)
            out[stem] = (cls, conf, boxes)
    return out


def match_batch(gt_cls, gt_boxes, p_cls, p_boxes):
    """复刻 ultralytics process_batch：返回 (n_pred, 10) 的 TP 矩阵。"""
    correct = np.zeros((len(p_cls), len(IOUV)), dtype=bool)
    if len(gt_cls) == 0 or len(p_cls) == 0:
        return correct
    iou = box_iou(torch.from_numpy(gt_boxes), torch.from_numpy(p_boxes)).numpy()
    correct_class = (gt_cls[:, None] == p_cls[None, :])
    iou = iou * correct_class
    x = np.nonzero(iou >= IOUV[0])
    if len(x[0]) == 0:
        return correct
    matches = np.concatenate(
        [np.stack(x, 1), iou[x[0], x[1]][:, None]], 1)  # (n, 3): gt, pred, iou
    # 按 IoU 降序 → 每个预测只留最优 GT → 每个 GT 只留最优预测
    matches = matches[matches[:, 2].argsort()[::-1]]
    matches = matches[np.unique(matches[:, 1], return_index=True)[1]]
    matches = matches[matches[:, 2].argsort()[::-1]]
    matches = matches[np.unique(matches[:, 0], return_index=True)[1]]
    m0, m1 = matches[:, 0].astype(int), matches[:, 1].astype(int)
    correct[m1] = iou[m0, m1][:, None] >= IOUV
    return correct


def evaluate(preds, gt):
    """全数据集跑匹配 → ap_per_class → 返回 (每类AP50 array, mAP50, mAP50-95)"""
    stats_tp, stats_conf, stats_pcls, stats_tcls = [], [], [], []
    for stem, (gt_cls, gt_boxes) in gt.items():
        p_cls, p_conf, p_boxes = preds.get(stem,
                                           (np.zeros(0, int), np.zeros(0), np.zeros((0, 4))))
        # 按置信度降序（官方协议）
        order = p_conf.argsort()[::-1]
        p_cls, p_conf, p_boxes = p_cls[order], p_conf[order], p_boxes[order]
        tp = match_batch(gt_cls, gt_boxes, p_cls, p_boxes)
        stats_tp.append(tp)
        stats_conf.append(p_conf)
        stats_pcls.append(p_cls)
        stats_tcls.append(gt_cls)

    tp = np.concatenate(stats_tp, 0)
    conf = np.concatenate(stats_conf, 0)
    p_cls = np.concatenate(stats_pcls, 0)
    t_cls = np.concatenate(stats_tcls, 0)

    results = ap_per_class(tp, conf, p_cls, t_cls,
                           plot=False, names=dict(enumerate(NAMES)))
    # 返回值: tp, fp, p, r, f1, ap, unique_classes, ...
    ap = results[5]            # (nc, 10)
    ucls = results[6]          # 有 GT 的类别
    ap50_full = np.zeros(NC)
    ap50_full[ucls] = ap[:, 0]
    map50 = ap[:, 0].mean()
    map5095 = ap.mean()
    return ap50_full, map50, map5095


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--raw', required=True, help='单帧预测 JSON')
    ap.add_argument('--smooth', required=True, help='平滑后预测 JSON')
    ap.add_argument('--labels', required=True, help='GT 标注目录 (YOLO txt)')
    ap.add_argument('--out', default='results/temporal/map_eval.txt')
    args = ap.parse_args()

    gt = load_gt(args.labels)
    print(f"[OK] GT 加载: {len(gt)} 张标注")
    raw = load_preds(args.raw)
    sm = load_preds(args.smooth)
    print(f"[OK] 预测加载: 单帧 {len(raw)} 帧 / 平滑 {len(sm)} 帧")

    lines = []
    def out(s=''):
        print(s)
        lines.append(s)

    out('=' * 64)
    out('时序平滑 mAP 评估（官方协议: IoU 0.5-0.95, 101 点插值 AP）')
    out('注意: 输入预测截断于 conf=0.25，绝对值低于正式 val；相对比较公平')
    out('=' * 64)

    raw_ap, raw_m50, raw_m95 = evaluate(raw, gt)
    out(f"单帧检测   mAP50 = {raw_m50:.4f} | mAP50-95 = {raw_m95:.4f}")
    sm_ap, sm_m50, sm_m95 = evaluate(sm, gt)
    out(f"时序平滑   mAP50 = {sm_m50:.4f} | mAP50-95 = {sm_m95:.4f}")
    out(f"差值       mAP50 = {sm_m50 - raw_m50:+.4f} | "
        f"mAP50-95 = {sm_m95 - raw_m95:+.4f}")

    out('')
    out(f"{'类别':<15} | {'单帧AP50':>8} | {'时序AP50':>8} | {'差值':>8}")
    out('-' * 52)
    for i, name in enumerate(NAMES):
        out(f"{name:<15} | {raw_ap[i]:>8.4f} | {sm_ap[i]:>8.4f} | "
            f"{sm_ap[i] - raw_ap[i]:>+8.4f}")
    out('-' * 52)
    out(f"{'mAP50':<15} | {raw_m50:>8.4f} | {sm_m50:>8.4f} | "
        f"{sm_m50 - raw_m50:>+8.4f}")
    out('=' * 64)

    Path(args.out).write_text('\n'.join(lines), encoding='utf-8')
    print(f"\n[OK] 报告已保存: {args.out}")


if __name__ == '__main__':
    main()
