# AutoDL 训练手册（M2 及后续实验）

## 一次性准备（约 10 分钟，花费 ≈ 0.2 元）

1. 注册 [AutoDL](https://www.autodl.com/)，充值 **10 元**（够跑 3+ 轮）
2. 控制台 → **容器实例** → **租用新实例**：
   - GPU：**RTX 3090（24G）按量计费**（约 1.3 元/h）
   - 镜像：**PyTorch 2.x**（任意近期版本，如 PyTorch 2.1 + CUDA 12.1）
   - **先开"无卡模式"**（约 0.1 元/h）——传数据阶段不用 GPU，省钱
3. 开机后点 **JupyterLab** 进入网页界面，上传到 `/root/autodl-tmp/`：
   - `dataset.zip`（379MB，在 `E:\pig-behavior-yolo\data\`，已下好）
   - `setup.sh`、`m2_train.py`（在 `E:\pig-behavior-yolo\autodl\`）
4. JupyterLab 里开个 Terminal，执行：
   ```bash
   cd /root/autodl-tmp
   bash setup.sh        # 解压数据 + 装 ultralytics（清华镜像）
   python m2_train.py --dry-run   # 结构自检（约 1 分钟，应全绿）
   ```
5. 自检通过 → **关机**（选"保留数据盘"）→ 重新开机时**取消无卡模式**（带上 3090）

## 正式训练（约 1–1.5 小时，花费 ≈ 2 元）

```bash
cd /root/autodl-tmp
nohup python m2_train.py > m2.log 2>&1 &
tail -f m2.log     # 看进度；关掉网页也不影响训练
```

判读：看到 `权重迁移：成功 448 键；缺失 57 键` + `结构自检通过` 后即可离开。
**训练完立刻关机**（按量计费，忘关机会一直扣钱）。

## 取回结果

JupyterLab 里打包下载 `/root/autodl-tmp/results/m2-emar/`（或整个 results 目录），
解压到本地 `E:\pig-behavior-yolo\results\`，然后叫助手分析。

## 备注

- 数据盘独立于实例：换实例、关机都不丢数据，dataset.zip 只需传一次
- 后续实验（对照组/M3）只需换训练脚本，数据和环境都现成
- 遇坑对照：报 CUDA 错误=镜像问题换 PyTorch 版本；下载慢=pip 已走清华镜像、GitHub 慢属正常（yolo11n.pt 仅 5MB）
