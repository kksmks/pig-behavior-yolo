# 项目结构导览（PROJECT MAP）

> 更新：2026-08-18 ｜ 项目：群养猪多行为实时检测（YOLOv11n + 类别不均衡采样 + FasterNet 轻量化 + Jetson Nano 部署），目标刊 JRTIP
> 图例：📄 文档 ｜ 🐍 脚本 ｜ 📊 数据/结果 ｜ 📦 交付物 ｜ ⛔ git 忽略（不入库）

```
pig-behavior-yolo/
│
├── README.md                    📄 仓库门面：项目简介、关键结果、Quick Start、复现指引
├── STATE.md                     📄 【断点续传总状态】新会话先读它——当前进度、全部决策、逐时戳更新记录
├── PROGRESS.md                  📄 里程碑体系（每 5% 一格，已 100%）
├── LOG.md                       📄 每日操作日志（早期手工流水）
├── JRTIP-revision-plan.md       📄 JRTIP 投稿作战计划（选刊、叙事框架、防线）
├── LICENSE                      📄 MIT（代码）；数据为 CC BY 4.0
├── requirements.txt             📄 Python 依赖清单
├── yolo11n.pt                   📊 YOLOv11n 官方预训练权重（基线起点）
├── yolo11-fasternet-n.yaml      📄 M5 模型结构配置（FasterNet 主干替换版）
│
├── paper/                       📦 【论文一切】
│   ├── JRTIP-paper-v5.docx          ★ 英文投稿主稿（当前版，8 图 7 表，10/12 页）
│   ├── 猪行为检测-中文成稿-v5.docx    ★ 中文版（送导师评审用，与英文同口径）
│   ├── Supplementary_Material_v5.docx  英文补充材料（表 S1/S2 + 图 S1–S3）
│   ├── 猪行为检测-补充材料-v5.docx     中文补充材料
│   ├── cover-letter-jrtip.md/.docx   JRTIP Cover Letter（real-time 论述 + 主动披露切分）
│   ├── author-info-template.md       ★ 作者信息填空模板（投稿前必办）
│   ├── REVIEW_BOARD.md               模拟审稿团全部报告（#1–#8 + #8-补，含 10 维审查标准）
│   ├── REVIEW_CHECKLIST.md           评审检查清单
│   ├── Q3-plan.md                    早期 Q3/Q4 冲刺计划
│   ├── journal-choice.md             选刊决策记录（JRTIP 主投 / EcoInfo 冲刺 / INMATEH 保底）
│   ├── outline.md / polish-v5-diff.md  提纲与 v5 人味化润色对照清单
│   ├── lit-review-training.md / lit-review-yolo12.md  文献调研笔记
│   ├── problem-log.md                踩坑记录（论文素材：onnxslim/cuDNN/INT8 等）
│   ├── tables/                       表格素材源（行为定义、每类 AP 原始表）
│   ├── template/                     JRTIP 官方 Word 模板 + 排版产物（v5-jrtip-format.docx/pdf，PAGES=10 实测）
│   └── draft-v1/v2-*.md 等           ⛔ 历史过程稿（留痕用，以 v5 为准）
│
├── scripts/                     🐍 【全部工具脚本】
│   ├── build_paper_docx*.py         成稿组装器（英文版注意：v5 是补丁制，勿用它整建英文稿）
│   ├── apply_v5_*.py                v5 系列补丁脚本（润色/合规/分解段/换图/小修，均带锚点断言）
│   ├── build_supplementary_zh*.py   补充材料组装器（中英）
│   ├── audit_jrtip_format.py        JRTIP 合规机查（26 项：摘要词数/引用/题注/声明…）
│   ├── paginate_jrtip.py            官方模板排版 + Word COM 页数实测
│   ├── build_figures.py             正文图源（分布/每类/帕累托/管线/泛化，600dpi 规范）
│   ├── analysis_detect.py / analysis_gradcam.py  检测效果图 / Grad-CAM 素材
│   ├── prepare_data.py              数据集下载/转换/校验
│   ├── train.py / export_deploy.py  训练入口 / ONNX→TRT 导出
│   ├── temporal_smooth.py / eval_temporal_map.py / run_temporal_inference.py  时序平滑（已否决，留证）
│   ├── cloud.py                     AutoDL 直连（status/exec/pull/push，CLOUD_PASS 环境变量）
│   └── nano/                        Jetson Nano 测量包（pre/post_bench、热节流解析、PR 曲线产出、补充图源）
│
├── autodl/                      🐍 云端训练包（AutoDL 时代产物）
│   ├── README.md / setup.sh         云端环境手册与初始化
│   ├── baseline_train.py / baseline_3seeds.py  基线 200 轮 + 三种子
│   ├── m3_train.py / m4_train.py / m5_train.py / m6_train.py  各变体训练脚本
│   ├── compare_fleet.py / fps_bench.py  对照组（v5n/v8n/v12n/RT-DETR）与 3090 FPS 基准
│   ├── make_gsplit.py               序列互斥切分（压力测试）生成器
│   └── yolo11-*.yaml                各模型配置
│
├── configs/                     📄 模型配置（yolo11-fasternet-n.yaml 正本）
├── notebooks/                   📄 Colab 时代笔记本（baseline / compare，已被 autodl 流程取代）
├── archive/                     📦 废案归档（M1/M1' 注意力失败案、Kaggle 废案，附 ARCHIVE.md 索引）
│
├── data/                        📊 【数据集】（⛔ 全目录 git 忽略）
│   ├── dataset/                     主数据集（Roboflow 猪行为 5,620 图，train/valid/test + data.yaml）
│   ├── comportamentos/              外部验证集（696 图，异农场异品种，CC BY 4.0）
│   ├── ext-eval/                    外部评估中间产物
│   ├── raw/  tmp/                   原始下载与临时文件
│   └── *.zip / annotated.tar        数据压缩包
│
├── results/                     📊 【实验结果】（核心件入库，大件忽略）
│   ├── EXPERIMENT_LOG.md            ★ 实验总账（每次训练的指标与判决，论文数字的唯一真源）
│   ├── baseline*/ m1*/ m2*/ m3*/ m4*/ m5*/ m6*/ yolo*/ rtdetr-l/  各实验目录（metrics.json 已入库）
│   ├── baseline-e200-best.pt / m5-best.pt  两个关键权重（已入库）
│   ├── analysis/                    论文图片素材（fig 系列、figS 系列、gradcam/、detections/、prcurves/）
│   ├── deploy/thermal/              热节流与功耗实测日志（thermal.log + INA3221 采样）
│   └── temporal/                    时序平滑否决实验产物
│
├── submission-package/          📦 【投稿材料包】（直接上传投稿系统的内容）
│   ├── README.md                    包说明与检查清单
│   ├── manuscript/                  主稿 docx（与 paper/ 当前版同步）
│   ├── supplementary/               补充材料 docx + ESM_1.pdf（上传版）
│   ├── cover-letter/                Cover Letter（与 paper/ 同步）
│   └── figures/                     高分辨率图件（Fig1–8 重命名版，单独上传用）
│
└── runs/                        ⛔ ultralytics 自动输出（val/predict 副产物，不入库）
```

## 新会话/新人 5 分钟上手路径

1. 先读 `STATE.md`——全部当前状态与最近决策都在里面（断点续传文件）
2. 再读 `README.md`——项目门面与关键结果
3. 要碰论文：读 `paper/REVIEW_BOARD.md`（最新报告在最前）+ `JRTIP-revision-plan.md`
4. 要碰数字：唯一真源是 `results/EXPERIMENT_LOG.md` + 各实验目录 `metrics.json`，不信记忆
5. 要跑实验：训练在 `autodl/`（云端），测量在 `scripts/nano/`（Nano），构图在 `scripts/build_figures.py`

## 几条容易踩的规矩

- **英文主稿不是脚本整建的**：v4 由 `build_paper_docx.py` 建，v5 全靠 `apply_v5_*.py` 补丁叠加——改英文稿请写新 apply 脚本（带锚点断言），勿整建覆盖
- **中文版是脚本整建的**：改 `build_paper_docx_zh_v5.py` 后直接重建
- **投稿包是手动同步的**：改完 `paper/` 当前版后，记得覆盖 `submission-package/` 对应件
- **git 提交先确认**：本项目规矩——任何 git 写操作前必须用户点头；push 失败走代理 `127.0.0.1:7897`
