#!/usr/bin/env python3
"""训练入口：基线与后续改进模型共用同一个脚本。

用法（本地或 Colab 均可）：
  python scripts/train.py --model yolo11n.pt --data data/neau/data.yaml --name baseline
  python scripts/train.py --model yolov8n.pt  --data data/neau/data.yaml --name yolov8n_cmp

每次训练自动在 results/<name>/ 下保存权重、曲线和 metrics.json（论文表格的数据源）。
"""
import argparse
import json
from pathlib import Path

from ultralytics import YOLO


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="yolo11n.pt", help="模型配置或预训练权重")
    ap.add_argument("--data", required=True, help="数据集 data.yaml 路径")
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--device", default="0", help="GPU 编号，CPU 则填 cpu")
    ap.add_argument("--name", default="baseline", help="实验名（results 下的子目录名）")
    args = ap.parse_args()

    model = YOLO(args.model)
    model.train(data=args.data, epochs=args.epochs, imgsz=args.imgsz, batch=args.batch,
                device=args.device, project="results", name=args.name)

    # 训练后在验证集上评估，指标写入 metrics.json，论文表格直接使用
    metrics = model.val()
    summary = {
        "model": args.model,
        "mAP50": round(float(metrics.box.map50), 4),
        "mAP50-95": round(float(metrics.box.map), 4),
        "precision": round(float(metrics.box.mp), 4),
        "recall": round(float(metrics.box.mr), 4),
    }
    out = Path("results") / args.name / "metrics.json"
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
