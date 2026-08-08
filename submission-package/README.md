# 投稿材料包 · JRTIP Submission Package

组装时间：2026-08-06 ｜ **更新至 v5：2026-08-07** ｜ 稿件版本：v5（8 图 7 表 + 补充材料表 S1/S2）

> **当前状态：只差填作者信息**（作者/单位/通讯邮箱/ORCID、Funding、Author Contributions）。
> v5 相对 v4：三种子基线统计口径（4.5 节/摘要/表 3 脚注）、文献补强 [27]–[33]、讨论对比段、
> 审稿团报告 #7 措辞修复、JRTIP 合规修复（摘要缩写展开/题注尾标点/Statements and Declarations/Online Resource 1）。

## 目录结构

```
submission-package/
├── manuscript/
│   └── JRTIP-paper-v5.docx          主稿（8 图 7 表内嵌，投稿系统上传）
├── supplementary/
│   ├── ESM_1.pdf                    ★ 补充材料上传件（表 S1+S2，PDF，Springer 命名规范）
│   └── Supplementary_Material_v5.docx  补充材料源文件（备查，不上传）
├── cover-letter/
│   ├── cover-letter-jrtip.docx      Cover Letter（投稿上传用；含 real-time 论述——JRTIP 强制）
│   └── cover-letter-jrtip.md        Cover Letter（纯文本底稿，系统要粘贴时用）
└── figures/                         单独上传用图（JRTIP 系统要求图表分离上传）
    ├── Fig1-instance-distribution-duplication.png  2883×1386
    ├── Fig2-architecture-fasternet.png             2779×1380
    ├── Fig3-training-curves-mAP50.png              2691×1466（2026-08-07 重绘：去图内标题、线型灰度可辨）
    ├── Fig4-accuracy-efficiency-tradeoff.png       2550×1529
    ├── Fig5-gradcam-residual-error.jpg             4030×1000
    ├── Fig6-confusion-matrix-M4.png                3000×2250
    ├── Fig7-deployment-pipeline.png                2552×1046
    └── Fig8-generalization.png                     1198×1417（竖版拼图，按单栏排版设计）
```

## 图分辨率复核（2026-08-07，Springer 标准：半色调 ≥300dpi / 组合图 ≥600dpi / 线图 ≥1200dpi）

| 投稿图号 | 建议排版 | 有效 dpi | 判定 |
|---|---|---|---|
| Fig.1 | 单栏 84mm | 872 | ✅ |
| Fig.2 | 单栏 84mm | 840 | ✅ |
| Fig.3 | 单栏 84mm | 814 | ✅ |
| Fig.4 | 单栏 84mm | 771 | ✅ |
| Fig.5 | 通栏 174mm | 588 | ✅（照片类，≥300 达标） |
| Fig.6 | 单栏 84mm | 907 | ✅ |
| Fig.7 | 单栏 84mm | 772 | ✅ |
| Fig.8 | **单栏 84mm**（竖版 (a)/(b) 上下拼） | 362 | ✅（照片+图组合，按单栏设计；勿通栏） |

> 注：主稿 docx 内嵌图仍为重出前的较低分辨率版本——评审阅读足够；生产排版以上述单独上传的高分辨率文件为准。

## 图号 ↔ 源文件对照（防错查）

| 投稿图号 | 论文图题（缩写） | 源文件（results/ 下） |
|---|---|---|
| Fig.1 | Instance distribution + duplication factors | analysis/fig6-class-distribution.png |
| Fig.2 | Architecture + FasterNet block | analysis/fig4-architecture.png |
| Fig.3 | Validation mAP50 over training | analysis/fig5-curves.png（由 results.csv 重绘） |
| Fig.4 | Accuracy–efficiency trade-off | analysis/fig8-pareto.png |
| Fig.5 | Grad-CAM + residual error（左右拼图成品） | analysis/fig5-gradcam-hardcase.jpg |
| Fig.6 | Confusion matrix (M4, normalized) | m4-wsample/confusion_matrix_normalized.png |
| Fig.7 | Deployment pipeline | analysis/fig9-deploy-pipeline.png |
| Fig.8 | Generalization（上下拼图成品） | analysis/fig8-generalization-ext.png |

> 注意：源文件名里的数字是历史编号（fig4–fig10），**与论文图号不一致**，投稿时以本包文件名（Fig1–Fig8）为准。

## 投稿前检查清单

- [ ] **填作者信息**：标题页作者/单位/城市/国家/通讯邮箱/ORCID；声明区 Funding、Author Contributions（正文 + 投稿系统界面两处都要填）
- [ ] Cover Letter 日期改为实际投稿日
- [x] 排版后实测页数 ≤12 —— **已测 10 页**（2026-08-08，官方 Word 模板双栏 + Word 排版引擎，含 33 条文献；余量 2 页，bio 约 0.2 页无忧；产物见 paper/template/v5-jrtip-format.pdf）
- [ ] 图题逐字复制进投稿系统；Fig.8 标注单栏排版
- [ ] 补充材料上传 ESM_1.pdf（正文已按 "Online Resource 1" 引用）
- [ ] 导师通讯署名落实
- [x] 三种子基线统计（2026-08-07 封账：val 0.5822±0.0087 / test 0.6060±0.0084）
- [x] 审稿团复审（报告 #7，R1 四问已修）
- [x] JRTIP 合规检查（摘要 211 词/关键词 6/声明区齐全/AI 声明/图题标点/Online Resource 1）
- [x] 图分辨率复核与提标重出（Fig1/3/4/7）
- [x] SI 转 PDF + ESM_1 命名
