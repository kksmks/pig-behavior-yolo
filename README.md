# Pig Behavior Detection —— Real-Time Multi-Behavior Detection on Edge Devices

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Ultralytics](https://img.shields.io/badge/ultralytics-8.4.105-green)](https://github.com/ultralytics/ultralytics)
[![License](https://img.shields.io/badge/license-CC%20BY%204.0-orange)](https://creativecommons.org/licenses/by/4.0/)

> **Paper**: *Real-Time Multi-Behavior Detection of Group-Housed Pigs on Edge Devices: Class-Imbalance-Aware Sampling and a Lightweight FasterNet Backbone*  
> **Target Journal**: Journal of Real-Time Image Processing (JRTIP), Springer  
> **Status**: Manuscript v4 in preparation (figure/table compression for JRTIP page limit). Temporal smoothing evaluated and **rejected** on the sparse-frame benchmark (2026-08-05, see EXPERIMENT_LOG).

---

## Overview

This repository contains the code, data preparation scripts, and deployment pipeline for a real-time pig behavior detection framework. The work addresses three practical gaps in the precision livestock farming (PLF) literature:

1. **Class imbalance**: Rare welfare-relevant behaviors (drinking, active, sitting) are overshadowed by frequent classes (resting, investigating).
2. **Server-only evaluation**: Most prior works benchmark on high-end GPUs; edge viability is undocumented.
3. **Over-optimistic generalization**: Random-frame splits inflate accuracy; cross-farm performance is rarely measured.

**Key Results** (YOLOv11n baseline → our framework):
- Rare-class `active` AP50: **52.6% → 63.9%** (+11.3 points)
- Overall test mAP50: statistically comparable (59.6% → 59.3%, within 1σ)
- Parameters: **−4.4%** (2.58M → 2.47M)
- Jetson Nano deployment: **19.7 FPS** @ 640×640, **33.3 FPS** @ 480×480 (~5 W)

---

## Repository Structure

```
pig-behavior-yolo/
├── scripts/
│   ├── train.py              # Unified training entry (baseline & variants)
│   ├── prepare_data.py       # Dataset conversion (VOC/COCO → YOLO, --group-sep)
│   ├── export_deploy.py      # ONNX → TensorRT export for Jetson Nano
│   ├── temporal_smooth.py    # Temporal smoothing (post-processing tracker)
│   ├── analysis_detect.py    # Per-class AP & detection visualization
│   ├── analysis_gradcam.py   # Grad-CAM attention maps
│   ├── build_figures.py      # Paper figure generation
│   └── cloud.py              # Remote AutoDL training automation
├── configs/
│   └── yolo11-fasternet-n.yaml   # M5: FasterNet backbone substitution
├── notebooks/
│   ├── colab_baseline.ipynb      # Baseline YOLOv11n (Colab)
│   ├── colab_compare.ipynb       # Fleet comparison (YOLOv5/8/12, RT-DETR)
│   └── colab_m2_emar.ipynb       # M2 training notebook (archived)
├── autodl/
│   ├── baseline_train.py     # AutoDL remote scripts
│   ├── m3_train.py           # M3: FasterNet only
│   ├── m4_train.py           # M4: class-imbalance-aware sampling
│   ├── m5_train.py           # M5: FasterNet + sampling (final model)
│   ├── m6_train.py           # M6: YOLOv12n + sampling (negative control)
│   └── fps_bench.py          # RTX 3090 FPS benchmarking
├── data/
│   ├── dataset/              # Roboflow pig-behavior (train/val/test)
│   └── comportamentos/       # External validation set (cross-farm)
├── results/                  # Training outputs (weights, curves, metrics.json)
└── paper/                    # Manuscript drafts & review materials
```

---

## Quick Start

### 1. Environment

```bash
pip install -r requirements.txt
```

Core dependencies: `ultralytics>=8.4.105`, `torch>=2.1.0`, `numpy`, `opencv-python`, `matplotlib`, `seaborn`.

### 2. Data Preparation

The primary dataset is publicly available on Roboflow Universe ([pig-behavior](https://universe.roboflow.com/km-sd0ce/pig-behavior-wlvku), CC BY 4.0). The external validation set is [Comportamentos](https://universe.roboflow.com/maria-dnxxx/comportamentos-vdzlw), also CC BY 4.0.

```bash
# Download from Roboflow (inside Colab or with proxy)
python scripts/prepare_data.py download-roboflow \
    --api-key <YOUR_KEY> --workspace km-sd0ce \
    --project pig-behavior-wlvku --version 1 --dst data/raw/roboflow

# Convert and verify
python scripts/prepare_data.py convert --src data/raw/roboflow --dst data/dataset
python scripts/prepare_data.py verify --dst data/dataset
```

### 3. Training

```bash
# Baseline (YOLOv11n)
python scripts/train.py --model yolo11n.pt --data data/dataset/data.yaml \
    --name baseline --epochs 200 --device 0

# M5 (FasterNet + sampling) — final model
python autodl/m5_train.py  # or adapt scripts/train.py with the M5 config
```

### 4. Temporal Smoothing (Post-Processing) — rejected on this benchmark

> **Honest status (2026-08-05):** on the sparse-frame validation split (frames sampled
> tens-to-hundreds of frames apart), IoU-based tracking fails and majority voting
> corrupts correct single-frame labels: mAP50 −2.66 (w3v2), −1.27 (w5v4), or zero
> effect (w3v3). No parameter setting helps. The technique remains legitimate for
> **dense consecutive frames** (live video on the Nano) but cannot be validated on
> this dataset and is **not claimed as an accuracy improvement** in the paper.
> Evaluation: `scripts/eval_temporal_map.py` (official-protocol mAP comparator).

```bash
# Step 1: Run detection on validation/test set
python scripts/temporal_smooth.py detect \
    --weights results/m5-fastnet-wsample/weights/best.pt \
    --data data/dataset/data.yaml --split val \
    --out results/temporal/predictions.json

# Step 2: Apply temporal smoothing (IoU tracking + majority vote)
python scripts/temporal_smooth.py smooth \
    --pred results/temporal/predictions.json \
    --window 3 --vote-thresh 2 \
    --out results/temporal/smoothed.json

# Step 3: Evaluate class distribution change
python scripts/temporal_smooth.py eval \
    --pred results/temporal/smoothed.json \
    --data data/dataset/data.yaml
```

### 5. Edge Deployment (Jetson Nano)

```bash
# On PC: export ONNX
python scripts/export_deploy.py --weights results/m5/weights/best.pt \
    --format onnx --half --imgsz 640

# Copy to Nano via scp, then build TensorRT engine on device
python scripts/export_deploy.py --weights best.onnx --format engine --half
```

---

## Model Variants

| Model | Description | Test mAP50 | Params | FPS@3090 |
|-------|-------------|:----------:|:------:|:--------:|
| Baseline | YOLOv11n | 0.596 | 2.58M | 112.8 |
| M3 | FasterNet backbone only | 0.569 | 2.47M | — |
| M4 | Class-imbalance sampling only | **0.604** | 2.58M | 112.1 |
| **M5** | **FasterNet + sampling (final)** | 0.593 | **2.47M** | **117.6** |
| M6 | YOLOv12n + sampling (negative) | 0.599 | 2.56M | 78.4 |

Full ablation and comparison tables are in the paper (`paper/JRTIP-paper-v3.docx`).

---

## Key Design Decisions

### Identity-Preserving Integration
When adapting pre-trained detectors, we found that inserting randomly initialized gating modules (e.g., EMA attention) corrupted the pre-trained feature distribution and cost 3–7 mAP points. Our solution: **keep channel flow intact** and transfer weights via index-aligned remapping (316/415 tensors). Only the task-specific classification head is re-initialized.

### Class-Imbalance-Aware Sampling
Instead of modifying the loss or network, we adjust the training data distribution offline:
- Each image is duplicated by `factor = min(5, round(√(N_max / N_rare)))` where `N_rare` is the rarest class present in the image.
- Hard links are used; no extra disk space.
- Validation and test sets remain untouched.

### Two-Level Generalization Analysis
We report results honestly:
1. **Unseen-sequence stress test**: sequence-disjoint split reveals all models degrade sharply.
2. **Cross-dataset zero-shot**: on an independent farm (Comportamentos), all models collapse to 0.036–0.067 mAP50.

This delimits where the framework works (same-farm deployment today) and where it does not (cross-farm adaptation is future work).

---

## Citation

```bibtex
@dataset{pig-behavior-roboflow,
  title = {Pig Behavior Dataset},
  publisher = {Roboflow Universe},
  version = {1},
  license = {CC BY 4.0},
  url = {https://universe.roboflow.com/km-sd0ce/pig-behavior-wlvku}
}

@inproceedings{bergamini2021extracting,
  title = {Extracting accurate long-term behavior changes from a large pig dataset},
  author = {Bergamini, L. and Pini, S. and Simoni, A. and others},
  booktitle = {VISIGRAPP},
  year = {2021}
}
```

---

## License

- **Code**: MIT License
- **Data**: CC BY 4.0 (Roboflow Universe terms)

---

## Contact

- **Author**: [To be filled]
- **Institution**: [To be filled]
- **Email**: [To be filled]

AI-assisted tools were used for language polishing and code assistance. All experiments, measurements, and reported numbers were produced and verified by the authors.
