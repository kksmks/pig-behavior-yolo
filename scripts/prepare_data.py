#!/usr/bin/env python3
"""数据准备：下载公开猪行为数据集并转换为 YOLO 格式。

用法：
  # 1. 转换已有数据集（自动识别 VOC XML / COCO JSON / 已是 YOLO 格式）
  #    视频抽帧数据务必加 --group-sep，按视频分组切分防泄漏：
  python scripts/prepare_data.py convert --src <原始数据目录> --dst data/neau --group-sep _frame

  # 2. 从 Roboflow 下载数据集（需要免费 API key）
  python scripts/prepare_data.py download-roboflow --api-key <KEY> \
      --workspace km-sd0ce --project pig-behavior-wlvku --version 1 --dst data/raw/roboflow

  # 3. 检查转换结果
  python scripts/prepare_data.py verify --dst data/neau
"""
import argparse
import json
import random
import shutil
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def find_images(root: Path) -> dict:
    """{文件名(不含扩展名): 完整路径}"""
    return {p.stem: p for p in root.rglob("*") if p.suffix.lower() in IMG_EXTS}


def parse_voc(root: Path):
    """解析 VOC XML 标注 -> {图像stem: [(类别, xc, yc, w, h), ...]}（归一化）"""
    samples, classes = {}, []
    for xml_path in root.rglob("*.xml"):
        r = ET.parse(xml_path).getroot()
        img_w = float(r.findtext("size/width", 0))
        img_h = float(r.findtext("size/height", 0))
        if img_w <= 0 or img_h <= 0:
            continue
        boxes = []
        for obj in r.findall("object"):
            name = (obj.findtext("name") or "").strip()
            bb = obj.find("bndbox")
            if not name or bb is None:
                continue
            xmin, ymin = float(bb.findtext("xmin")), float(bb.findtext("ymin"))
            xmax, ymax = float(bb.findtext("xmax")), float(bb.findtext("ymax"))
            if xmax <= xmin or ymax <= ymin:
                continue
            boxes.append((name, (xmin + xmax) / 2 / img_w, (ymin + ymax) / 2 / img_h,
                          (xmax - xmin) / img_w, (ymax - ymin) / img_h))
            if name not in classes:
                classes.append(name)
        if boxes:
            samples[xml_path.stem] = boxes
    return samples, classes


def parse_coco(root: Path):
    """解析 COCO JSON 标注 -> 同 parse_voc"""
    jsons = sorted(root.rglob("*.json"))
    if not jsons:
        return {}, []
    ann = json.loads(jsons[0].read_text(encoding="utf-8"))
    cats = sorted(ann["categories"], key=lambda c: c["id"])
    classes = [c["name"] for c in cats]
    id2idx = {c["id"]: i for i, c in enumerate(cats)}
    imgs = {im["id"]: im for im in ann["images"]}
    samples = {}
    for a in ann["annotations"]:
        im = imgs[a["image_id"]]
        x, y, w, h = a["bbox"]
        stem = Path(im["file_name"]).stem
        samples.setdefault(stem, []).append(
            (classes[id2idx[a["category_id"]]],
             (x + w / 2) / im["width"], (y + h / 2) / im["height"],
             w / im["width"], h / im["height"]))
    return samples, classes


def parse_yolo(root: Path):
    """已是 YOLO 格式（.txt + classes 文件）-> 同 parse_voc"""
    classes = []
    for f in ("classes.txt", "obj.names", "data.yaml"):
        p = root / f
        if not p.exists():
            continue
        if p.suffix == ".yaml":
            import yaml
            names = yaml.safe_load(p.read_text(encoding="utf-8")).get("names", [])
            classes = list(names.values()) if isinstance(names, dict) else list(names)
        else:
            classes = [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
        break
    if not classes:
        return {}, []
    samples = {}
    for txt in root.rglob("*.txt"):
        if txt.name in ("classes.txt",):
            continue
        boxes = []
        for line in txt.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) == 5:
                i, xc, yc, w, h = int(parts[0]), *map(float, parts[1:])
                if i < len(classes):
                    boxes.append((classes[i], xc, yc, w, h))
        if boxes:
            samples[txt.stem] = boxes
    return samples, classes


