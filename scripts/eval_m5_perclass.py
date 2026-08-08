#!/usr/bin/env python3
"""M5 每类 AP 补测（本地 CPU 版，官方 val 通道）。

用途：补齐 per-class-ap.md 中 M5 缺失的 val active 单元格与 test 集每类 AP。
结果（2026-08-07 实测，与云端数值逐格核对一致，偏差 ≤0.003）：
  val  mAP50 0.5611（云端 0.5608）：active 0.452 ← 原缺失格
  test mAP50 0.5933（云端 0.5932）：每类 AP 见 per_class_m5_test_official.json

注意（教训）：不要走 model.predict + 自复刻 AP 的路线——predict 默认 NMS
IoU=0.7 而官方 val 用 0.6，整体 AP 会偏低约 3 个点（本脚本初版曾踩坑）。
一律用 model.val() 官方通道，batch 大小不影响 AP 数值。

用法：python scripts/eval_m5_perclass.py
输出：results/m5-fastnet-wsample/per_class_m5_{val,test}_official.json
"""
import json
from pathlib import Path

import torch
from torch import nn
import ultralytics.nn.tasks as tasks

ROOT = Path(__file__).resolve().parent.parent
WEIGHTS = ROOT / 'results' / 'm5-best.pt'
DATA_YAML = ROOT / 'data' / 'dataset' / 'data.yaml'
OUT_DIR = ROOT / 'results' / 'm5-fastnet-wsample'


class FasterBlock(nn.Module):
    """与 autodl/m5_train.py 完全一致（加载 M5 权重前必须注册）。"""
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


def main():
    from ultralytics import YOLO
    model = YOLO(str(WEIGHTS))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    expect = {'val': 0.5608, 'test': 0.5932}
    for split in ['test', 'val']:
        m = model.val(data=str(DATA_YAML), split=split, batch=16, device='cpu', verbose=False)
        pc = {m.names[i]: round(float(m.box.ap50[i]), 4) for i in range(len(m.names))}
        out = {'split': split,
               'mAP50': round(float(m.box.map50), 4),
               'mAP50-95': round(float(m.box.map), 4),
               'precision': round(float(m.box.mp), 4),
               'recall': round(float(m.box.mr), 4),
               'protocol': 'official ultralytics model.val defaults (conf=0.001, nms iou=0.6), batch=16, CPU',
               'per_class_AP50': pc}
        p = OUT_DIR / f'per_class_m5_{split}_official.json'
        p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f'[{split}] mAP50={out["mAP50"]}（云端 {expect[split]}） mAP50-95={out["mAP50-95"]}')
        for k, v in pc.items():
            print(f'  {k:14s} {v:.4f}')
        if abs(out['mAP50'] - expect[split]) > 0.005:
            print(f'[WARN] 与云端 {split} 偏差 >0.005，需人工核对！')
        print(f'[OK] 已保存 {p}')


if __name__ == '__main__':
    main()
