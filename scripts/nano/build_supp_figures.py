# 补充材料图：figS2 延迟分解 + figS3 持续运行时序（数据源：trtexec 复测 + thermal.log）
# 运行：python scripts/nano/build_supp_figures.py → results/analysis/figS2-latency-breakdown.png / figS3-thermal-timeline.png
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

OUT = Path('results/analysis')
plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 10,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'figure.dpi': 600, 'savefig.bbox': 'tight'})

# ---------- figS2: (a) 引擎侧堆叠条 (b) CPU 侧耗时 ----------
eng = [  # (label, H2D, GPU, D2H, fps)
    ('M5 @640', 0.48, 49.63, 0.06, 19.9),
    ('Baseline @640', 0.49, 50.02, 0.05, 19.8),
    ('M5 @480', 0.27, 29.57, 0.03, 33.5),
    ('Baseline @480', 0.28, 30.60, 0.03, 32.3),
]
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.6, 2.9), gridspec_kw={'width_ratios': [1.35, 1]})
y = np.arange(len(eng))
left = np.zeros(len(eng))
for i, (lab, c) in enumerate([('H2D', '#9ecae1'), ('GPU compute', '#4C72B0'), ('D2H', '#c7c7c7')]):
    vals = np.array([e[i + 1] for e in eng])
    ax1.barh(y, vals, left=left, color=c, height=0.6, label=lab, zorder=2)
    left += vals
for yi, e in zip(y, eng):
    ax1.text(left[list(eng).index(e)] + 0.8, yi, f'{e[4]} FPS', va='center', fontsize=8.5)
ax1.set_yticks(y)
ax1.set_yticklabels([e[0] for e in eng], fontsize=9)
ax1.set_xlabel('Latency (ms)')
ax1.set_xlim(0, 62)
ax1.legend(fontsize=7.5, frameon=False, ncol=3, loc='lower center',
           bbox_to_anchor=(0.5, 1.02), handlelength=1.2, columnspacing=0.9)
ax1.set_title('(a)', fontsize=10, pad=22)
ax1.grid(axis='x', ls=':', alpha=0.4, zorder=0)

cpu_items = [  # (label, ms, color)
    ('JPEG decode (1080p src)', 74.5, '#C44E52'),
    ('Resize 1080p→640', 32.6, '#C44E52'),
    ('JPEG decode (640 src)', 15.4, '#DD8452'),
    ('Normalize + CHW (C)', 6.8, '#4C72B0'),
    ('Pad', 0.8, '#7f7f7f'),
    ('NMS (≈370 candidates, C)', 0.49, '#55A868'),
]
y2 = np.arange(len(cpu_items))
ax2.barh(y2, [v for _, v, _ in cpu_items], color=[c for *_, c in cpu_items], height=0.6, zorder=2)
for yi, (lab, v, _) in zip(y2, cpu_items):
    ax2.text(v * 1.15, yi, f'{v} ms', va='center', fontsize=8)
ax2.set_yticks(y2)
ax2.set_yticklabels([lab for lab, _, _ in cpu_items], fontsize=8)
ax2.set_xscale('log')
ax2.set_xlim(0.3, 250)
ax2.set_xlabel('CPU-side cost (ms, log)')
ax2.set_title('(b)', fontsize=10, pad=22)
ax2.grid(axis='x', ls=':', alpha=0.4, zorder=0)
fig.savefig(OUT / 'figS2-latency-breakdown.png')
plt.close(fig)

# ---------- figS3: 热节流时序 ----------
lines = Path('results/deploy/thermal/thermal.log').read_text(errors='replace').splitlines()
t, gpu_t, cpu_t, util = [], [], [], []
for i, ln in enumerate(lines):
    m = re.search(r'GR3D_FREQ (\d+)%', ln)
    g = re.search(r'GPU@([\d.]+)C', ln)
    c = re.search(r'CPU@([\d.]+)C', ln)
    if m and g:
        t.append(i)
        util.append(int(m.group(1)))
        gpu_t.append(float(g.group(1)))
        cpu_t.append(float(c.group(1)) if c else float('nan'))
fig, ax = plt.subplots(figsize=(7.2, 2.8))
ax.plot(t, gpu_t, color='#C44E52', lw=1.4, label='GPU temperature')
ax.plot(t, cpu_t, color='#DD8452', lw=1.0, label='CPU temperature')
ax.set_xlabel('Elapsed time (s) — 12,000 consecutive inferences, M5 @640 FP16')
ax.set_ylabel('Temperature (°C)')
ax.set_ylim(25, 65)
ax.axhline(55.5, color='#C44E52', ls=':', lw=0.8)
ax.text(len(t) * 0.62, 56.5, 'peak 55.5 °C', fontsize=8, color='#C44E52')
ax2 = ax.twinx()
ax2.spines['right'].set_visible(True)
ax2.plot(t, util, color='#4C72B0', lw=0.8, alpha=0.6, label='GPU utilization (right)')
ax2.set_ylabel('GPU utilization (%)', color='#4C72B0')
ax2.set_ylim(0, 110)
ax2.tick_params(axis='y', colors='#4C72B0')
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, fontsize=8, frameon=False, loc='lower center', ncol=3)
ax.grid(ls=':', alpha=0.4)
fig.savefig(OUT / 'figS3-thermal-timeline.png')
plt.close(fig)
print('OK: figS2, figS3 已生成')
