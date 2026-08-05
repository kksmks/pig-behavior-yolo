# 投稿材料包 · JRTIP Submission Package

组装时间：2026-08-06 ｜ 稿件版本：v4 定稿（8 图 7 表 + Table S1）

## 目录结构

```
submission-package/
├── manuscript/
│   └── JRTIP-paper-v4.docx          主稿（8 图 7 表内嵌）
├── supplementary/
│   └── Supplementary_Material.docx  补充材料（Table S1 每类 AP）
├── cover-letter/
│   ├── cover-letter-jrtip.docx      Cover Letter（投稿上传用）
│   └── cover-letter-jrtip.md        Cover Letter（纯文本底稿，系统要粘贴时用）
└── figures/                         单独上传用图（JRTIP 系统要求图表分离上传）
    ├── Fig1-instance-distribution-duplication.png  1342×644
    ├── Fig2-architecture-fasternet.png             2779×1380
    ├── Fig3-training-curves-mAP50.png              1579×980
    ├── Fig4-accuracy-efficiency-tradeoff.png       1186×711
    ├── Fig5-gradcam-residual-error.jpg             4030×1000
    ├── Fig6-confusion-matrix-M4.png                3000×2250
    ├── Fig7-deployment-pipeline.png                1187×486
    └── Fig8-generalization.png                     1198×1417
```

## 图号 ↔ 源文件对照（防错查）

| 投稿图号 | 论文图题（缩写） | 源文件（results/ 下） |
|---|---|---|
| Fig.1 | Instance distribution + duplication factors | analysis/fig6-class-distribution.png |
| Fig.2 | Architecture + FasterNet block | analysis/fig4-architecture.png |
| Fig.3 | Validation mAP50 over training | analysis/fig5-curves.png |
| Fig.4 | Accuracy–efficiency trade-off | analysis/fig8-pareto.png |
| Fig.5 | Grad-CAM + residual error（左右拼图成品） | analysis/fig5-gradcam-hardcase.jpg |
| Fig.6 | Confusion matrix (M4, normalized) | m4-wsample/confusion_matrix_normalized.png |
| Fig.7 | Deployment pipeline | analysis/fig9-deploy-pipeline.png |
| Fig.8 | Generalization（上下拼图成品） | analysis/fig8-generalization-ext.png |

> 注意：源文件名里的数字是历史编号（fig4–fig10），**与论文图号不一致**，投稿时以本包文件名（Fig1–Fig8）为准。

## 投稿前检查清单

- [ ] 用户通读中英 v4 完毕，导师意见已回收并处理
- [ ] 旧 Roboflow key 已吊销换新（数据可用性声明不含 key，安全）
- [ ] 排版后实测英文版页数 ≤12；超页执行预案（Fig.3→补充 / Table 2→正文，见 STATE.md）
- [ ] 投稿系统图题逐字从主稿复制（避免手打出入）
- [ ] Cover Letter 中通讯作者信息与投稿系统填写一致（导师通讯署名落实后核对）

## 分辨率说明

全部图按单栏（约 3.5 in）排版时等效 ≥330 dpi；Fig.2 / Fig.5 / Fig.6 / Fig.8 跨双栏（约 7 in）仍 ≥290 dpi，满足 Springer 系期刊线图要求。若系统提示分辨率不足，优先重导 Fig.4 / Fig.7（当前最小的两张）。
