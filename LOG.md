# 每日操作日志

> ⚠️ **断点恢复请读根目录 `STATE.md`（总状态文件）**，本日志只记每日流水。

## 使用规则（先读）

- **每天收工前花 2 分钟记一条**：今天做了什么、改了哪些文件、卡在哪、明天干什么
- 新条目加在**最上面**（倒序，最新的最好找）
- 分工：本日志记"操作和决定"；训练指标记 `results/EXPERIMENT_LOG.md`；论文素材记 `paper/`
- 文件命名一律 `小写-连字符`，临时文件丢 `data/tmp/`（每周清空）
- 每条日志格式：

```
## YYYY-MM-DD
- 做了：……
- 文件变更：新建/修改了哪些文件
- 卡点：……（没有就写"无"）
- 明日待办：……
```

## 2026-08-08（页数实测销账：v5 = 10/12 页）

- 做了：
  - **答疑"Word 不行"**：查 JRTIP 官方投稿指南——"Word files are also accepted"，期刊同时提供 LaTeX/Word 双模板；审稿看系统编译 PDF，源文件格式不影响评审
  - **下载官方 Word 模板**（media.springer.com 直链，EIC Kehtarnavaz 签名）→ Word COM 转 docx，解析几何：Letter / T·B 17.8mm / L·R 16.5mm / 双栏 288twips / TNR 正文 10pt 行距 252 / 标题 24 / 作者 11 / 摘要 9 / 图题表题 8 / 文献 8
  - **scripts/paginate_jrtip.py 灌 v5 入双栏**：Fig.2/5 通栏 174mm、其余单栏 84mm（Fig.8 遵 08-07 决议单栏勿通栏）、连续分节符、表格栏宽 100%+8pt、run 字号剥离
  - **Word 排版引擎实测 PAGES=10**（计词 6751），导出 PDF 校验：8 图 7 表 33 文献全齐、Declarations/Online Resource 在位
  - 过程纠偏：先对 v4 测（10 页），读 STATE 发现 v5 已成现行稿（三种子+33 文献，+628 词），改源复测同为 10 页，删 v4 测量中间件，以 v5 为准
  - bio（~0.2 页）加入后仍远低于 12 页上限，超页预案废止
- 文件变更：新建 scripts/paginate_jrtip.py、paper/template/{JRTIP-WordTemplate.doc,.docx,v5-jrtip-format.docx,.pdf}；修改 STATE.md、submission-package/README.md（页数检查项打勾）
- 卡点：无
- 用户侧剩余（不变）：通读 v5 四件 → 填作者/单位/邮箱/ORCID + Funding + Author Contributions → 送导师 → 投稿

---

## 2026-08-07（傍晚：baseline 三种子跑完 + v5 基线统计写入）

