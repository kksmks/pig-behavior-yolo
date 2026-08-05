#!/usr/bin/env python3
"""M5 训练（AutoDL 版）：M4 类别加权采样 + M3 FasterNet 轻量化主干（组合实验）

消融阶梯：baseline → +采样(M4) → +采样&轻量化(M5)
检验"既准又轻"：M4 的弱类增益能否落到 M3 的轻量模型上（-5.6% 参数 + 精度回升）。

用法：
  python m5_train.py --dry-run          # 过采样 + 建模自检（不训练）
  nohup python m5_train.py > m5.log 2>&1 &
"""
import argparse
import json
import math
import os
import re
import glob
from collections import Counter
from pathlib import Path

import torch
from torch import nn
import ultralytics.nn.tasks as tasks

WORK = Path('/root/autodl-tmp') if Path('/root/autodl-tmp').exists() else Path('.')
MAX_FACTOR = 5


class FasterBlock(nn.Module):
    """FasterNet Block：PConv（1/4 通道空间卷积）+ 两个逐点卷积 + 残差，通道不变。"""
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


def build_oversampled(data_root: Path, os_root: Path):
    """类别加权离线过采样（与 m4_train.py 同逻辑）：sqrt 反比倍率，封顶 MAX_FACTOR。"""
    train_img, train_lbl = data_root / 'train/images', data_root / 'train/labels'
    class_cnt = Counter()
    img_classes = {}
    for txt in train_lbl.glob('*.txt'):
        classes = {int(l.split()[0]) for l in txt.read_text().splitlines() if l.split()}
        if classes:
            img_classes[txt.stem] = classes
            for c in classes:
                class_cnt[c] += 1
    max_cnt = max(class_cnt.values())

    def factor(c):
        return min(MAX_FACTOR, max(1, round(math.sqrt(max_cnt / class_cnt[c]))))

    (os_root / 'train/images').mkdir(parents=True, exist_ok=True)
    (os_root / 'train/labels').mkdir(parents=True, exist_ok=True)
    ext_of = {p.stem: p.suffix for p in train_img.glob('*')}
    total = 0
    for stem, classes in img_classes.items():
        f = max(factor(c) for c in classes)
        suffix = ext_of.get(stem)
        if suffix is None:
            continue
        for i in range(f):
            di = os_root / 'train/images' / f'{stem}__r{i}{suffix}'
            dl = os_root / 'train/labels' / f'{stem}__r{i}.txt'
            for dst, src in ((di, train_img / f'{stem}{suffix}'), (dl, train_lbl / f'{stem}.txt')):
                if not dst.exists():
                    os.link(src, dst)
            total += 1

    import yaml as _yaml
    meta = _yaml.safe_load((data_root / 'data.yaml').read_text(encoding='utf-8'))
    os_yaml = (f"path: {os_root.resolve()}\ntrain: train/images\n"
               f"val: {(data_root / 'valid/images').resolve()}\n"
               f"test: {(data_root / 'test/images').resolve()}\nnames:\n"
               + ''.join(f"  {i}: {n}\n" for i, n in
                         (meta['names'].items() if isinstance(meta['names'], dict)
                          else enumerate(meta['names']))))
    (os_root / 'data-os.yaml').write_text(os_yaml, encoding='utf-8')
    print(f'过采样训练集: {len(img_classes)} → {total} 张（硬链接）')
    return os_root / 'data-os.yaml'


def build_model():
    """FasterNet 模型 + 权重重映射（同 m3_train.py，本地已验证 316/99/0）。"""
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
                continue
            new_idx = SHIFT[idx]
        else:
            new_idx = idx + 3
        remapped[k.replace(f'model.{idx}.', f'model.{new_idx}.', 1)] = v
    model_sd = model.model.state_dict()
    remapped = {k: v for k, v in remapped.items() if k in model_sd and model_sd[k].shape == v.shape}
    missing, unexpected = model.model.load_state_dict(remapped, strict=False)
    print(f'权重迁移：成功 {len(remapped)} 键；缺失 {len(missing)} 键；多余 {len(unexpected)} 键')
    with torch.no_grad():
        _ = model.model.eval()(torch.zeros(1, 3, 640, 640))
    print('结构自检通过')
    return model


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--data', default=str(WORK / 'dataset'))
    ap.add_argument('--epochs', type=int, default=200)
    ap.add_argument('--batch', type=int, default=16)
    ap.add_argument('--seed', type=int, default=0, help='随机种子（重复实验用）')
    ap.add_argument('--name', default='m5-fastnet-wsample', help='实验名（结果目录名）')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    os_root = WORK / 'dataset-os'
    data_yaml = str(os_root / 'data-os.yaml') if (os_root / 'data-os.yaml').exists() \
        else str(build_oversampled(Path(args.data), os_root))
    model = build_model()
    if args.dry_run:
        print('dry-run 完成，未进入训练')
        return

    model.train(data=data_yaml, epochs=args.epochs, patience=30, imgsz=640,
                batch=args.batch, device=0, seed=args.seed,
                project=str(WORK / 'results'), name=args.name)

    metrics = model.val()
    summary = {'mAP50': round(float(metrics.box.map50), 4),
               'mAP50-95': round(float(metrics.box.map), 4),
               'precision': round(float(metrics.box.mp), 4),
               'recall': round(float(metrics.box.mr), 4)}
    metrics_test = model.val(split='test')
    summary.update({'test_mAP50': round(float(metrics_test.box.map50), 4),
                    'test_mAP50-95': round(float(metrics_test.box.map), 4)})
    out = WORK / 'results' / args.name / 'metrics.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print('指标:', summary)
    print('对照: 基线@200 test 0.5964 | M4 test 0.6035 | M3 test 0.5691')
    print(f'完成。结果在 {WORK}/results/{args.name}/')


if __name__ == '__main__':
    main()
