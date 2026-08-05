#!/usr/bin/env python3
"""对照实验组（AutoDL 版）：4 个主流模型串行训练 + val/test 双评估

选型依据（文献审核 2026-07-27）：
  TriPerceptNet(Frontiers 2025) 用 RT-DETR/v5n/v6n/v8n/v11n；
  MEI-YOLOv11(INMATEH) 用 v5-v12+RT-DETR；玉米表型(MDPI 2025) 用 FasterRCNN/SSD/RT-DETR/v5n/v8n。
  本方四选：YOLOv5n(经典锚点)、YOLOv8n(中坚引用锚点)、YOLOv12n(最新代)、RT-DETR-l(Transformer 范式)。
  Faster R-CNN/SSD 已属效率淘汰项，Related Work 提及即可，不跑。
协议：与基线完全相同的数据（原始 dataset，非过采样）、200 轮 + patience 30、
  输入 640、默认超参——保证公平对比（审稿点）。

用法：nohup python compare_fleet.py > fleet.log 2>&1 &
"""
import glob
import json
from pathlib import Path

WORK = Path('/root/autodl-tmp') if Path('/root/autodl-tmp').exists() else Path('.')
FLEET = [
    ('rtdetr-l.pt', 8, 'RTDETR'),
    ('yolov8n.pt', 16, 'YOLO'),
    ('yolo12n.pt', 16, 'YOLO'),
    ('yolov5n.pt', 16, 'YOLO'),
]


def main():
    cands = glob.glob(str(WORK / 'dataset' / '**/data.yaml'), recursive=True)
    assert cands, '未找到 data.yaml'
    data_yaml = cands[0]
    print('数据集:', data_yaml)

    from ultralytics import RTDETR, YOLO
    for weights, batch, kind in FLEET:
        name = weights.replace('.pt', '')
        print(f'\n{"="*60}\n开始训练: {name} (batch={batch})\n{"="*60}', flush=True)
        try:
            model = RTDETR(weights) if kind == 'RTDETR' else YOLO(weights)
            model.train(data=data_yaml, epochs=200, patience=30, imgsz=640,
                        batch=batch, device=0, project=str(WORK / 'results'), name=name)
            metrics = model.val()
            summary = {'mAP50': round(float(metrics.box.map50), 4),
                       'mAP50-95': round(float(metrics.box.map), 4),
                       'precision': round(float(metrics.box.mp), 4),
                       'recall': round(float(metrics.box.mr), 4)}
            metrics_test = model.val(split='test')
            summary.update({'test_mAP50': round(float(metrics_test.box.map50), 4),
                            'test_mAP50-95': round(float(metrics_test.box.map), 4)})
            out = WORK / 'results' / name / 'metrics.json'
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(summary, indent=2), encoding='utf-8')
            print(f'{name} 完成: {summary}', flush=True)
        except Exception as e:
            print(f'!! {name} 失败: {e}', flush=True)
            continue
    print('\n全部对照组训练结束')


if __name__ == '__main__':
    main()