- 做了：
  - **接管 AutoDL 跑 baseline 三种子**（14:57 启动，约 3.6h 跑完，scripts/cloud.py exec 通道；SFTP 的 push/pull 已确认坏掉，上传走 base64+exec、下载走 exec cat）：seed0 val 0.5729/test 0.5964、seed1 0.5835/0.6095、seed2 0.5902/0.6120 → **val 0.5822±0.0087 / test 0.6060±0.0084**；seed0 逐格复现旧单次 0.5964
  - **统计结论**：M4 −0.007 在基线 1σ 内；M5 −0.016 ≈ 2SE（p≈0.09 不显著）→ 论文叙事不变（不优于基线、胜在弱类再分配+召回+效率），但"单次基线 0.5964"的旧锚点全部换成三种子口径
  - **v5 写入**：scripts/apply_baseline_3seeds.py 锚点替换 6 处全中——摘要 (0.590±0.009 vs 三种子基线 0.606±0.008)、Table 3 脚注 (three-seed baseline 0.6060±0.0084)、4.5 节四句重写（含 seed0 复现句、M5 p≈0.09、M4 1σ 内）
  - **JRTIP 官方投稿指南合规检查**（springer.com/journal/11554/submission-guidelines 逐条比对）：新增修复 6 处（scripts/apply_v5_jrtip.py 全中）——摘要 mAP50/FPS 首现展开（211 词仍 ≤250）、Fig.5/8 题注尾句号删除（Springer 图题规则）、Declarations→Statements and Declarations、SI 两处提及改 "Online Resource 1"、补充材料头部加期刊名+作者占位行。已合规：关键词 6 个、文献 33 条全被引无遗漏、图表顺序引用、IRB/动物福利声明、Data Availability（含 GitHub 代码）、AI-Assisted 声明（符合 Springer LLM 政策）、Cover Letter real-time 论述。**🔴 用户必办=作者/单位/通讯邮箱/ORCID/Funding/Author Contributions 占位**；🟡 图有效分辨率按组合图 600dpi 复核（README 记最弱 330dpi）、SI 投稿时转 PDF 命名 ESM_1.pdf、投稿界面需单独填 Author Contributions+Competing Interests
  - 结果落账：results/baseline-r0/r1/r2/metrics.json + baseline-3seeds-summary.json；EXPERIMENT_LOG.md 加三行
  - **审稿团报告 #7（v5 改动段落专项）**：R1 抓到 4 个 🔴/措辞问题全部当场修复（scripts/apply_v5_review7.py，4 处全中）——①摘要 "statistically indistinguishable"→"comparable"（n=3 t 检验不显著≠等效）②2.1 对 PBR-YOLO 的缺失性声明无法确证（Elsevier 全文不可得）→ 随机切分声明只挂 Rahman（其全文自认 within-facility）+ "to our knowledge" 对冲 ③Discussion "show that...do not transfer"（n=2 因果过强）→"suggest...may not transfer" ④S2 caption 补 "single-run values (seed 0)" 防与 4.5 节三种子均值误读矛盾。4.5 节新统计数字复核无误（SE 0.0069/t 2.25/p≈0.088）。R3 领域核查发现 [33] Luo 与 [27] PBR-YOLO 同课题组且 [33] 确用增强做类平衡——我方声明范围未波及，列入备答信素材
  - **中文版同步 v5**：新建 build_paper_docx_zh_v5.py / build_supplementary_zh_v5.py（v4 脚本未动）→ 中文成稿-v5.docx + 补充材料-v5.docx，英文 v5 全部改动逐节移植（三种子基线口径/三段文献补强/讨论对比段/关键词 6/文献 33/表 S2/审稿团措辞），结构校验 14 项锚点全过
  - **submission-package 换 v5 全套**：主稿/SI 换 v5（v4 件移除）；Word COM 转 ESM_1.pdf（pypdf 验证含 S1/S2/0.452）；图分辨率复核后 Fig1/3/4/7 提标重出（build_figures.py dpi→430 + upgrade_fig3_hidpi.py 重绘 Fig3 并去图内标题——原图违反 Springer 规则；M5 改虚线灰度可辨），重出后 771–907dpi；Fig8 定为单栏排版（362dpi 达标，勿通栏）；README 重写为"只差填作者信息"状态
- 文件变更：新建 scripts/apply_baseline_3seeds.py、apply_v5_review7.py、apply_v5_jrtip.py、build_paper_docx_zh_v5.py、build_supplementary_zh_v5.py、upgrade_fig3_hidpi.py、results/baseline-*/metrics.json、results/baseline-3seeds-summary.json、submission-package/supplementary/ESM_1.pdf；修改 paper/JRTIP-paper-v5.docx（6+4+6 处）、Supplementary_Material_v5.docx（S2 caption+头部行）、results/EXPERIMENT_LOG.md、paper/REVIEW_BOARD.md（报告 #7）、scripts/build_figures.py（dpi 430）、submission-package/README.md（全量重写）；产出 paper/猪行为检测-中文成稿-v5.docx、猪行为检测-补充材料-v5.docx；submission-package 主稿/SI/图 4 张换 v5
- 卡点：无
- 明日待办：① **用户去 AutoDL 控制台关机**（约 2 元/h，只能本人操作）② 用户通读 v5 四件 → 填作者/单位/邮箱/ORCID + Funding + Author Contributions → 投稿 ③ 确认功耗测量工具名（plan P4）④ 排版实测页数（投稿排版后）⑤ 投稿前可选：全文扫 [31][32] 核对 "do not discuss" 声明

---

## 2026-08-07（文献补强 v5 + M5 每类 AP 补测）

