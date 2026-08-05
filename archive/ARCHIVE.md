# archive/ —— 废案归档

规则：否决的实验产物移到这里，**不删**（失败也是数据，论文"模块选型"可能引用）。
每批归档在下方登记表加一行；不同批次建子文件夹 `archive/YYYY-MM-DD/` 区分。

## 归档登记

| 文件 | 归档时间 | 原因 |
|---|---|---|
| colab_m2_emar.ipynb | 2026-07-25 21:35 | M2 废案：EMAR残差@P3，终局 0.4988（-7.2）否决；注意力路线整体关闭 |
| yolo11-emar-n.yaml | 2026-07-25 21:35 | 同上，M2 模型配置 |
| m2_train.py | 2026-07-25 21:35 | 同上，AutoDL 版 M2 训练脚本（AutoDL 实例上副本已无用） |
| colab_m1_ema.ipynb | 2026-07-25 17:00 | M1 废案：EMA@主干末端，终局 -2.95 否决（详见 results/EXPERIMENT_LOG.md） |
| yolo11-ema-n.yaml | 2026-07-25 17:00 | 同上，M1 模型配置 |
| colab_m1p_ema_neck.ipynb | 2026-07-25 17:00 | M1' 废案：EMA@颈部P3，epoch37 叫停否决（落后 M1 同期 8 点） |
| yolo11-ema-neck-n.yaml | 2026-07-25 17:00 | 同上，M1' 模型配置 |
| colab_single_cell.py | 2026-07-25 17:00 | Colab 上传问题的临时备用方案，笔记本直连后过时 |
| kaggle_baseline.ipynb | 2026-07-25 17:00 | Kaggle 路线弃用（+86 手机验证失败），训练路线定为 Colab |

注：results/m1-ema/ 保留原位不归档——其中的曲线和混淆矩阵是论文素材。
