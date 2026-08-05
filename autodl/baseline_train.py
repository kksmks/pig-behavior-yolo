#!/usr/bin/env python3
"""基线重跑（AutoDL 版）：YOLOv11n 原版，200 轮 + patience 30 早停

用途：统一新协议（200 epochs + patience 30）后的公平对照基线。
支持 --data 指定数据集（如重切分后的 dataset-gsplit）。

用法：
  nohup python baseline_train.py > baseline200.log 2>&1 &
  nohup python baseline_train.py --data /root/autodl-tmp/dataset-gsplit > baseline-gs.log 2>&1 &
"""
import argparse
import glob
import json
from pathlib import Path

WORK = Path('/root/autodl-tmp') if Path('/root/autodl-tmp').exists() else Path('.')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default=str(WORK / 'dataset'), help='数据集目录（自动递归找 data.yaml）')
    ap.add_argument('--name', default='baseline-e200', help='实验名（结果目录名）')
    args = ap.parse_args()

    cands = glob.glob(str(Path(args.data) / '**/data.yaml'), recursive=True)
    assert cands, '未找到 data.yaml，检查数据集'
    data_yaml = cands[0]
    print('数据集:', data_yaml)

    from ultralytics import YOLO
    model = YOLO('yolo11n.pt')  # 原版基线，全量 COCO 预训练
    model.train(data=data_yaml, epochs=200, patience=30, imgsz=640, batch=16,
                device=0, project=str(WORK / 'results'), name=args.name)

    metrics = model.val()
    summary = {'mAP50': round(float(metrics.box.map50), 4),
               'mAP50-95': round(float(metrics.box.map), 4),
               'precision': round(float(metrics.box.mp), 4),
               'recall': round(float(metrics.box.mr), 4)}
    # 评测协议 v2：同时在 held-out test 集上评估（选模用 val，报告用 test，防 val 过拟合）
    metrics_test = model.val(split='test')
    summary.update({'test_mAP50': round(float(metrics_test.box.map50), 4),
                    'test_mAP50-95': round(float(metrics_test.box.map), 4)})
    out = WORK / 'results' / args.name / 'metrics.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print('指标:', summary)
    print('对照旧基线(100轮): mAP50=0.5706')
    print(f'完成。结果在 {WORK}/results/{args.name}/')


if __name__ == '__main__':
    main()
