#!/usr/bin/env python3
"""序列级防泄漏重切分（云端运行，硬链接零拷贝）

背景：源数据集 15 个视频序列在官方 train/valid/test 中全部重叠（序列级泄漏）。
本脚本按序列重切（帧级同源不跨集）：
  test : 2019_11_28_000113（571帧/10类最全）+ 2019_12_10_000060（169帧/5类）= 740帧(13%)
  valid: 2019_11_15_000033（483帧/7类）+ Em（281帧/lying）= 764帧(14%)
  train: 其余 11 源 = 4116帧(73%)

用法：python make_gsplit.py
"""
import os
import re
from pathlib import Path

ROOT = Path('/root/autodl-tmp/dataset')
OUT = Path('/root/autodl-tmp/dataset-gsplit')
TEST = {'2019_11_28_000113', '2019_12_10_000060'}
VALID = {'2019_11_15_000033', 'Em'}


def group_key(stem):
    m = re.match(r'(2019_\d{2}_\d{2}_\d{6})', stem)
    return m.group(1) if m else re.split(r'[-_]', stem)[0]


def split_of(g):
    if g in TEST:
        return 'test'
    if g in VALID:
        return 'valid'
    return 'train'


def main():
    count = {'train': 0, 'valid': 0, 'test': 0}
    for sp in ('train', 'valid', 'test'):
        for img in (ROOT / sp / 'images').glob('*'):
            g = group_key(img.stem)
            dst = split_of(g)
            lbl = ROOT / sp / 'labels' / (img.stem + '.txt')
            (OUT / dst / 'images').mkdir(parents=True, exist_ok=True)
            (OUT / dst / 'labels').mkdir(parents=True, exist_ok=True)
            di = OUT / dst / 'images' / img.name
            dl = OUT / dst / 'labels' / lbl.name
            if not di.exists():
                os.link(img, di)
            if lbl.exists() and not dl.exists():
                os.link(lbl, dl)
            count[dst] += 1
    print('重切分完成:', count)

    # 验证零泄漏
    def keys(sp):
        return {group_key(p.stem) for p in (OUT / sp / 'images').glob('*')}
    t, v, te = keys('train'), keys('valid'), keys('test')
    assert not (t & v) and not (t & te) and not (v & te), '仍存在跨集序列！'
    print('泄漏验证通过：三个子集序列零重叠')

    import yaml
    meta = yaml.safe_load((ROOT / 'data.yaml').read_text(encoding='utf-8'))
    text = (f"path: {OUT.resolve()}\ntrain: train/images\nval: valid/images\ntest: test/images\nnames:\n"
            + ''.join(f"  {i}: {n}\n" for i, n in
                      (meta['names'].items() if isinstance(meta['names'], dict)
                       else enumerate(meta['names']))))
    (OUT / 'data.yaml').write_text(text, encoding='utf-8')
    print('data.yaml 已写入', OUT / 'data.yaml')


if __name__ == '__main__':
    main()
