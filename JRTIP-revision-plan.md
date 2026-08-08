# JRTIP 投稿改进工作执行计划（v2）

> 创建：2026-08-07 ｜ v2 更新：2026-08-07 傍晚（今日已完成项见 ✅）
> 目标期刊：Journal of Real-Time Image Processing (Springer)
> 当前稿件：`paper\JRTIP-paper-v5.docx` + `paper\Supplementary_Material_v5.docx`（**v4 原件未动，投稿前请通读 v5**）
> 总体结论：**不需要补大实验；文献时效性与统计完备性已补齐大半，剩余唯一实质实验 = baseline 三种子。**

---

## 今日已完成（2026-08-07）

- ✅ **差距评估**：基于 scholar 三组检索（结果存 Kimi 工作区 CSV），确认新颖性风险点与必引文献
- ✅ **E3 小实验**：M5 每类 AP 本地 CPU 官方通道补测（`scripts/eval_m5_perclass.py`）
  - val active 缺失格 = **0.452**；val 0.5611 / test 0.5933 与云端 0.5608/0.5932 逐格核对偏差 ≤0.003
  - test 每类 AP 全新补齐（active 0.533 / sitting 0.568 / fight 0.849 / nose-to-nose 0.749…）
  - 教训已记录：predict+复刻 AP 因 NMS IoU 差异（0.7 vs 官方 0.6）偏低 ~3 点，勿用
- ✅ **P1 文献补强（已写入 v5）**：
  - 2.1 末补 PBR-YOLO [27]（Smart Agric. Technol. 10:100785, 2025）+ Rahman YOLO11n/TensorRT [28]（Porcine Health Manag. 2026）
  - 2.2 末补 IRFS [29]（arXiv:2305.08069）+ Crasto 诊断 [30]（arXiv:2403.07113，单作者已核实）
  - 2.3 末补 JRTIP 本刊 FasterNet 先例 [31,32]（21(2):49 / 21(4):122）+ 剪枝蒸馏路线 [33]（Animals 15(11):1563）
  - Discussion 首段末补与相邻路线对比段；4.4 补 Table S2 指引句；关键词 8→6
- ✅ **补充材料 v5**：Table S1 补 M5 active 0.452；新增 Table S2（test 每类 AP，Baseline/M4/M5）
- ✅ **E1 预备**：`autodl/baseline_3seeds.py` 已备并本地干跑通过（协议与 baseline_train.py 一致，seed 0/1/2，命名 baseline-r0/r1/r2）
- ✅ 数据记录同步：`paper/tables/per-class-ap.md`、`LOG.md`

## 确认无需做的事（相比 v1 计划的修正）

- ~~表/图编号重排~~ → v4 正式稿已由 finalize_v4.py 修复（Table 1–7 / Fig. 1–8 连续），此前评估基于的是 v4-partial 半成品
- ~~M3+ warm-restart 补行~~ → Table 3 中 M3 的 0.5691 本身就是续训后数字，数据已在
- ~~GitHub 仓库~~ → 已上线（github.com/kksmks/pig-behavior-yolo）
- 时序平滑 → 已实测否决并写入 Limitations

---

## 剩余待办（按优先级）

### P1 🔴 baseline 三种子训练（唯一实质实验，GPU 约 3×1.5h，AutoDL 约 6 元）
```bash
# AutoDL 上（数据集就位后）：
nohup python baseline_3seeds.py > baseline-3seeds.log 2>&1 &
```
- 跑完自动产出 `results/baseline-3seeds-summary.json`（val/test mean±std）
- **论文更新点**：Table 3 脚注与 4.5 节 "versus a single-run baseline of 0.5964" → 改为三种子均值±std 表述；摘要 "statistically indistinguishable" 措辞按新数字复核
- 预期判决：M4 test 均值（0.5987）vs 基线均值——若基线均值 ≈0.596，叙事不变；若基线均值 ≥0.599，M4 的"总分增益"框架进一步弱化（仍靠稀有类+召回叙事，不影响主结论）

### P2 🟡 v5 通读与审稿团复审
- [ ] 用户通读 JRTIP-paper-v5.docx 五处新增段落（2.1/2.2/2.3/4.4/Discussion）+ Supplementary_Material_v5.docx
- [ ] 过 REVIEW_BOARD 三角评审新增段落（重点 R1：与 PBR-YOLO 的差异化表述是否站稳；R3：畜牧角度表述）
- [ ] 若通过：v5 转正为投稿稿，submission-package 同步换新（manuscript + supplementary 两个文件）

### P3 🟡 作者侧占位（只能用户/导师填）
- [ ] 作者/单位/邮箱（Title 页）
- [ ] Author Contributions（CRediT）+ Funding
- [ ] Data Availability 里的 GitHub 链接核对（仓库已上线，确认文中 URL 正确）

### P4 🟡 第 5 节测量方法学一句话（E4）
- [ ] 用户确认：功耗用什么测的（tegrastats？jtop？功率计？）、FPS 是否 trtexec sustained 均值
- 补 2 句进第 5 节（Table 8 已删，数据在正文，方法学跟在部署段即可）

### P5 🟢 投稿前例行
- [ ] Springer 排版后实测页数 ≤12（预案：Fig.3→补充 / Table 1 实例数列→正文）
- [ ] Cover Letter 日期、图题逐字复制检查

---

## 审稿预案（备好不主动做）

1. **"为什么不和 PBR-YOLO 比？"** → 已在 2.1/Discussion 主动引用并差异化；数据集不同（仔猪 8 行为 vs 群养育肥猪 10 行为）、对方未开源、我方统一协议已覆盖三代 YOLO+RT-DETR+YOLOv12。若审稿人坚持且代码可得，预留 2–3 天 GPU 补一行同协议对比。
2. **"为什么老 Nano / 没 INT8？"** → 第 5 节已有完整论述（Maxwell 无 INT8 单元、TRT 8.2 校准失败、5W 成本定位）。
3. **跨农场 0.03–0.07 是否说明方法无效？** → 全员崩溃的领域级问题，本文主动量化；M5 域外高 P 低 R 说明预测变保守而非随机。

## 投前最终检查清单
- [ ] 摘要/正文/表格数字三方一致（0.526→0.639、+2.1 recall、−4.4%、117.6 FPS、19.7/33.3 FPS）
- [ ] baseline 三种子统计已替换 4.5 节单次基线表述
- [ ] 参考文献 [1]–[33] 无缺引/跳号（v5 新增 [27]–[33] 均已在正文出现 ≥2 次）
- [ ] 占位符清零（作者/Funding/Contributions/GitHub URL）
- [ ] 页数 ≤12；图分辨率 ≥300dpi
- [ ] 关键词 6 个 ✓（v5 已改）
