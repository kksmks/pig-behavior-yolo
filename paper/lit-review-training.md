# 训练方法文献调研笔记（2026-07-25）

来源：WFE-YOLO 全文（INMATEH 78(1), 2026，猪行为检测最直接对手）+ 类别不均衡综述（arXiv 2403.07113）等。

## 核心结论

1. **训练超参不改**：WFE-YOLO 全套超参 = ultralytics 默认值（lr0=0.01, mom=0.937, wd=0.0005,
   HSV 0.015/0.7/0.4, translate 0.1, scale 0.5, fliplr 0.5, mosaic 1.0, warmup 3 ep）。
   收益来自模块与数据分布，不调参。→ 我方维持默认协议，冻结此项。

2. **WFE-YOLO 三件套**（其数据集 30,197 张自采，5 类：Stand/Lie/Eat/Drink/Bite，Drink 仅 776 与 we 同病）：
   - YW-Dataset：类别频率倒数 → 图像级加权随机采样（只动数据加载，不碰模型/损失）
   - FCGB：PConv + CGLU 替换 C3k2 内部 Bottleneck（内嵌式，保通道流）
   - EDH 紧凑检测头：参数 2.58M→1.96M(-24%)、GFLOPs 6.3→4.4(-30%)、mAP@50 0.8233（自家大数据集，不可与我们对标数值）

3. **类别不均衡治理路线**（综述 arXiv 2403.07113 基准）：采样法（class-aware / repeat-factor）与
   损失加权、增强（mosaic/mixup/copy-paste）各有胜负；采样法实现最简且不引入训练不稳定。

## 据此采纳（路线图 v2）

| 项 | 内容 | 状态 |
|---|---|---|
| M3 | FasterNet 主干（适配器式） | 训练中 |
| M4 | **类别加权采样**（仿 YW-Dataset，模型无关） | 下一开发项 |
| M3.1 | FCGB 式 C3k2 内嵌 PConv（选做） | 视 M3 结果 |
| M5 | 紧凑检测头（EDH 式，效率主战场） | M4 后 |
| 评测 | 每类 AP 表突出低频类；终评 +TTA | 待做 |
| 超参 | ultralytics 默认，冻结 | ✅ |