- 做了：
  - **JRTIP 投稿差距评估**（应用户要求，基于 scholar 检索）：结论=不需大实验，需补文献时效性+统计完备性；全文见根目录 JRTIP-revision-plan.md
  - **M5 每类 AP 本地补测**：用 scripts/eval_m5_perclass.py（注册 FasterBlock → model.val 官方通道，CPU）补齐 val active 缺失格 **0.452**，并新测 test 每类 AP（active 0.533 / sitting 0.568 / fight 0.849…）；val 0.5611、test 0.5933 与云端 0.5608/0.5932 逐格核对偏差 ≤0.003，协议验证通过
  - **v5 双件产出**：scripts/apply_v5_edits.py → paper/JRTIP-paper-v5.docx（2.1/2.2/2.3 末尾各补一段、Discussion 补对比段、4.4 补 Table S2 指引句、关键词 8→6、参考文献 [27]–[33] 共 7 条均已核实：PBR-YOLO/Rahman/IRFS/Crasto/Guo-JRTIP/YOLO-FGD-JRTIP/Luo 剪枝蒸馏）+ paper/Supplementary_Material_v5.docx（S1 补 active 0.452、新增 Table S2 测试集每类 AP）；表顺序 bug 由 scripts/fix_supp_v5_order.py 修复
  - baseline 三种子训练脚本备好（autodl/baseline_3seeds.py），待 GPU
- 文件变更：新建 scripts/eval_m5_perclass.py、apply_v5_edits.py、fix_supp_v5_order.py、autodl/baseline_3seeds.py、JRTIP-revision-plan.md；修改 paper/tables/per-class-ap.md；产出 paper/JRTIP-paper-v5.docx、Supplementary_Material_v5.docx（**v4 原件未动**）
- 卡点：无（v5 待用户通读 + 审稿团过一遍新增段落）
- 明日待办：① AutoDL 跑 baseline_3seeds.py（约 3×1.5h）→ 更新 4.5 节统计 ② 用户通读 v5 双件 ③ 确认功耗测量工具名（补第 5 节方法学一句话）④ 排版实测页数

---

## 2026-08-06（凌晨④：旧 Roboflow key 吊销销账）

- 做了：用户在 Roboflow Settings→API Keys 删除 Key 1（hMQC…，泄露那把），截图确认列表只剩 Key 2；Key 2（NRyn…）经全仓 grep 确认零出现、从未暴露，保留。STATE.md 快照/待办/更新记录三处销账，submission-package/README.md 检查项打勾
- 文件变更：STATE.md、submission-package/README.md
- 卡点：无
- 用户侧剩余：通读中英 v4 → 送导师；投稿排版后实测英文页数 ≤12

---

## 2026-08-06（凌晨③：投稿材料包预组装）

- 做了：
  - **submission-package/ 组装完成**：figures/（Fig1–Fig8 按论文图号规范命名，从 results/analysis 与 results/m4-wsample 收齐，含两张拼图成品）+ manuscript/JRTIP-paper-v4.docx + supplementary/Supplementary_Material.docx + cover-letter/（docx+md 双版本）+ README.md
  - README 内容：目录结构、图号↔源文件对照表（源文件历史编号 fig4–fig10 与论文图号不一致的防错提醒）、投稿前检查清单 5 项、分辨率说明（全部 ≥290dpi 等效，满足 Springer 线图要求）
- 文件变更：新建 submission-package/（14 文件，~6MB）；STATE.md 快照+更新记录
- 卡点：无
- 今日待办（用户侧）：不变——通读中英 v4 → 送导师；**吊销旧 Roboflow key**；投稿排版后实测英文页数 ≤12

---

## 2026-08-06（凌晨②：GitHub 上线 + URL 回填）

- 做了：
  - **GitHub 仓库上线**：用户网页建仓 kksmks/pig-behavior-yolo（Public、无初始化文件）；重写 4 个提交作者为 kksmks <kksmks@users.noreply.github.com>（rebase --root --exec reset-author）；连远程推 main 成功（直连无需代理、凭据管理器无弹窗）
  - **4 处 URL 占位回填**（https://github.com/kksmks/pig-behavior-yolo）：JRTIP-paper-v4.docx 数据可用性声明、cover-letter-jrtip.{md,docx}、build_paper_docx_zh.py → 重建中文 v4；中文声明措辞"将于投稿前公开"→"已在...公开"
- 文件变更：paper/JRTIP-paper-v4.docx、cover-letter-jrtip.{md,docx}、build_paper_docx_zh.py、猪行为检测-中文成稿-v4.docx
- 卡点：无
- 今日待办（用户侧）：通读中英 v4 → 送导师；吊销旧 Roboflow key；投稿排版后实测英文页数 ≤12

