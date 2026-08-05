#!/usr/bin/env python3
"""效率基准（AutoDL GPU）：各模型推理速度实测（热身后 100 次均值）。

用法：python fps_bench.py
"""
import time
from pathlib import Path

import torch
from torch import nn
import ultralytics.nn.tasks as tasks


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

WORK = Path('/root/autodl-tmp')
MODELS = {
    'baseline-e200': WORK / 'results/baseline-e200/weights/best.pt',
    'm4-wsample': WORK / 'results/m4-wsample/weights/best.pt',
    'm5-fastnet-wsample': WORK / 'results/m5-fastnet-wsample/weights/best.pt',
    'yolo12n': WORK / 'results/yolo12n/weights/best.pt',
}
IMG = next((WORK / 'dataset/valid/images').glob('*'))

from ultralytics import YOLO

print(f'{"模型":<22}{"ms/图":>8}{"FPS":>8}')
for name, w in MODELS.items():
    if not w.exists():
        print(f'{name}: 权重缺失，跳过')
        continue
    model = YOLO(str(w))
    for _ in range(20):  # 预热
        model.predict(str(IMG), device=0, verbose=False)
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    N = 100
    for _ in range(N):
        model.predict(str(IMG), device=0, verbose=False)
    torch.cuda.synchronize()
    ms = (time.perf_counter() - t0) / N * 1000
    print(f'{name:<22}{ms:>8.2f}{1000/ms:>8.1f}', flush=True)
