# 生成论文新增图形（数据源：EXPERIMENT_LOG / per-class-ap.md / 本地数据集复算，均已审计）
# 运行：python scripts/build_figures.py → results/analysis/fig6..fig10
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

OUT = Path('results/analysis')
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'font.size': 10.5,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'figure.dpi': 430,
    'savefig.bbox': 'tight',
})

C_BASE, C_M4, C_M5, C_OTH = '#7f7f7f', '#4C72B0', '#C44E52', '#b7b7b7'

CLASSES = ['investigating', 'walk', 'lying', 'standing', 'eat', 'fight',
           'nose-to-nose', 'active', 'drink', 'sitting']
INSTANCES = [4203, 2736, 2485, 1812, 980, 807, 358, 259, 211, 144]
FACTORS = [1, 1, 1, 1, 2, 2, 3, 3, 3, 4]  # 由 m4_train.py 公式按训练集图像数复算

# ---------- Fig. 6 类别分布 + 复制倍率（3.1 用） ----------
fig, ax = plt.subplots(figsize=(7.2, 3.2))
x = np.arange(len(CLASSES))
bars = ax.bar(x, INSTANCES, color='#4C72B0', width=0.65, zorder=2)
ax.set_yscale('log')
ax.set_ylabel('Annotated instances (log)')
ax.set_xticks(x)
ax.set_xticklabels(CLASSES, rotation=28, ha='right', fontsize=8.5)
ax.set_ylim(80, 9000)
for xi, v in zip(x, INSTANCES):
    ax.text(xi, v * 1.12, str(v), ha='center', fontsize=7.5, color='#333333')
ax2 = ax.twinx()
ax2.spines['right'].set_visible(True)
ax2.plot(x, FACTORS, 's--', color='#C44E52', ms=5, lw=1.2, zorder=3,
         label='duplication factor (right)')
ax2.set_ylim(0, 5.2)
ax2.set_yticks([1, 2, 3, 4])
ax2.set_ylabel('Duplication factor', color='#C44E52')
ax2.tick_params(axis='y', colors='#C44E52')
ax.annotate('imbalance ratio ≈ 29:1', xy=(0.02, 0.90), xycoords='axes fraction', fontsize=9)
ax2.legend(loc='upper right', bbox_to_anchor=(1.0, 0.70), fontsize=8, frameon=False)
fig.savefig(OUT / 'fig6-class-distribution.png')
plt.close(fig)

# ---------- Fig. 7 每类 AP 分组柱状（4.4 用，val AP50） ----------
VAL = {  # baseline / M4 / M5（M5 active 无数据 → None）
    'baseline': [0.581, 0.687, 0.783, 0.438, 0.436, 0.858, 0.686, 0.459, 0.408, 0.403],
    'M4':       [0.570, 0.686, 0.766, 0.449, 0.447, 0.842, 0.622, 0.552, 0.459, 0.423],
    'M5':       [0.577, 0.667, 0.743, 0.445, 0.449, 0.786, 0.710, None, 0.430, 0.349],
}
fig, ax = plt.subplots(figsize=(7.6, 3.4))
w = 0.26
SERIES = [('baseline', C_BASE, ''), ('M4 (sampling)', C_M4, ''), ('M5 (combined)', C_M5, '//')]
for i, (name, color, hatch) in enumerate(SERIES):
    key = name.split(' ')[0]
    vals = VAL[key]
    xs = x + (i - 1) * w
    for xi, v in zip(xs, vals):
        if v is not None:
            ax.bar(xi, v, width=w * 0.92, color=color, hatch=hatch,
                   edgecolor='white', lw=0.3, zorder=2)
ax.set_xticks(x)
ax.set_xticklabels(CLASSES, rotation=28, ha='right', fontsize=8.5)
ax.set_ylabel('AP50 (validation)')
ax.set_ylim(0, 0.95)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(fc=C_BASE, label='Baseline'),
                   Patch(fc=C_M4, label='M4 (sampling)'),
                   Patch(fc=C_M5, hatch='//', ec='white', label='M5 (combined)')],
          ncol=3, frameon=False, fontsize=9,
          loc='upper center', bbox_to_anchor=(0.5, 1.14))
ax.grid(axis='y', ls=':', alpha=0.4, zorder=0)
fig.savefig(OUT / 'fig7-perclass-ap.png')
plt.close(fig)

# ---------- Fig. 8 精度-效率散点（4.6 用） ----------
# (params M, test mAP50, FPS or None, label, color)
PTS = [
    (2.58, 0.5964, 112.8, 'Baseline (YOLOv11n)', C_BASE),
    (2.58, 0.6035, 112.1, 'M4 (ours)', C_M4),
    (2.47, 0.5932, 117.6, 'M5 (ours)', C_M5),
    (2.50, 0.6001, None, 'YOLOv5n', C_OTH),
    (3.01, 0.5877, None, 'YOLOv8n', C_OTH),
    (2.56, 0.6135, 78.4, 'YOLOv12n', C_OTH),
    (32.0, 0.6008, None, 'RT-DETR-l', C_OTH),
]
fig, ax = plt.subplots(figsize=(6.6, 3.8))
for px, py, fps, lab, col in PTS:
    if fps:
        ax.scatter(px, py, s=fps * 1.6, color=col, zorder=3,
                   edgecolor='k', linewidth=0.5)
    else:
        ax.scatter(px, py, s=70, facecolor='none', edgecolor=col, linewidth=1.4, zorder=3)