---

## 2026-08-06（凌晨：中文版过审封账）

- 做了：
  - **中文 v4 过模拟审稿团**：自动扫描（旧编号残留 0 / 35 项中英关键数字段落+单元格比对全一致 / 过度声明仅 SOTA 存于文献标题）+ 三审 → REVIEW_BOARD 报告#6-补 收录
  - 结论：🔴 必修 0 项；🟡 知悉 2 项（± 号空格风格中英不一但各自自洽；作者/单位/GitHub 占位待填）；**中文 v4 与英文 v4 同口径、无雷，可直接送导师评审**
- 文件变更：paper/REVIEW_BOARD.md（报告#6-补）
- 卡点：无
- 今日待办（用户侧）：通读双版 → 送导师；吊销旧 Roboflow key；GitHub push 后回填 URL；排版后实测英文页数

---

## 2026-08-05（深夜②：中文版同步 v4 口径）

- 做了：
  - **中文版成稿同步 v4**：scripts/build_paper_docx_zh.py 全量重写至 v4 口径 → paper/猪行为检测-中文成稿-v4.docx（8 图 7 表）；新建 scripts/build_supplementary_zh.py → paper/猪行为检测-补充材料-v4.docx（表 S1 每类 AP）
  - 拼图永久资产落位：results/analysis/fig5-gradcam-hardcase.jpg（左右）、fig8-generalization-ext.png（上下）——中英两版共用
  - 同步点与英文版逐项对齐：表 1+2 合并四列（训练图像数本地实测）、部署表化正文（四行全保留）、每类 AP 移补充、效率→表 5/压力→表 6/跨数据集→表 7、图 5a/b 与图 8a/b 引用、Table 2 正文引用补入 3.3 节末、Limitations 时序句改实测阴性结果
  - 结构核查通过（脚本）：8 图段/7 表、图题注 1-8 顺、表/图引用均 ≥2（题注+正文）、表 S1 引用 1 处
  - git 两次提交：8823a33（仓库初始化）→ faada57（中文 v4 同步）
- 文件变更：scripts/build_paper_docx_zh.py（重写）、scripts/build_supplementary_zh.py（新建）、paper/猪行为检测-中文成稿-v4.docx、paper/猪行为检测-补充材料-v4.docx、results/analysis/fig5-gradcam-hardcase.jpg、fig8-generalization-ext.png
- 卡点：无
- 明日待办：
  - 用户通读中英 v4 双版（重点拼图观感）→ 中文版给导师评审
  - 吊销旧 Roboflow key 换新；GitHub 建仓 push（faada57）后回填 URL 占位
  - 投稿排版后实测英文版页数 ≤12（预案 Fig.3→补充 / Table 2→正文）

---

## 2026-08-05（深夜：v4 定稿 + 投稿冲刺四件套）

- 做了（第二波，接"时序平滑判决日"）：
  - **v4 定稿完成**：scripts/finalize_v4.py 一次性完成 manual-todo 全部手动项——Table 1+2 合并（定义+意义/实例/训练图像四列，训练图像数本地标签实测 sitting104/investigating1714 复核）、部署表删除数据写入第5节、每类 AP 表移 Supplementary_Material.docx（Table S1）、效率→Table 5/压力→Table 6/跨数据集→Table 7、Fig.5 Grad-CAM+难例左右拼图、Fig.8 泛化柱状+异源实况上下拼图（限高7.2in）；脚本审计 Fig.1-8/Table 1-7 题注唯一+引用≥1 无跳号；发现并修复编号脚本残留混乱（Table 2×2/4×3/6×2、Fig 4/6/7/8 双黄蛋）与 Table 2 正文零引用
  - **时序平滑谎言清除**：Limitations 原句"temporal smoothing would likely improve"与当日实测判决矛盾，已改为实测阴性结果句（稀疏帧 IoU 跟踪失效、密集帧部署场景仍可期）
  - **审稿团终审报告#6 收录**（REVIEW_BOARD.md）：报告#5 篇幅🔴清零；残余风险=页数贴上限（~6.4k词+8图7表估 11-12.5 页，排版后实测，预案 Fig.3→补充/Table 2→正文）
  - **Cover Letter 双版本**（paper/cover-letter-jrtip.md + .docx）：JRTIP real-time 实质论述（延迟-分辨率权衡/INT8 缺失/融合抹平三现实）+ 主动披露切分策略与两级泛化 + 补充材料声明；未点名竞品
  - **GitHub 仓库整理**：git init + 首次提交（8823a33，74 文件）；**7 个文件明文 Roboflow API key 全部抹除**（notebooks×2 + archive×5，JSON 校验通过，建议用户吊销旧 key 换新的）；.gitignore 补 data/ext-eval/、data/tmp/、备份 docx；requirements.txt 重写去重补全（torch/python-docx/matplotlib/paramiko 等）
