# 本地产出三模型 PR/F1 曲线（test 集，CPU）：baseline / M4 / M5
# 运行：python scripts/nano/gen_pr_curves.py  → results/analysis/prcurves/{baseline,m4,m5}/
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path
import torch
from torch import nn
import ultralytics.nn.tasks as tasks


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


tasks.FasterBlock = FasterBlock
from ultralytics import YOLO

NAMES = ['active', 'drink', 'eat', 'fight', 'investigating', 'lying',
         'nose-to-nose', 'sitting', 'standing', 'walk']
ROOT = Path('data/dataset').resolve()
tmp = Path('data/tmp'); tmp.mkdir(exist_ok=True)
y = tmp / 'data-test-pr.yaml'
y.write_text(
    f"path: {ROOT}\ntrain: train/images\nval: test/images\ntest: test/images\n"
    f"nc: 10\nnames: {NAMES}\n".replace("'", '"'), encoding='utf-8')

MODELS = {
    'baseline': 'results/baseline-e200-best.pt',
    'm3': 'results/m3-fasternet-plus/weights/best.pt',
    'm4': 'results/m4-wsample/weights/best.pt',
    'm5': 'results/m5-best.pt',
}
outdir = Path('results/analysis/prcurves'); outdir.mkdir(parents=True, exist_ok=True)
for name, w in MODELS.items():
    dst = outdir / name
    dst.mkdir(exist_ok=True)
    model = YOLO(w)
    r = model.val(data=str(y), split='val', device='cpu', verbose=False, plots=True,
                  project=str(outdir), name=name, exist_ok=True)
    print(name, 'mAP50 =', round(float(r.box.map50), 4), flush=True)
print('OK -> results/analysis/prcurves/')