offsets = {'Baseline (YOLOv11n)': (9, -3), 'M4 (ours)': (7, 9),
           'YOLOv8n': (8, -6), 'YOLOv12n': (-4, 11), 'RT-DETR-l': (-70, 8)}
# 左缘密集簇用引线标注（文本放空区，箭头指向标记）
LEADERS = {'M5 (ours)': (2.75, 0.5895), 'YOLOv5n': (3.6, 0.6072)}
for px, py, fps, lab, col in PTS:
    if lab in LEADERS:
        ax.annotate(lab, (px, py), xytext=LEADERS[lab], fontsize=8,
                    arrowprops=dict(arrowstyle='-', color='#666666', lw=0.8,
                                    shrinkA=2, shrinkB=6))
    else:
        ax.annotate(lab, (px, py), textcoords='offset points', xytext=offsets[lab], fontsize=8)
ax.set_xscale('log')
ax.set_xticks([2.5, 3, 4, 6, 10, 32])
ax.set_xticklabels(['2.5', '3', '4', '6', '10', '32'])
ax.set_xlabel('Parameters (M, log scale)')
ax.set_ylabel('test mAP50')
ax.set_ylim(0.575, 0.625)
ax.set_xlim(2.3, 45)
ax.grid(ls=':', alpha=0.4, zorder=0)
ax.annotate('marker size ∝ measured FPS (RTX 3090); hollow = FPS not measured',
            xy=(0.02, 0.03), xycoords='axes fraction', fontsize=7.5, color='#555555')
fig.savefig(OUT / 'fig8-pareto.png')
plt.close(fig)

# ---------- Fig. 9 部署管线图（第 5 节用） ----------
fig, ax = plt.subplots(figsize=(7.4, 2.9))
ax.axis('off')
boxes = [
    (0.03, 'PyTorch\nbest.pt\n(2.47M params)'),
    (0.29, 'ONNX export\nopset 12\n(no graph slim)'),
    (0.55, 'TensorRT 8.2\nFP16 engine\n(one build at a time)'),
    (0.81, 'Jetson Nano\nJetPack 4.6.3\nMaxwell, 4 GB'),
]
for bx, txt in boxes:
    ax.add_patch(plt.Rectangle((bx, 0.52), 0.16, 0.34, fc='#eef3fa', ec='#4C72B0', lw=1.2,
                               transform=ax.transAxes, zorder=2))
    ax.text(bx + 0.08, 0.69, txt, transform=ax.transAxes, ha='center', va='center', fontsize=8.2)
for ax_ in [0.20, 0.46, 0.72]:
    ax.annotate('', xy=(ax_ + 0.075, 0.69), xytext=(ax_, 0.69), xycoords='axes fraction',
                arrowprops=dict(arrowstyle='-|>', color='#333333', lw=1.4))
ax.add_patch(plt.Rectangle((0.29, 0.06), 0.42, 0.30, fc='#fdf3f3', ec='#C44E52', lw=1.0,
                           transform=ax.transAxes, zorder=2))
ax.text(0.50, 0.21, 'Measured (sustained, batch 1):\n'
                    '640×640: 50.2 ms = 19.7 FPS   |   480×480: 30.0 ms = 33.3 FPS\n'
                    'total board power ≈ 5 W; INT8 unavailable on Maxwell (calibration fails)',
        transform=ax.transAxes, ha='center', va='center', fontsize=8.2, color='#7a2222')
ax.annotate('', xy=(0.89, 0.51), xytext=(0.50, 0.37), xycoords='axes fraction',
            arrowprops=dict(arrowstyle='-|>', color='#C44E52', lw=1.1, ls='--'))
fig.savefig(OUT / 'fig9-deploy-pipeline.png')
plt.close(fig)

# ---------- Fig. 10 泛化鸿沟柱状（6.1 用） ----------
REGIMES = ['Random split\n(test)', 'Unseen sequences\n(test)', 'External farm\n(zero-shot)']
GEN = {
    'Baseline': ([0.5964, 0.1545, 0.0671], C_BASE, ''),
    'M4 (sampling)': ([0.6035, 0.1454, 0.0375], C_M4, ''),
    'M5 (combined)': ([0.5932, 0.1526, 0.0361], C_M5, '//'),
}
fig, ax = plt.subplots(figsize=(6.8, 3.4))
xg = np.arange(3)
w = 0.25
for i, (name, (vals, col, hatch)) in enumerate(GEN.items()):
    xs = xg + (i - 1) * w
    ax.bar(xs, vals, width=w * 0.9, color=col, hatch=hatch, edgecolor='white', lw=0.3,
           zorder=2, label=name)
    for xi, v in zip(xs, vals):
        ax.text(xi, v + 0.012, f'{v:.3f}', ha='center', fontsize=7.3)
ax.set_xticks(xg)
ax.set_xticklabels(REGIMES, fontsize=9)
ax.set_ylabel('mAP50')
ax.set_ylim(0, 0.70)
ax.legend(frameon=False, fontsize=9, loc='upper right')
ax.grid(axis='y', ls=':', alpha=0.4, zorder=0)
fig.savefig(OUT / 'fig10-generalization.png')
plt.close(fig)

print('OK: fig6–fig10 已生成到', OUT)
for f in ['fig6-class-distribution.png', 'fig7-perclass-ap.png', 'fig8-pareto.png',
          'fig9-deploy-pipeline.png', 'fig10-generalization.png']:
    print(' ', f, (OUT / f).stat().st_size // 1024, 'KB')