- 文件变更：paper/JRTIP-paper-v4.docx（定稿）、paper/Supplementary_Material.docx、paper/cover-letter-jrtip.{md,docx}、scripts/finalize_v4.py、REVIEW_BOARD.md（报告#6）、.gitignore、requirements.txt、7 个 key 文件、.git/
- 卡点：无
- 明日待办：
  - 用户通读 v4 定稿 docx（重点 Fig.5/Fig.8 拼图观感）→ 投稿排版后实测页数（≤12）
  - 用户吊销旧 Roboflow key 并生成新 key（旧 key 曾明文存于 7 文件）
  - GitHub 建仓 push（Data Availability 声明里的 [GitHub URL] 占位待填）
  - 中文版同步 v4 口径 → 导师评审

---

## 2026-08-05（时序平滑判决日）

- 做了：
  - 时序平滑模块开发闭环：temporal_smooth.py / run_temporal_inference.py / autodl/temporal_inference_full.py；M5 全量 val（1123 帧/15 序列/3132 框）推理+平滑完成
  - **补建缺失的真 mAP 评估**（scripts/eval_temporal_map.py，复刻 ultralytics 官方协议 box_iou+ap_per_class、IoU 0.5-0.95 十阈值、101 点插值）——原 eval 子命令只有类别分布统计，判不了模块生死
  - **判决：时序平滑否决**。w3v2 −2.66 / w5v4 −1.27 / w3v3 零效——稀疏抽帧（帧号差 50~580）下 IoU 跟踪失效，投票污染正确标签；该技巧只适用于密集连续帧部署场景，论文不得主张精度收益（诚实记录，同 M1/M1' 先例）
  - **揪出并修复类名映射 bug**：run_temporal_inference.py 的 CLS_NAMES 误用 Roboflow 展示序，与 data.yaml 类序（字母序）不符 → compare 报告类名整体错标（计数正确）；已修复并重生成 compare.txt
  - v4 成稿压缩推进：JRTIP-paper-v4.docx / v4-partial.docx 生成（11图10表→≤8图≤6表，JRTIP 12 页上限）；auto_ref_numbering.py / fix_table_numbers.py；剩余手动 Word 操作清单见 paper/v4-manual-todo.txt（拼图、并表、连环改号）
- 文件变更：新建 scripts/eval_temporal_map.py；修改 run_temporal_inference.py（类序修复）；results/temporal/（predictions_full/smoothed_full/smoothed_w3v3/smoothed_w5v4/compare.txt/map_eval*.txt）；EXPERIMENT_LOG 补两行
- 卡点：无
- 明日待办：
  - 用户按 v4-manual-todo.txt 在 Word 里完成手动操作（拼图/并表/Table 3-5 改号）→ 另存 v4 正式版
  - v4 定稿后过模拟审稿团终审（REVIEW_BOARD 报告#6）
  - GitHub 代码仓整理（Data Availability 用，含 eval_temporal_map.py）

---

## 2026-08-03（深夜封账）

- 做了：
  - 外部验证全部落账（M5 外集 0.0361，P9 泛化鸿沟证据链完整）
  - 论文详细提纲（outline.md）→ v2 双稿（draft-v2-en JRTIP 版 + draft-v2-zh 中文评审版）→ **带图成稿 JRTIP-paper-v2.docx（五图全嵌）**
  - 选刊定案：JRTIP 主推（SCIE Q2，Springer 订阅制免费，IF 4.9）；冲刺序 EcoInform → JRTIP → INMATEH 保底
  - 倍率消融（斧 3）完成：cap4=cap5（本数据集最大倍率只用 4），cap3 略降——敏感性分析素材到手
  - 图 4 结构图、图 5 训练曲线绘制完成；写作规范手册（writing-guide.md）成稿
