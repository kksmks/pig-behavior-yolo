#!/usr/bin/env python3
"""导出部署模型。

两步走：
  1. 在训练机（PC/Colab）上导出 ONNX：
     python scripts/export_deploy.py --weights results/baseline/weights/best.pt --format onnx --half

  2. 把 .onnx 拷到 Jetson Nano，在 Nano 上构建 TensorRT engine（设备相关，必须在 Nano 本机执行）：
     python scripts/export_deploy.py --weights best.onnx --format engine --half

随后在 Nano 上实测 FPS / 功耗，数据写进论文 Deployment 章节。
"""
import argparse
from pathlib import Path

from ultralytics import YOLO


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--weights", required=True, help="best.pt 或 best.onnx 路径")
    ap.add_argument("--format", default="onnx", choices=["onnx", "engine"])
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--half", action="store_true", help="FP16 半精度（Nano 部署建议开启）")
    args = ap.parse_args()

    model = YOLO(args.weights)
    out = model.export(format=args.format, imgsz=args.imgsz, half=args.half, simplify=True)
    size_mb = Path(out).stat().st_size / 1024 / 1024
    print(f"导出完成: {out}  ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
