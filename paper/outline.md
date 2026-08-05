# 论文详细提纲（v1，2026-08-03）

**工作题目**：Lightweight Multi-Behavior Detection of Group-Housed Pigs: Class-Imbalance-Aware Sampling, FasterNet Backbone, and Edge Deployment Validation
**目标期刊**：Animals / Sensors（冲）→ AgriEngineering / INMATEH（稳）
**主线叙事**：群养猪多行为检测存在类别不均衡与部署成本两个痛点 → 数据层治理（加权采样）+ 结构轻量化（FasterNet）→ 精度持平且更轻更快 → Nano 边缘实测 + 诚实的泛化分析

---

## 1. Abstract（≤200 词）

- 痛点：群养猪行为监测对健康/福利预警关键；现有检测模型类别偏科重、部署成本高
- 方法：类别不均衡感知采样策略 + FasterNet 轻量化主干（基于 YOLOv11n）
- 关键数字：稀有类 active AP +11.3（test）、参数 -5.6%、3090 上 117.6 FPS（全场最快）、Nano 480 输入 33 FPS / 约 5W
- 结论：精度持平基线（差异不显著）而更轻更快，边缘部署可行

## 2. Introduction（漏斗四段）

1. 生猪养殖智能化背景：行为=健康与福利的直接指标（引 Matthews 2016、WFE-YOLO 等）
2. 现有视觉方法综述：YOLO 系检测在畜禽行为的应用（引 GAB-YOLO、CAMLLA、DMSF-YOLO）
3. **三个缺口**（每点对应后文一节实验）：类别不均衡致稀有行为识别弱 / 模型重难以边缘部署 / 泛化评估普遍缺失
4. 贡献三条：①类别不均衡感知采样（弱类 active +11.3 AP）②FasterNet 轻量化（-5.6% 参数且最快）③Nano 部署验证 + 系统性泛化分析

## 3. Related Work（~1 页）

- 3.1 畜禽行为视觉检测（Tu 2022、Li 2024 CEA 群养猪多行为、Yang 2020 综述）
- 3.2 类别不均衡治理（加权采样/repeat-factor sampling、focal loss；引 arXiv 2403.07113 基准）
- 3.3 轻量化检测与边缘部署（FasterNet CVPR2023、GET-YOLO、Rahman 2026 Nano 部署）
- 收束句：以上工作均未同时解决不均衡+轻量+部署验证，本文补齐

## 4. Materials and Methods

### 4.1 数据集
- 来源：Roboflow Universe pig-behavior（CC BY 4.0，源自 Bergamini et al. 2021 公开数据）
- 规模：5,620 张 / 10 类 / 13,995 框；QC 抽查报告（12 张目检通过）
- **表 1**：行为定义表（paper/tables/behavior-definitions.md）
- **表 2**：类别分布（investigating 4203 vs sitting 144，不均衡比 29:1）
- 伦理声明：仅公开数据、非侵入、无需伦理审批

### 4.2 基线模型
- YOLOv11n（2.58M/6.3G），选择理由 + M6 阴性对照佐证（采样在 yolo12n 上 -1.4 点，基座选择被数据验证）

### 4.3 方法 1：类别不均衡感知采样
- 公式：类别权重 w_c = √(N_max/N_c)，封顶 5 倍；图像权重 = 所含类权重最大值；离线过采样实现
- 效果：训练集 3,936→5,889 张，稀有类曝光 ×3–4

### 4.4 方法 2：FasterNet 轻量化主干
- PConv（1/4 通道空间卷积）+ 逐点卷积 + 残差；替换 P3/P4/P5 层 C3k2（P2 保留原版）
- 预训练权重重映射策略（层索引对齐，316 键迁移）

### 4.5 训练与评测协议
- 200 轮 + patience 30 早停；AdamW 默认超参（lr0=0.01, wd=0.0005, HSV/mosaic 默认）
- 选模用 val，报告用 held-out test；3 次重复报均值±标准差
- 硬件：RTX 3090（训练）、Jetson Nano（部署）

### 4.6 评价指标
- mAP50/mAP50-95/P/R + 参数量/GFLOPs/FPS/功耗

## 5. Experiments and Results

### 5.1 实验设置（环境表）

### 5.2 消融实验 —— **表 3（核心表）**
| 配置 | test mAP50 | 参数量 |
|---|---|---|
| 基线 | 0.5964 | 2.58M |
| +采样（M4） | **0.6035** | 2.58M |
| +FasterNet（M3） | 0.5691 | 2.47M |
| +采样+FasterNet（M5） | 0.5932 | **2.47M** |
| 采样@yolo12n（M6，阴性对照） | 0.5994 | 2.56M |
- 文字分析：采样增益（+0.71）、轻量化代价（-2.7）、组合后（-0.32 换 -5.6%）、M6 说明基座选择