- 文件变更：paper/ 下 outline、draft-v2-en/zh、JRTIP-paper-v2.docx、journal-choice、Q3-plan、writing-guide；m4_train.py 加 --max-factor
- 卡点：无
- 明日待办：
  - 用户 Nano 上电 → 我做 M5 权重正式部署实测（部署表最后一块）
  - 用户通读 docx + 中文版找导师
  - 模拟审稿团对成稿做终审
  - 整理 GitHub 代码仓（Data Availability 用）

## 2026-07-27

- 做了：
  - M5 全自动训练+巡查+判决闭环跑通：test 0.5932，**里程碑 40% 达成，最终模型候选锁定**
  - M3 test 补测（本地 CPU）0.5691；四方表齐全
  - 建立 PROGRESS.md 里程碑体系（20 格）
  - 云端 SSH 直连（scripts/cloud.py）实现远程全自动训练
- 文件变更：results/m5-fastnet-wsample/、PROGRESS.md、scripts/cloud.py、autodl/m5_train.py
- 卡点：无
- 明日（7-27 白天）待办：
  1. 【第 9 格 45%】对照实验组：我先做文献审核定对照名单（rtdetr-l/yolov8n/yolo12n），备好脚本后叫用户开机，全自动连跑
  2. 用户顺手：Nano 查 `cat /etc/nv_tegra_release`；挂代理确认 aimagelab 数据集可下载
  3. 我（不占用户）：整理效率指标表（55% 预备）；评估 M4' 微调必要性

## 2026-07-25（晚间封账）

- 做了（全天汇总）：
  - M1' 中期叫停否决（0.338@37）→ 根因定性"乘法门控污染预训练特征"→ M2 残差版仍否决（0.4988）→ **注意力路线正式关闭**（三轮全负）
  - 交付前审核三关规则建立（用户要求）+ 本地 CPU 验证环境（torch2.1.1+ultralytics8.4.105）
  - AutoDL 打通（~2 元/轮）；代理 127.0.0.1:7897 可用，数据集 dataset.zip 已在本机
  - Colab 额度耗尽事件 → 笔记本升级 Drive 持久化版（备用）
  - 废案归档 archive/；问题记录 paper/problem-log.md（P1-P6）
  - 训练方法调研（WFE-YOLO 全文）→ 路线图 v2：超参冻结默认、M4=类别加权采样、M5=紧凑检测头
  - **M3 开发完成**（FasterNet v2，两轮本地迭代枪毙增肥版）：参数-5.6%/FLOPs-0.3%/迁移316键，m3_train.py dry-run 通过
- 文件变更：archive/、paper/（problem-log、lit-review-training、REVIEW_CHECKLIST）、autodl/（README、setup.sh、m3_train.py）、STATE.md 持续更新
- 卡点：无（M3 待用户实跑）
- 明日待办：见下一条"明日清单"

## 2026-07-25（下午）

- 做了：
  - 项目整体迁移 C:\Users\1 → **E:\pig-behavior-yolo**（69 文件校验一致，原目录已删，无绝对路径需改）
  - 新建 notebooks/colab_compare.ipynb（参数化对照实验：rtdetr-l/yolov8n/yolo12n，只改 MODEL/BATCH 两变量）
  - NEAU 数据集邮件无回复（已 1 周，按预案降级为备选）→ 制定可信度增强四路线（见会话）：
    A 跨数据集外部验证（首选 Mendeley Zhang2025 猪行为数据集，DOI 待核）；B aimagelab/ Qi 13 类数据集申请；C 自建小测试集（预标注+人工修）；D 数据文档化 Dataset Card + 泄漏检查报告 + 3 次重复 + 开源复现包
- 文件变更：项目迁移至 E 盘；新建 colab_compare.ipynb
- 卡点：无
- 明日待办：
  - 我核实 Mendeley 数据集 DOI 与 Qi(arXiv 2503.09378) 数据链接
  - 用户跑 colab_m1p_ema_neck.ipynb（主线）；有空填 aimagelab 数据集申请表
  - 仍未办：Nano JetPack 版本

## 2026-07-25

