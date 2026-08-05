#!/usr/bin/env python3
"""M4 训练（AutoDL 版）：类别加权采样（离线过采样）+ 原版 YOLOv11n

原理（借鉴 YW-Dataset / LVIS repeat-factor sampling，独立实现）：
  统计训练集各类实例数 → 类别权重 = sqrt(最大类/该类)（开方抑制极端倍率）
  → 含稀有类的图像按权重硬链接复制 → 训练时稀有类自然高频出现。
  只动训练集，val/test 原样不动（评测公平）。模型零改动，无预训练污染。

用法：
  python m4_train.py --dry-run          # 只做过采样并打印前后分布（不训练）
  nohup python m4_train.py > m4.log 2>&1 &
"""
import argparse
import glob
import json
import math
import os
import shutil
from collections import Counter
from pathlib import Path

WORK = Path('/root/autodl-tmp') if Path('/root/autodl-tmp').exists() else Path('.')
MAX_FACTOR = 5  # 单图最大复制倍数，防极端过拟合


def build_oversampled(data_root: Path, os_root: Path, cap: int = MAX_FACTOR):
    """扫描训练集标注 → 计算倍率 → 硬链接生成过采样训练集 → 写 data-os.yaml"""
    train_img, train_lbl = data_root / 'train/images', data_root / 'train/labels'
    assert train_img.exists(), f'未找到训练集: {train_img}'

    # 1. 统计每类实例数 & 每张图含哪些类
    class_cnt = Counter()
    img_classes = {}
    for txt in train_lbl.glob('*.txt'):
        classes = {int(l.split()[0]) for l in txt.read_text().splitlines() if l.split()}
        if not classes:
            continue
        img_classes[txt.stem] = classes
        for c in classes:
            class_cnt[c] += 1

    names = (data_root / 'data.yaml').read_text(encoding='utf-8')
    max_cnt = max(class_cnt.values())

    # 2. 类别倍率：sqrt(max/count)，封顶 MAX_FACTOR；图像倍率取其所含类的最大值
    def factor(c):
        return min(cap, max(1, round(math.sqrt(max_cnt / class_cnt[c]))))

    # 3. 生成过采样数据集（硬链接，零额外磁盘）
    (os_root / 'train/images').mkdir(parents=True, exist_ok=True)
    (os_root / 'train/labels').mkdir(parents=True, exist_ok=True)
    ext_of = {p.stem: p.suffix for p in train_img.glob('*') if p.suffix.lower() in
              ('.jpg', '.jpeg', '.png', '.bmp', '.webp')}
    eff_cnt = Counter()
    total_imgs = 0
    for stem, classes in img_classes.items():
        f = max(factor(c) for c in classes)
        suffix = ext_of.get(stem)
        if suffix is None:
            continue
        for i in range(f):
            dst_img = os_root / 'train/images' / f'{stem}__r{i}{suffix}'
            dst_lbl = os_root / 'train/labels' / f'{stem}__r{i}.txt'
            for dst, src in ((dst_img, train_img / f'{stem}{suffix}'),
                             (dst_lbl, train_lbl / f'{stem}.txt')):
                if not dst.exists():
                    os.link(src, dst)
            total_imgs += 1
            for c in classes:
                eff_cnt[c] += 1

    # 4. 类别名映射（沿用原 data.yaml 的 names）+ 写新 yaml
    import yaml as _yaml
    meta = _yaml.safe_load(names)
    valid_abs = (data_root / 'valid/images').resolve()
    test_abs = (data_root / 'test/images').resolve()
    os_yaml = (f"path: {os_root.resolve()}\ntrain: train/images\n"
               f"val: {valid_abs}\ntest: {test_abs}\n"
               f"names:\n" + ''.join(f"  {i}: {n}\n" for i, n in
                                     (meta['names'].items() if isinstance(meta['names'], dict)
                                      else enumerate(meta['names']))))
    (os_root / 'data-os.yaml').write_text(os_yaml, encoding='utf-8')

    # 5. 打印前后分布
    print(f'{"类别":<14}{"原实例":>8}{"倍率":>6}{"有效实例":>8}')
    for c in sorted(class_cnt):
        print(f'{meta["names"][c] if isinstance(meta["names"], dict) else meta["names"][c]:<14}'
              f'{class_cnt[c]:>8}{factor(c):>6}{eff_cnt[c]:>8}')
    print(f'训练图: 原 {len(img_classes)} → 过采样 {total_imgs}（硬链接，val/test 不动）')
    return os_root / 'data-os.yaml'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--data', default=str(WORK / 'dataset'), help='原始数据集目录')
    ap.add_argument('--epochs', type=int, default=200)
    ap.add_argument('--batch', type=int, default=16)
    ap.add_argument('--seed', type=int, default=0, help='随机种子（重复实验用）')
    ap.add_argument('--max-factor', type=int, default=MAX_FACTOR, help='过采样倍率上限（消融用）')
    ap.add_argument('--name', default='m4-wsample', help='实验名（结果目录名）')
    ap.add_argument('--dry-run', action='store_true', help='只做过采样与分布打印，不训练')
    args = ap.parse_args()

    os_root = WORK / f'dataset-os-f{args.max_factor}'
    if not (os_root / 'data-os.yaml').exists():
        data_yaml = build_oversampled(Path(args.data), os_root, cap=args.max_factor)
    else:
        print('过采样数据集已存在，直接复用')
        data_yaml = str(os_root / 'data-os.yaml')

    if args.dry_run:
        print('dry-run 完成，未进入训练')
        return

    from ultralytics import YOLO
    model = YOLO('yolo11n.pt')  # 原版基线模型 + 加权采样（模型零改动）
    model.train(data=str(data_yaml), epochs=args.epochs, patience=30, imgsz=640,
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
    print('对照基线@200: val 0.5729 / test 0.5964 | 判决线: test ≥ 0.61 且弱类 AP 提升')
    print(f'完成。结果在 {WORK}/results/m4-wsample/')


if __name__ == '__main__':
    main()