def write_dataset(samples, classes, images, dst: Path, val_ratio, test_ratio, seed=42,
                  group_sep=None):
    """按比例切分并写出 YOLO 目录结构 + data.yaml。

    group_sep: 视频抽帧数据必须设置（如 "_frame"）。按帧名前缀分组切分，
    保证同一视频的所有帧只进入一个子集，防止相邻帧泄漏导致指标虚高。
    """
    items = sorted(samples.items())
    rng = random.Random(seed)
    if group_sep:
        groups = {}
        for stem, boxes in items:
            key = stem.rsplit(group_sep, 1)[0] if group_sep in stem else stem
            groups.setdefault(key, []).append((stem, boxes))
        keys = sorted(groups)
        rng.shuffle(keys)
        n = len(keys)
        n_test, n_val = int(n * test_ratio), int(n * val_ratio)
        splits = {"test": [it for k in keys[:n_test] for it in groups[k]],
                  "val": [it for k in keys[n_test:n_test + n_val] for it in groups[k]],
                  "train": [it for k in keys[n_test + n_val:] for it in groups[k]]}
        print(f"按视频分组切分（分隔符 '{group_sep}'，共 {n} 组），防止同视频帧跨集泄漏")
    else:
        rng.shuffle(items)
        n = len(items)
        n_test, n_val = int(n * test_ratio), int(n * val_ratio)
        splits = {"test": items[:n_test], "val": items[n_test:n_test + n_val],
                  "train": items[n_test + n_val:]}
    cls2idx = {c: i for i, c in enumerate(classes)}
    missing = 0
    for split, rows in splits.items():
        (dst / "images" / split).mkdir(parents=True, exist_ok=True)
        (dst / "labels" / split).mkdir(parents=True, exist_ok=True)
        for stem, boxes in rows:
            img = images.get(stem)
            if img is None:
                missing += 1
                continue
            shutil.copy2(img, dst / "images" / split / img.name)
            lines = [f"{cls2idx[c]} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n" for c, xc, yc, w, h in boxes]
            (dst / "labels" / split / f"{stem}.txt").write_text("".join(lines), encoding="utf-8")
    if missing:
        print(f"[警告] {missing} 条标注找不到对应图像，已跳过")
    yaml_text = (f"# 由 prepare_data.py 生成\npath: {dst.resolve()}\n"
                 f"train: images/train\nval: images/val\ntest: images/test\nnames:\n"
                 + "".join(f"  {i}: {c}\n" for i, c in enumerate(classes)))
    (dst / "data.yaml").write_text(yaml_text, encoding="utf-8")
    print(f"完成：train={len(splits['train'])} val={len(splits['val'])} test={len(splits['test'])}")
    print(f"类别({len(classes)}): {classes}")
    print(f"配置已写入 {dst / 'data.yaml'}")


def cmd_convert(args):
    src, dst = Path(args.src), Path(args.dst)
    if not src.exists():
        sys.exit(f"源目录不存在: {src}")
    for fmt, parser in (("VOC", parse_voc), ("COCO", parse_coco), ("YOLO", parse_yolo)):
        samples, classes = parser(src)
        if samples:
            print(f"检测到 {fmt} 格式，共 {len(samples)} 张有标注图像")
            break
    else:
        sys.exit("未识别到任何标注（支持 VOC XML / COCO JSON / YOLO txt）")
    write_dataset(samples, classes, find_images(src), dst, args.val, args.test,
                  group_sep=args.group_sep)


def cmd_download_roboflow(args):
    try:
        from roboflow import Roboflow
    except ImportError:
        sys.exit("请先安装: pip install roboflow")
    rf = Roboflow(api_key=args.api_key)
    rf.workspace(args.workspace).project(args.project) \
        .version(args.version).download("yolov8", location=str(args.dst))
    print(f"已下载到 {args.dst}（YOLO 格式，可直接用 verify 检查）")


def cmd_verify(args):
    dst = Path(args.dst)
    counter = Counter()
    for split in ("train", "val", "test"):
        imgs = list((dst / "images" / split).glob("*")) if (dst / "images" / split).exists() else []
        labels = list((dst / "labels" / split).glob("*.txt")) if (dst / "labels" / split).exists() else []
        print(f"{split}: {len(imgs)} 图像, {len(labels)} 标注")
        for lb in labels:
            for line in lb.read_text(encoding="utf-8").splitlines():
                if line.split():
                    counter[int(line.split()[0])] += 1
    print("各类别标注框数量:", dict(sorted(counter.items())))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("convert", help="转换已有数据集为 YOLO 格式")
    p.add_argument("--src", required=True, help="原始数据集目录")
    p.add_argument("--dst", required=True, help="输出目录，如 data/neau")
    p.add_argument("--val", type=float, default=0.15, help="验证集比例")
    p.add_argument("--test", type=float, default=0.15, help="测试集比例")
    p.add_argument("--group-sep", default=None,
                   help="视频抽帧数据必填：帧名中的分组分隔符，如 '_frame'，"
                        "使同一视频的帧不跨子集（防止数据泄漏、指标虚高）")
    p.set_defaults(func=cmd_convert)

    p = sub.add_parser("download-roboflow", help="从 Roboflow 下载数据集")
    p.add_argument("--api-key", required=True)
    p.add_argument("--workspace", required=True)
    p.add_argument("--project", required=True)
    p.add_argument("--version", type=int, default=1)
    p.add_argument("--dst", type=Path, default=Path("data/raw/roboflow"))
    p.set_defaults(func=cmd_download_roboflow)

    p = sub.add_parser("verify", help="检查数据集统计信息")
    p.add_argument("--dst", required=True)
    p.set_defaults(func=cmd_verify)

    args = ap.parse_args()
    args.func(args)
