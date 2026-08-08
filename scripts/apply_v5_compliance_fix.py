# -*- coding: utf-8 -*-
"""
apply_v5_compliance_fix.py — 2026-08-08 格式合规体检后的三处修复（英文 v5 主稿）：
1. Conflicts of Interest → Competing Interests（JRTIP Statements and Declarations 规定的标签名）
2. [2] Peden 2018 补 DOI（10.1016/j.applanim.2018.03.003，SRUC 机构库核实）
3. [18] Gu 2024 文章号 109524 → 109512（ScienceDirect 核实，原系笔误）并补 DOI
同步刷新 submission-package/manuscript/JRTIP-paper-v5.docx。
"""
import shutil
from pathlib import Path
from docx import Document

ROOT = Path(__file__).resolve().parent.parent
MS = ROOT / 'paper' / 'JRTIP-paper-v5.docx'
PKG = ROOT / 'submission-package' / 'manuscript' / 'JRTIP-paper-v5.docx'

REPL = [
    ('Conflicts of Interest: The authors declare no conflict of interest.',
     'Competing Interests: The authors declare no competing interests.'),
    ('practice: the case of mixing aggression between pigs. Appl. Anim. Behav. Sci. 204, 1–9 (2018)',
     'practice: the case of mixing aggression between pigs. Appl. Anim. Behav. Sci. 204, 1–9 (2018). '
     'https://doi.org/10.1016/j.applanim.2018.03.003'),
    ('Comput. Electron. Agric. 227, 109524 (2024)',
     'Comput. Electron. Agric. 227, 109512 (2024). https://doi.org/10.1016/j.compag.2024.109512'),
]

doc = Document(str(MS))
hits = 0
for p in doc.paragraphs:
    for old, new in REPL:
        if old in p.text:
            # 段内替换：保留首个 run 格式，清空其余
            done = False
            for r in p.runs:
                if old in r.text:
                    r.text = r.text.replace(old, new)
                    done = True
                    break
            if not done:
                # 跨 run 情况：整段重建（本文件参考段为单 run，兜底用）
                full = p.text.replace(old, new)
                for r in p.runs[1:]:
                    r.text = ''
                if p.runs:
                    p.runs[0].text = full
            hits += 1
            print(f'FIXED: {old[:60]}…')

assert hits == len(REPL), f'只命中 {hits}/{len(REPL)} 处，中止'
doc.save(str(MS))
shutil.copy(str(MS), str(PKG))
print(f'OK: {hits} 处修复，已同步 {PKG.name}')