- 做了：
  - M1（EMA@主干末端）终局判决：**否决**，mAP50 54.11% vs 基线 57.06%（-2.95）
  - 诊断：颈部/头部未吃到预训练权重（索引偏移）+ EMA 与 C2PSA 自注意力堆叠
  - 重要发现：M1 的 eat 类 0.38→0.77、lying 0.67→0.89，证明注意力方向有效、错在位置
  - 按评审标准出正式评估（7 维度，见会话与 paper/REVIEW_CHECKLIST.md）
  - 建好 M1' 修正版：EMA 挪颈部 P3 + 预训练权重重映射 + 近重复帧泄漏检查格
  - 用户约定：桌面"跑的结果"文件夹统一存放结果压缩包（命名 results-YY.M.DD.zip）
- 文件变更：新建 configs/yolo11-ema-neck-n.yaml、notebooks/colab_m1p_ema_neck.ipynb、paper/REVIEW_CHECKLIST.md；更新 EXPERIMENT_LOG.md
- 卡点：无
- 明日待办：
  - 用户跑 colab_m1p_ema_neck.ipynb（T4，约 2h），关注第 4 格"缺失键应只有 EMA"与泄漏检查数字
  - 排队对照实验：yolov8n、rtdetr-l（改基线笔记本模型名即可）
  - 仍未办：NEAU 邮件、Nano JetPack 版本

## 2026-07-19

- 做了：
  - 用户在 Colab 完成 YOLOv11n 基线训练（100 轮），results.zip 已解压入 `results/baseline/`
  - 基线：mAP50 57.06% / mAP50-95 41.69% / P 51.3% / R 58.7%，已登记 EXPERIMENT_LOG
  - 混淆矩阵分析确定改进靶点：eat/drink 漏检（槽区小目标）、standing↔sitting、walk↔active 混淆；fight 类最强（0.83）
  - 质检图目检通过：标注可用；图像命名证实为视频抽帧
- 文件变更：results/baseline/（权重、曲线、混淆矩阵、metrics.json、qc_samples.png）
- 卡点：无
- 明日待办：
  - 用户 Colab 跑 RT-DETR-R18 对照基线（训练格改一行，见会话）
  - 我准备第一个改进模块代码（EMA 注意力）
  - 仍未办：NEAU 邮件、Nano JetPack 版本（`cat /etc/nv_tegra_release`）

## 2026-07-18

- 做了：
  - 确定方向：群养猪多行为轻量检测 + Jetson Nano 部署（目标 Q3/Q4，Animals/Sensors/AgriEngineering/INMATEH）
  - 创新点查新：发现 GAB-YOLO（GhostNet+Wise-IoU+边缘，采食单行为）、WFE-YOLO、Rahman(YOLO11n+TRT) 等近邻工作，据此重新定位"多行为 + Nano 实测 + 精度-效率权衡"
  - 改进菜单换血：FasterNet/StarNet、SPD-Conv/P2、EMA/iRMB、Shape-IoU、HS-FPN（避开 GAB 已占组合）
  - 搭好项目脚手架：prepare_data.py / train.py / export_deploy.py，均通过语法检查
  - prepare_data.py 增加 `--group-sep` 按视频分组切分（防相邻帧泄漏）
  - 拿到 Roboflow API key；确认数据集实情：5620 张、10 类、官方预切分、CC BY 4.0、类别不均衡（investigating 4203 框 vs sitting 144 框）
  - 本地下载失败（谷歌云存储国内不可达）→ 改为云端笔记本内下载
  - 新建本日志
- 文件变更：新建 scripts/、notebooks/、results/EXPERIMENT_LOG.md、LOG.md；修改 README.md（查新定位、Colab 流程、评测协议）
- 卡点：Colab 本地不可达（谷歌服务）→ 用户可科学上网；Kaggle 手机验证失败（+86 收不到验证码、Start Verification 按钮无响应）→ 最终定 Colab 路线
- 进展：用户已在 Colab 上传 colab_baseline.ipynb 并开始跑基线；QC 格 glob 路径过窄报错已修复（改递归 `**`，三个笔记本文件均已同步）；新增 notebooks/colab_single_cell.py 备用
- 明日待办（顺延）：
  - 发 NEAU 数据集申请邮件（bsdai@neau.edu.cn，模板在会话记录里；2 周无回复转 Roboflow 为主）
  - 查 Jetson Nano 的 JetPack 版本：`cat /etc/nv_tegra_release`
  - 拿回 results.zip 后检查 qc_samples.png 与 metrics.json
