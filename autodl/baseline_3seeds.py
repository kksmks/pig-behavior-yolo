#!/usr/bin/env python3
"""Baseline 三种子补跑（AutoDL 版）：YOLOv11n 原版 × seed 0/1/2

目的：目前只有 M4（0.5987±0.0062）和 M5（0.5904±0.0086）有三种子统计，
基线只有单次 0.5964。审稿人大概率会问"M4/M5 与基线的差是否在噪声内"，
需要基线的 mean±std 才能让 4.5 节的统计论证严格成立（JRTIP-revision-plan.md P2-E1）。

协议与 autodl/baseline_train.py 完全一致（200 epochs + patience 30 + imgsz 640 + batch 16），
仅加 --seed；命名沿用既有约定 baseline-r0/r1/r2（对照 m4-r0/r1/r2）。

用法：
  python baseline_3seeds.py --dry-run                     # 只检查数据集与计划，不训练
  nohup python baseline_3seeds.py > baseline-3seeds.log 2>&1 &

跑完后：把三个 metrics.json 的 test_mAP50 均值±样本标准差算出来，
更新论文 Table 3 脚注与 4.5 节（当前写法："versus a single-run baseline of 0.5964"）。
"""
import argparse
import glob
import json
from pathlib import Path

WORK = Path('/root/autodl-tmp') if Path('/root/autodl-tmp').exists() else Path('.')
SEEDS = [0, 1, 2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default=str(WORK / 'dataset'), help='数据集目录（自动递归找 data.yaml）')
    ap.add_argument('--dry-run', action='store_true', help='只检查数据集与计划，不训练')
    args = ap.parse_args()

    cands = glob.glob(str(Path(args.data) / '**/data.yaml'), recursive=True)
    assert cands, f'未找到 data.yaml：{args.data}'
    data_yaml = cands[0]
    print('数据集:', data_yaml)
    print('计划: YOLOv11n 原版 × seeds', SEEDS, '（200 epochs, patience 30, batch 16, imgsz 640）')
    print('结果目录:', [f'{WORK}/results/baseline-r{s}' for s in SEEDS])
    if args.dry_run:
        print('[dry-run] 检查通过，未启动训练')
        return

    from ultralytics import YOLO
    for s in SEEDS:
        name = f'baseline-r{s}'
        print(f'===== seed {s} → {name} =====')
        model = YOLO('yolo11n.pt')
        model.train(data=data_yaml, epochs=200, patience=30, imgsz=640, batch=16,
                    device=0, seed=s, project=str(WORK / 'results'), name=name)

        metrics = model.val()
        summary = {'seed': s,
                   'mAP50': round(float(metrics.box.map50), 4),
                   'mAP50-95': round(float(metrics.box.map), 4),
                   'precision': round(float(metrics.box.mp), 4),
                   'recall': round(float(metrics.box.mr), 4)}
        metrics_test = model.val(split='test')
        summary.update({'test_mAP50': round(float(metrics_test.box.map50), 4),
                        'test_mAP50-95': round(float(metrics_test.box.map), 4)})
        out = WORK / 'results' / name / 'metrics.json'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(summary, indent=2), encoding='utf-8')
        print(f'[{name}] 指标:', summary)

    # 汇总（样本标准差，与 M4/M5 统计口径一致）
    import statistics as st
    tests, vals = [], []
    for s in SEEDS:
        d = json.loads((WORK / 'results' / f'baseline-r{s}' / 'metrics.json').read_text(encoding='utf-8'))
        tests.append(d['test_mAP50'])
        vals.append(d['mAP50'])
    agg = {'val_mAP50_mean': round(st.mean(vals), 4), 'val_mAP50_std': round(st.stdev(vals), 4),
           'test_mAP50_mean': round(st.mean(tests), 4), 'test_mAP50_std': round(st.stdev(tests), 4),
           'runs': {f'baseline-r{s}': json.loads((WORK / 'results' / f'baseline-r{s}' / 'metrics.json').read_text(encoding='utf-8')) for s in SEEDS}}
    (WORK / 'results' / 'baseline-3seeds-summary.json').write_text(
        json.dumps(agg, indent=2, ensure_ascii=False), encoding='utf-8')
    print('===== 三种子汇总 =====')
    print(f"val  {agg['val_mAP50_mean']} ± {agg['val_mAP50_std']}")
    print(f"test {agg['test_mAP50_mean']} ± {agg['test_mAP50_std']}   ← 更新论文 4.5 节与 Table 3 脚注")
    print('对照: M4 test 0.5987±0.0062 / M5 test 0.5904±0.0086 / 旧单次基线 0.5964')


if __name__ == '__main__':
    main()
