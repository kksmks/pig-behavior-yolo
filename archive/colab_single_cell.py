# ===== 猪行为检测 · Colab 基线训练（单格版）=====
# 用法：在 Colab 新建空白笔记本，把本文件全部内容粘进一个代码格，点运行。
# 运行前确认：菜单 代码执行程序/Runtime → 更改运行时类型 → T4 GPU

API_KEY = 'YOUR_ROBOFLOW_API_KEY'  # Roboflow API key（勿外传）

import json, glob, zipfile, urllib.request, subprocess, random, shutil

# 1. GPU 检查（应显示 Tesla T4）
subprocess.run(['nvidia-smi'])

# 2. 下载并解压数据集（约 1-2 分钟）
meta = json.load(urllib.request.urlopen(
    f'https://api.roboflow.com/km-sd0ce/pig-behavior-wlvku/1/yolov8?api_key={API_KEY}'))
print('数据集:', meta['project']['name'], '| 图片:', meta['version']['images'])
subprocess.run(['curl', '-sL', '-o', '/content/dataset.zip', meta['export']['link']], check=True)
with zipfile.ZipFile('/content/dataset.zip') as z:
    z.extractall('/content/dataset')
DATA_YAML = glob.glob('/content/dataset/**/data.yaml', recursive=True)[0]
print('data.yaml:', DATA_YAML)

# 3. 标注质检图（绿框应大致框住猪；异常请停止并反馈）
import cv2
import matplotlib.pyplot as plt
from pathlib import Path
random.seed(42)
imgs = random.sample(glob.glob('/content/dataset/**/train/images/*.*', recursive=True), 12)
fig, axes = plt.subplots(3, 4, figsize=(16, 12))
for ax, p in zip(axes.flat, imgs):
    img = cv2.imread(p); h, w = img.shape[:2]
    lb = Path(p.replace('images', 'labels')).with_suffix('.txt')
    if lb.exists():
        for line in lb.read_text().splitlines():
            parts = line.split()
            if len(parts) < 5:
                continue
            _, xc, yc, bw, bh = map(float, parts[:5])
            cv2.rectangle(img, (int((xc-bw/2)*w), int((yc-bh/2)*h)),
                          (int((xc+bw/2)*w), int((yc+bh/2)*h)), (0, 255, 0), 2)
    ax.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)); ax.axis('off')
plt.tight_layout(); plt.savefig('/content/qc_samples.png', dpi=80); plt.show()

# 4. 安装 ultralytics 并训练基线（约 1.5-3 小时，页面保持打开）
subprocess.run(['pip', 'install', '-q', 'ultralytics'], check=True)
from ultralytics import YOLO
model = YOLO('yolo11n.pt')
model.train(data=DATA_YAML, epochs=100, imgsz=640, batch=16,
            device=0, project='/content/results', name='baseline')

# 5. 评估并保存指标
metrics = model.val()
summary = {'mAP50': round(float(metrics.box.map50), 4),
           'mAP50-95': round(float(metrics.box.map), 4),
           'precision': round(float(metrics.box.mp), 4),
           'recall': round(float(metrics.box.mr), 4)}
with open('/content/results/baseline/metrics.json', 'w') as f:
    json.dump(summary, f, indent=2)
print('指标:', summary)

# 6. 打包并自动下载 results.zip
shutil.copy('/content/qc_samples.png', '/content/results/baseline/qc_samples.png')
shutil.make_archive('/content/results', 'zip', '/content/results')
from google.colab import files
files.download('/content/results.zip')
print('全部完成！')
