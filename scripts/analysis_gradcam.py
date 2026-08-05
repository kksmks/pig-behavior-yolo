#!/usr/bin/env python3
"""Grad-CAM 对比图生成（本地 CPU）：基线 vs M3（轻量化后关注区域是否保持）。

输出：results/analysis/gradcam/<图片名>_cam.jpg（原图 | 基线热力 | M3热力 三联）
在 E:\pig-behavior-yolo 下运行：python scripts/analysis_gradcam.py
"""
import cv2
import numpy as np
import torch
from torch import nn
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


class FasterBlock(nn.Module):
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


class GradCAM:
    """对检测头最强类别分数做反向传播的 Grad-CAM。"""

    def __init__(self, yolo, target_layer):
        self.net = yolo.model.eval()
        self.acts = None
        self.grads = None
        target_layer.register_forward_hook(lambda m, i, o: setattr(self, 'acts', o))
        target_layer.register_full_backward_hook(lambda m, gi, o: setattr(self, 'grads', o[0]))

    def __call__(self, x):
        out = self.net(x)
        # eval 返回 (decoded, {'scores': [1,nc,8400]})，scores 为 logits
        score = out[1]['scores'].sigmoid().max()
        self.net.zero_grad()
        score.backward(retain_graph=True)
        w = self.grads.mean(dim=(2, 3), keepdim=True)
        cam = torch.relu((w * self.acts).sum(1, keepdim=True))
        cam = torch.nn.functional.interpolate(cam, x.shape[2:], mode='bilinear', align_corners=False)
        cam = cam.squeeze().detach().cpu().numpy()
        return (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)


def load_tensor(path):
    img = cv2.imread(str(path))
    rgb = img[..., ::-1].copy()
    x = torch.from_numpy(rgb.transpose(2, 0, 1)).float().unsqueeze(0) / 255.0
    return img, x


def overlay(img, cam):
    heat = cv2.applyColorMap((cam * 255).astype(np.uint8), cv2.COLORMAP_JET)
    return cv2.addWeighted(img, 0.55, heat, 0.45, 0)


def main():
    import ultralytics.nn.tasks as tasks
    tasks.FasterBlock = FasterBlock
    from ultralytics import YOLO

    m_base = YOLO('results/baseline/weights/best.pt')
    m_m3 = YOLO('results/m3-fasternet-plus-best.pt')
    for m in (m_base, m_m3):
        for p in m.model.parameters():
            p.requires_grad_(True)  # ultralytics 加载后参数默认冻结，Grad-CAM 需要梯度

    # 目标层：主干末端（v11: 第 10 层 C2PSA；M3: 第 13 层 C2PSA）
    cam_base = GradCAM(m_base, m_base.model.model[10])
    cam_m3 = GradCAM(m_m3, m_m3.model.model[13])

    out_dir = Path('results/analysis/gradcam')
    out_dir.mkdir(parents=True, exist_ok=True)

    samples = sorted(Path('data/dataset/test/images').glob('2019_11_28*'))[:2] + \
        sorted(Path('data/dataset/test/images').glob('2019_12_10*'))[:1]

    for p in samples:
        img, x = load_tensor(p)
        cb = overlay(img, cam_base(x))
        cm = overlay(img, cam_m3(x))
        tri = np.concatenate([img, cb, cm], axis=1)
        cv2.putText(tri, 'image', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(tri, 'baseline', (650, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(tri, 'M3-FasterNet', (1290, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        out = out_dir / f'{p.stem}_cam.jpg'
        cv2.imwrite(str(out), tri)
        print('已生成:', out)


if __name__ == '__main__':
    main()