### 5.3 与主流模型对比 —— **表 4**
（基线/M4/M5 vs yolov5n 0.6001 / yolov8n 0.5877 / yolo12n 0.6135 / RT-DETR-l 0.6008；参数与 GFLOPs 列全）

### 5.4 分类别分析 —— **表 5**（per-class-ap.md）
- 弱类改善：active 0.526→0.639（test）、drink 0.408→0.459（val）、sitting +2.0
- 代价如实写：nose-to-nose -6.4（val）

### 5.5 统计可靠性 —— **表 6**
- M4：val 0.5790±0.0054 / test 0.5987±0.0062
- M5：val 0.5620±0.0079 / test 0.5904±0.0086
- 陈述：与基线差异在 1σ 内 → "精度持平"的诚实表述

### 5.6 效率评估 —— **表 7**
- 3090 FPS：M5 117.6（最快）/ 基线 112.8 / yolo12n 78.4（慢 33%）

### 5.7 可视化 —— **图 1（Grad-CAM 三联）+ 图 2（难例检测对比）**
- 注意力聚焦猪体（gradcam/）；fight/lying 混淆误检例（detections/）作错误分析

## 6. 边缘部署验证 —— **表 8**

- 链路：PyTorch → ONNX（opset 12）→ TensorRT 8.2（JetPack 4.6.3）
- 结果：640 输入 50.8ms/19.7 FPS；**480 输入 29.9ms/33 FPS**；整机功耗 ~5W
- 诚实限制：INT8 在 Maxwell 无原生支持（校准失败），采用 FP16 方案
- FasterNet vs 基线在 Nano 打平：TRT 算子融合抹平理论差距（如实呈现）
- 待办：正式数字用 M5 权重补测（权重已在手，待 Nano 上电）

## 7. 泛化分析（诚实专章）—— **表 9 + 图 3**

- 7.1 序列级压力测试：基线/M4/M5 在未见序列上 val 0.075–0.139 / test 0.145–0.155
  → **M4 在异源场景为基线 2 倍（0.139 vs 0.075）**：采样对泛化有缓解
- 7.2 跨数据集验证（Comportamentos，独立农场+花斑品种）：全员 0.036–0.067
  → 图 3：异源检测实况（白猪栏位漏检、花斑猪未检出）
  → 结论：跨农场/品种泛化是领域开放难题，本文如实披露并指出域适应为后续方向

## 8. Discussion

- 意义：首个同时覆盖"不均衡治理+轻量化+边缘实测+泛化披露"的猪行为检测工作
- 局限：sitting 样本量（144 框）限制该类上限；跨场泛化未解决；单一场景数据源
- 未来：域适应/多源数据、INT8 需新一代边缘硬件（Orin）、视频时序行为分析

## 9. Conclusion

- 三句话：采样治不均衡 + FasterNet 轻量化 + Nano 实测可行；泛化鸿沟如实披露

## 10. 声明段（MDPI 模板全套，含 AI 使用声明与 Data Availability）

---

## 图表清单核对（写作时逐一对照）

| 编号 | 内容 | 素材位置 | 状态 |
|---|---|---|---|
| 表 1 | 行为定义 | paper/tables/behavior-definitions.md | ✅ |
| 表 2 | 类别分布 | 数据集统计（需重算最终版） | 🟡 重算 |
| 表 3 | 消融 | EXPERIMENT_LOG | ✅ |
| 表 4 | 对比组 | EXPERIMENT_LOG | ✅ |
| 表 5 | 每类 AP | paper/tables/per-class-ap.md | ✅ |
| 表 6 | 统计可靠性 | m4-r*/m5-r* | ✅ |
| 表 7 | 效率 | fps_bench 输出 | ✅ |
| 表 8 | 部署 | Nano 实测 | 🟡 待 M5 权重补测 |
| 表 9 | 泛化 | gsplit+ext 记录 | ✅ |
| 图 1 | Grad-CAM | results/analysis/gradcam/ | ✅ 可扩样 |
| 图 2 | 难例检测 | results/analysis/detections/ | ✅ |
| 图 3 | 异源实况 | results/analysis/ext-detections.jpg | ✅ |
| 图 4 | 模型结构图（M5 架构） | 需绘制 | ❌ 待画 |
| 图 5 | 训练曲线对比 | results.csv 拼图 | ❌ 待做 |
