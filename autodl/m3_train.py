#!/usr/bin/env python3
"""M3 训练（AutoDL 版）：YOLOv11n + FasterNet 轻量化主干 v2

设计：P2 保留原版 C3k2，P3/P4/P5 换 "1×1 适配 + FasterBlock×2"（expand=1）。
本地验证：参数 2.62M→2.48M(-5.6%)、FLOPs 6.61G→6.59G(-0.3%)、
          权重迁移 316 键 / 缺失 99 / 多余 0、前向通过。

用法：
  python m3_train.py --dry-run                       # 只验证结构，不训练
  nohup python m3_train.py > m3.log 2>&1 &           # 后台训练（首轮 100 轮）
  # 首轮结束后续训 50 轮（热重启微调，lr 调低）：
  nohup python m3_train.py --weights results/m3-fasternet/weights/best.pt \
      --epochs 50 --lr0 0.002 --name m3-fasternet-plus > m3b.log 2>&1 &
  tail -f m3.log
"""
import argparse
import glob
import json
import re
from pathlib import Path

import torch
from torch import nn
import ultralytics.nn.tasks as tasks


class FasterBlock(nn.Module):
    """FasterNet Block (CVPR 2023)：PConv（仅 1/4 通道做空间卷积）+ 两个逐点卷积 + 残差。
    输入输出通道数不变。expand=1（低通道模型 expand=2 反而增肥，本地实测）。"""
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

YAML_TEXT = r'''
nc: 10
scales:
  n: [0.50, 0.25, 1024]
backbone:
  - [-1, 1, Conv, [64, 3, 2]]
  - [-1, 1, Conv, [128, 3, 2]]
  - [-1, 2, C3k2, [256, False, 0.25]]
  - [-1, 1, Conv, [256, 3, 2]]
  - [-1, 1, Conv, [512, 1, 1]]
  - [-1, 2, FasterBlock, [128]]
  - [-1, 1, Conv, [512, 3, 2]]
  - [-1, 1, Conv, [512, 1, 1]]
  - [-1, 2, FasterBlock, [128]]
  - [-1, 1, Conv, [1024, 3, 2]]
  - [-1, 1, Conv, [1024, 1, 1]]
  - [-1, 2, FasterBlock, [256]]
  - [-1, 1, SPPF, [1024, 5]]
  - [-1, 2, C2PSA, [1024]]
head:
  - [-1, 1, nn.Upsample, [None, 2, 'nearest']]
  - [[-1, 8], 1, Concat, [1]]
  - [-1, 2, C3k2, [512, False]]
  - [-1, 1, nn.Upsample, [None, 2, 'nearest']]
  - [[-1, 5], 1, Concat, [1]]
  - [-1, 2, C3k2, [256, False]]
  - [-1, 1, Conv, [256, 3, 2]]
  - [[-1, 16], 1, Concat, [1]]
  - [-1, 2, C3k2, [512, False]]
  - [-1, 1, Conv, [512, 3, 2]]
  - [[-1, 13], 1, Concat, [1]]
  - [-1, 2, C3k2, [1024, True]]
  - [[19, 22, 25], 1, Detect, [nc]]
'''

WORK = Path('/root/autodl-tmp') if Path('/root/autodl-tmp').exists() else Path('.')


def build_model():
    """建模型 + 权重重映射（本地已验证：成功 316 键 / 缺失 99 / 多余 0）"""
    from ultralytics import YOLO
    from ultralytics.utils.downloads import attempt_download_asset

    yaml_path = WORK / 'yolo11-fasternet-n.yaml'
    yaml_path.write_text(YAML_TEXT.strip() + '\n', encoding='utf-8')
    model = YOLO(str(yaml_path))

    ckpt = torch.load(attempt_download_asset('yolo11n.pt'), map_location='cpu', weights_only=False)
    sd = ckpt['model'].state_dict() if 'model' in ckpt else ckpt
    SHIFT = {0: 0, 1: 1, 2: 2, 3: 3, 5: 6, 7: 9, 9: 12, 10: 13}
    remapped = {}
    for k, v in sd.items():
        m = re.match(r'model\.(\d+)\.', k)
        idx = int(m.group(1))
        if idx <= 10:
            if idx not in SHIFT:
                continue  # 原 C3k2（4/6/8）不匹配 FasterBlock，跳过
            new_idx = SHIFT[idx]
        else:
            new_idx = idx + 3  # 头部整体后移 3 位
        remapped[k.replace(f'model.{idx}.', f'model.{new_idx}.', 1)] = v
    model_sd = model.model.state_dict()
    remapped = {k: v for k, v in remapped.items() if k in model_sd and model_sd[k].shape == v.shape}
    missing, unexpected = model.model.load_state_dict(remapped, strict=False)
    print(f'权重迁移：成功 {len(remapped)} 键；缺失 {len(missing)} 键（应为 99）；多余 {len(unexpected)} 键')
    with torch.no_grad():
        _ = model.model.eval()(torch.zeros(1, 3, 640, 640))
    print('结构自检通过')
    return model


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--data', default=str(WORK / 'dataset'), help='数据集目录（自动递归找 data.yaml）')
    ap.add_argument('--epochs', type=int, default=100)
    ap.add_argument('--batch', type=int, default=16)
    ap.add_argument('--lr0', type=float, default=0.01, help='初始学习率（续训建议 0.002）')
    ap.add_argument('--weights', default=None, help='续训权重路径（如 best.pt）；缺省则从零建模型')
    ap.add_argument('--name', default='m3-fasternet', help='实验名（结果目录名）')
    ap.add_argument('--dry-run', action='store_true', help='只验证结构，不训练')
    args = ap.parse_args()

    if args.dry_run:
        build_model()
        print('dry-run 完成，未进入训练')
        return

    if args.weights:
        from ultralytics import YOLO
        model = YOLO(args.weights)
        print(f'续训模式：加载 {args.weights}，lr0={args.lr0}')
    else:
        model = build_model()

    cands = glob.glob(str(Path(args.data) / '**/data.yaml'), recursive=True)
    assert cands, f'未在 {args.data} 下找到 data.yaml'
    data_yaml = cands[0]
    print('数据集:', data_yaml)

    model.train(data=data_yaml, epochs=args.epochs, imgsz=640, batch=args.batch,
                lr0=args.lr0, device=0, project=str(WORK / 'results'), name=args.name)

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
    print('对照基线: mAP50=0.5706 | 目标: 精度不降（≥0.56）即为轻量化成功')
    print(f'完成。结果在 {WORK}/results/{args.name}/')


if __name__ == '__main__':
    main()
