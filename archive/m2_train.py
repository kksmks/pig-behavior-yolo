#!/usr/bin/env python3
"""M2 训练（AutoDL 版）：YOLOv11n + EMAR 残差注意力 @ 颈部 P3

用法：
  python m2_train.py --dry-run                       # 只验证结构，不训练（约 1 分钟）
  nohup python m2_train.py > m2.log 2>&1 &           # 后台训练（约 1-2h/3090）
  tail -f m2.log                                     # 看进度
"""
import argparse
import glob
import json
import os
import re
from pathlib import Path

import torch
from torch import nn
import ultralytics.nn.tasks as tasks


class EMA(nn.Module):
    """Efficient Multi-Scale Attention (ICASSP 2023)，输入输出通道数不变。"""
    def __init__(self, channels, factor=8):
        super().__init__()
        self.groups = factor
        assert channels // self.groups > 0
        self.softmax = nn.Softmax(-1)
        self.agp = nn.AdaptiveAvgPool2d((1, 1))
        self.pool_h = nn.AdaptiveAvgPool2d((None, 1))
        self.pool_w = nn.AdaptiveAvgPool2d((1, None))
        self.gn = nn.GroupNorm(channels // self.groups, channels // self.groups)
        self.conv1x1 = nn.Conv2d(channels // self.groups, channels // self.groups, 1)
        self.conv3x3 = nn.Conv2d(channels // self.groups, channels // self.groups, 3, padding=1)

    def forward(self, x):
        b, c, h, w = x.size()
        group_x = x.reshape(b * self.groups, -1, h, w)
        x_h = self.pool_h(group_x)
        x_w = self.pool_w(group_x).permute(0, 1, 3, 2)
        hw = self.conv1x1(torch.cat([x_h, x_w], dim=2))
        x_h, x_w = torch.split(hw, [h, w], dim=2)
        x1 = self.gn(group_x * x_h.sigmoid() * x_w.permute(0, 1, 3, 2).sigmoid())
        x2 = self.conv3x3(group_x)
        x11 = self.softmax(self.agp(x1).reshape(b * self.groups, -1, 1).permute(0, 2, 1))
        x12 = x2.reshape(b * self.groups, c // self.groups, -1)
        x21 = self.softmax(self.agp(x2).reshape(b * self.groups, -1, 1).permute(0, 2, 1))
        x22 = x1.reshape(b * self.groups, c // self.groups, -1)
        weights = (torch.matmul(x11, x12) + torch.matmul(x21, x22)).reshape(b * self.groups, 1, h, w)
        return (group_x * weights.sigmoid()).reshape(b, c, h, w)


class EMAR(nn.Module):
    """EMA 的残差封装：y = x + EMA(x)，插入预训练网络不破坏原特征分布。"""
    def __init__(self, channels):
        super().__init__()
        self.ema = EMA(channels)

    def forward(self, x):
        return x + self.ema(x)


tasks.EMA = EMA
tasks.EMAR = EMAR

YAML_TEXT = r'''
nc: 10
scales:
  n: [0.50, 0.25, 1024]
backbone:
  - [-1, 1, Conv, [64, 3, 2]]
  - [-1, 1, Conv, [128, 3, 2]]
  - [-1, 2, C3k2, [256, False, 0.25]]
  - [-1, 1, Conv, [256, 3, 2]]
  - [-1, 2, C3k2, [512, False, 0.25]]
  - [-1, 1, Conv, [512, 3, 2]]
  - [-1, 2, C3k2, [512, True]]
  - [-1, 1, Conv, [1024, 3, 2]]
  - [-1, 2, C3k2, [1024, True]]
  - [-1, 1, SPPF, [1024, 5]]
  - [-1, 2, C2PSA, [1024]]
head:
  - [-1, 1, nn.Upsample, [None, 2, 'nearest']]
  - [[-1, 6], 1, Concat, [1]]
  - [-1, 2, C3k2, [512, False]]
  - [-1, 1, nn.Upsample, [None, 2, 'nearest']]
  - [[-1, 4], 1, Concat, [1]]
  - [-1, 2, C3k2, [256, False]]
  - [-1, 1, EMAR, [64]]
  - [-1, 1, Conv, [256, 3, 2]]
  - [[-1, 13], 1, Concat, [1]]
  - [-1, 2, C3k2, [512, False]]
  - [-1, 1, Conv, [512, 3, 2]]
  - [[-1, 10], 1, Concat, [1]]
  - [-1, 2, C3k2, [1024, True]]
  - [[17, 20, 23], 1, Detect, [nc]]
'''

WORK = Path('/root/autodl-tmp') if Path('/root/autodl-tmp').exists() else Path('.')


def build_model():
    """建模型 + 权重重映射（本地已验证：成功 448 键 / 缺失 57 / 多余 0）"""
    from ultralytics import YOLO
    from ultralytics.utils.downloads import attempt_download_asset

    yaml_path = WORK / 'yolo11-emar-n.yaml'
    yaml_path.write_text(YAML_TEXT.strip() + '\n', encoding='utf-8')
    model = YOLO(str(yaml_path))

    ckpt = torch.load(attempt_download_asset('yolo11n.pt'), map_location='cpu', weights_only=False)
    sd = ckpt['model'].state_dict() if 'model' in ckpt else ckpt
    remapped = {}
    for k, v in sd.items():
        m = re.match(r'model\.(\d+)\.', k)
        if m and 17 <= int(m.group(1)) <= 23:
            k = k.replace(f'model.{m.group(1)}.', f'model.{int(m.group(1))+1}.', 1)
        remapped[k] = v
    model_sd = model.model.state_dict()
    remapped = {k: v for k, v in remapped.items() if k in model_sd and model_sd[k].shape == v.shape}
    missing, unexpected = model.model.load_state_dict(remapped, strict=False)
    print(f'权重迁移：成功 {len(remapped)} 键；缺失 {len(missing)} 键（应为 57）；多余 {len(unexpected)} 键')
    with torch.no_grad():
        _ = model.model.eval()(torch.zeros(1, 3, 640, 640))
    print('结构自检通过')
    return model


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--data', default=str(WORK / 'dataset'), help='数据集目录（自动递归找 data.yaml）')
    ap.add_argument('--epochs', type=int, default=100)
    ap.add_argument('--batch', type=int, default=16)
    ap.add_argument('--dry-run', action='store_true', help='只验证结构，不训练')
    args = ap.parse_args()

    model = build_model()
    if args.dry_run:
        print('dry-run 完成，未进入训练')
        return

    cands = glob.glob(str(Path(args.data) / '**/data.yaml'), recursive=True)
    assert cands, f'未在 {args.data} 下找到 data.yaml，检查 setup.sh 是否解压成功'
    data_yaml = cands[0]
    print('数据集:', data_yaml)

    model.train(data=data_yaml, epochs=args.epochs, imgsz=640, batch=args.batch,
                device=0, project=str(WORK / 'results'), name='m2-emar')

    metrics = model.val()
    summary = {'mAP50': round(float(metrics.box.map50), 4),
               'mAP50-95': round(float(metrics.box.map), 4),
               'precision': round(float(metrics.box.mp), 4),
               'recall': round(float(metrics.box.mr), 4)}
    out = WORK / 'results' / 'm2-emar' / 'metrics.json'
    out.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print('指标:', summary)
    print('对照基线: mAP50=0.5706 | 判决线: >0.581 有效')
    print(f'完成。结果在 {WORK}/results/m2-emar/')


if __name__ == '__main__':
    main()
