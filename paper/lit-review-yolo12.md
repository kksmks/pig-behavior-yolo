# M6 文献审核：yolo12n 能否当新基座（2026-07-27）

## 核心结论：建议换，且只换"基座"不换"打法"

### 1. yolo12n 是什么（官方依据）

- 出处：[Tian et al., "YOLOv12: Attention-Centric Real-Time Object Detectors", NeurIPS 2025](https://www.arxiv.org/pdf/2502.12524.pdf)（正会接收，非野版本）
- 三大改动：**A2 区域注意力**（降复杂度保感受野）、**R-ELAN**（残差聚合稳训练）、**FlashAttention**（内存访问优化，仅加速用）
- 工程友好化：去位置编码、MLP ratio 4→1.2、线性层改 Conv+BN——**都是为部署提速的设计**

### 2. 部署可行性（我们最关心的）

- TensorRT 导出在野外已被反复验证（[TensorRT-YOLO 支持 v12](https://github.com/sunsmarterjie/yolov12/issues/22)、多篇导出实测）
- [YOLO26 论文在 Jetson Nano/Orin 上对比了 yolo12](https://arxiv.org/html/2509.25164v4)，说明边缘部署是常态
- FlashAttention 只是加速优化，**推理可回退标准算子**（reshape/softmax/matmul，TRT 原生支持）——JP4.6（TRT 8.2）需冒烟测试确认，风险可控
- 若冒烟失败：部署章退回 M5（yolo11n 基座），主线不受损

### 3. 农业圈接受度（审稿人视角）

- [GTDR-YOLOv12 杂草检测（Agronomy 2025，已被引 35）](https://www.mdpi.com/2073-4395/15/8/1824)——基于 yolo12 的农业改进论文已在发，审稿人认这个基座
- 我们实测 yolo12n test 0.6135 > yolo11n 0.5964（同体积 2.56M/6.3G）——数据层面也支持

### 4. 决策

| 方案 | 判定 | 理由 |
|---|---|---|
| **M6 = yolo12n + 加权采样** | ✅ 做（约 2 元） | 采样与架构无关，零结构改造；若增益迁移则新王登基 |
| FasterNet 改造 yolo12 | ❌ 不做 | yolo12 的收益正来自其注意力块（A2C2f），换成 PConv 是拆它的台；机制冲突 |
| 部署 | yolo12n 与 M5 双路冒烟 | 谁能上 Nano 用谁 |

判决线（预登记）：M6 test **≥0.61** 新王；0.60–0.61 与 M4 并列按故事选；<0.60 采样未迁移，冠军留 M4/M5。
