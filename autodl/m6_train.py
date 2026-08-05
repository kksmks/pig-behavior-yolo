#!/usr/bin/env python3
"""M6 训练（AutoDL 版）：类别加权采样 + YOLOv12n 新基座

依据：paper/lit-review-yolo12.md（yolo12n 实测 test 0.6135 全场王；采样与架构无关零改造）。
判决线：test ≥0.61 新王；<0.60 采样未迁移。

用法：
  python m6_train.py --dry-run          # 只做过采样与分布打印（不训练）
  nohup python m6_train.py > m6.log 2>&1 &
"""
import argparse
import glob
import json
import math
import os
from collections import Counter
from pathlib import Path

WORK = Path('/root/autodl-tmp') if Path('/root/autodl-tmp').exists() else Path('.')
MAX_FACTOR = 5


def build_oversampled(data_root: Path, os_root: Path):
    """类别加权离线过采样（与 m4/m5 同逻辑，已验证）：sqrt 反比倍率，封顶 MAX_FACTOR。"""
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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--data', default=str(WORK / 'dataset'))
    ap.add_argument('--epochs', type=int, default=200)
    ap.add_argument('--batch', type=int, default=16)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    os_root = WORK / 'dataset-os'
    data_yaml = str(os_root / 'data-os.yaml') if (os_root / 'data-os.yaml').exists() \
        else str(build_oversampled(Path(args.data), os_root))
    if args.dry_run:
        print('dry-run 完成，未进入训练')
        return

    from ultralytics import YOLO
    model = YOLO('yolo12n.pt')  # 新基座（NeurIPS 2025 官方），仅此一处与 M4 不同
    model.train(data=str(data_yaml), epochs=args.epochs, patience=30, imgsz=640,
                batch=args.batch, device=0, project=str(WORK / 'results'), name='m6-yolo12n-wsample')

    metrics = model.val()
    summary = {'mAP50': round(float(metrics.box.map50), 4),
               'mAP50-95': round(float(metrics.box.map), 4),
               'precision': round(float(metrics.box.mp), 4),
               'recall': round(float(metrics.box.mr), 4)}
    metrics_test = model.val(split='test')
    summary.update({'test_mAP50': round(float(metrics_test.box.map50), 4),
                    'test_mAP50-95': round(float(metrics_test.box.map), 4)})
    out = WORK / 'results' / 'm6-yolo12n-wsample' / 'metrics.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print('指标:', summary)
    print('对照: yolo12n 裸基座 test 0.6135 | M4 test 0.6035 | 判决线: test ≥0.61 新王')
    print(f'完成。结果在 {WORK}/results/m6-yolo12n-wsample/')


if __name__ == '__main__':
    main()
