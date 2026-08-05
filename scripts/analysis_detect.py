#!/usr/bin/env python3
"""难例检测对比图（本地 CPU）：基线模型在密集/遮挡场景下的检测效果。

输出：results/analysis/detections/<图片名>_det.jpg
在 E:\pig-behavior-yolo 下运行：python scripts/analysis_detect.py
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import cv2
from ultralytics import YOLO


def main():
    model = YOLO('results/baseline/weights/best.pt')
    out_dir = Path('results/analysis/detections')
    out_dir.mkdir(parents=True, exist_ok=True)

    # 选密集猪群场景（2019_11_28 序列）+ 打斗场景
    samples = sorted(Path('data/dataset/test/images').glob('2019_11_28*'))[:4]
    for p in samples:
        results = model.predict(str(p), conf=0.25, device='cpu', verbose=False)[0]
        annotated = results.plot()
        out = out_dir / f'{p.stem}_det.jpg'
        cv2.imwrite(str(out), annotated)
        n = len(results.boxes)
        print(f'{p.name}: 检出 {n} 个目标 → {out}')


if __name__ == '__main__':
    main()
