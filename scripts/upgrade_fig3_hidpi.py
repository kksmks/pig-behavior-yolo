# 高分辨率重出投稿弱图（2026-08-07，Springer 分辨率合规）：
#   Fig3 训练曲线：从 results.csv 重绘——去图内标题（Springer 禁）、线型灰度可辨、430dpi
#   Fig1/4/7 由 build_figures.py（dpi 已提至 430）重出，本脚本只处理 Fig3
# 运行：python scripts/upgrade_fig3_hidpi.py → results/analysis/fig5-curves.png（覆盖，内容一致）
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'font.size': 10.5,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'figure.dpi': 430,
    'savefig.bbox': 'tight',
})

RUNS = [
    ('results/baseline/results.csv', 'Baseline (YOLOv11n)', '#7f7f7f', '-'),
    ('results/m4-wsample/results.csv', 'M4 (sampling)', '#4C72B0', '-'),
    ('results/m5-fastnet-wsample/results.csv', 'M5 (sampling+FasterNet)', '#C44E52', '--'),
]

fig, ax = plt.subplots(figsize=(7.0, 3.6))
for path, label, color, ls in RUNS:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    ax.plot(df['epoch'], df['metrics/mAP50(B)'], ls, color=color, lw=1.4, label=label)
ax.set_xlabel('Epoch')
ax.set_ylabel('mAP50 (val)')
ax.legend(frameon=False, fontsize=9, loc='lower right')
ax.grid(ls=':', alpha=0.4)
fig.savefig('results/analysis/fig5-curves.png')
plt.close(fig)
print('OK fig5-curves.png 重绘完成（无图内标题，430dpi）')
