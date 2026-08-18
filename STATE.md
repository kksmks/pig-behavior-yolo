# PROJECT STATE —— 项目总状态（断点续传文件）

> **用途**：会话上下文丢失/压缩时，新会话先读本文件 + `LOG.md` 即可恢复全部工作状态。
> 进度里程碑见 `PROGRESS.md`（每 5% 一格，达成即记时间戳）。
>
> **更新协议（硬性规则）**：
> 1. 任何实验结果、模块判决、关键决策、环境变化发生后**当场更新**，不攒批
> 2. 每次更新做两件事：① 修改对应章节内容 ② 在文末"更新记录"加一条带时间戳的记录
> 3. 时间戳格式：`YYYY-MM-DD HH:MM`（本地时间，以 `date` 命令为准）
> 4. 更新频率宁可过度不可不足——丢状态的代价远大于多写两行
>
> 最后更新：2026-08-08 23:15

## 1. 项目一句话

本科生科研训练：**群养猪多行为轻量级检测（改进 YOLOv11n）+ Jetson Nano 边缘部署验证**，
目标 Q3/Q4 期刊（主推 JRTIP / 冲刺序 EcoInform → JRTIP → INMATEH 保底），
整体周期 4 个月到投稿。

## 2. 当前进度快照（2026-08-05）

- ✅ **实验工作全部封账**（2026-08-04）：消融阶梯（基线0.5964/M4 0.6035/M3 0.5691/M5 0.5932/M6阴性对照0.5994）+ 对照组 4 模型（yolo12n 0.6135 精度王）+ M4/M5 三次重复 + 压力测试 + 外部验证（0.036–0.067 泛化鸿沟）+ Nano 部署矩阵（19.7FPS@640 / 33.3FPS@480 / ~5W）
- ✅ 论文 v3 双版成稿（英 JRTIP-paper-v3.docx / 中 猪行为检测-中文成稿-v3.docx，全量数字审计通过）
- ✅ **v4 定稿完成**（2026-08-05）：8 图 7 表 + 补充材料 Table S1（Supplementary_Material.docx），全部图表号脚本审计无跳号；Cover Letter 双版本就绪；审稿团报告#6 通过；~~残余风险=排版后实测页数~~ **页数已实测=10/12 页（2026-08-08，v5 口径）**
- ✅ GitHub 仓库上线（https://github.com/kksmks/pig-behavior-yolo，5 提交全署名 kksmks；7 文件明文 API key 已抹除，**泄露旧 key 已于 2026-08-06 吊销**）
- ✅ **投稿材料包就绪**（2026-08-06）：submission-package/（Fig.1-8 单独上传文件 + 主稿 + 补充材料 + Cover Letter 双版本 + README 清单/检查表）；图源历史编号 fig4-fig10 ≠ 论文图号，投稿以包内 Fig1-8 命名为准
- ❌ **时序平滑模块否决**（2026-08-05）：w3v2 −2.66 / w5v4 −1.27 / w3v3 零效。稀疏抽帧下 IoU 跟踪失效；只适用于密集连续帧部署场景，论文 Limitations 已写为实测阴性结果
- ✅ **baseline 三种子封账**（2026-08-07，AutoDL 3090）：val 0.5822±0.0087 / **test 0.6060±0.0084**（seed0 逐格复现旧单次 0.5964）；M4 −0.007 在 1σ 内、M5 −0.016 ≈ 2SE（p≈0.09 不显著）→ 叙事不变，已写入 v5 摘要/Table 3 脚注/4.5 节（results/baseline-3seeds-summary.json）

## 3. 关键数据

**数据集（主）**：Roboflow pig-behavior（km-sd0ce/pig-behavior-wlvku v1）
- 5620 张 / **10 类**：nose-to-nose358, standing1812, investigating4203, eat980, active259, walk2736, drink211, sitting144, fight807, lying2485（标注框数）
- 官方预切分 train/valid/test = 3936/1123/561；已统一 resize 640；**CC BY 4.0**（引用需署名）
- 基线混淆矩阵诊断：fight 最强(0.83)；弱类 eat0.38（60%漏成背景）/drink0.53/standing0.51/sitting0.54/active0.44；walk↔active 互混 25%
- QC 目检通过（12 张抽查）；图像为视频抽帧（命名带日期帧号）→ 泄漏检查在 M1' 第3格进行，**数字待回收**
- 下载方式：笔记本内 Roboflow API（**API key 明文在各 notebook 第2格**，勿外传/上传 git）
- 本地下载不可行（谷歌存储被墙）；Colab 需挂代理；Kaggle 因 +86 手机验证失败已放弃

**对标数字**：NEAU CEA2024 同任务 mAP 80.05%（YOLOX+SlowFast 视频法，walking AP 55.76%）

## 4. 关键决策（不要再翻案）

1. 主线 YOLOv11n（Nano 部署生态最成熟），RT-DETR 只作对比模型
2. 定位："**多行为（含难检类）+ Nano 实测 + 精度-效率权衡**"，避开 GAB-YOLO（采食单行为）/Rahman（哺乳单行为）/WFE-YOLO（无部署）
3. 改进菜单：EMA/iRMB 注意力、FasterNet/StarNet 轻量主干、Shape-IoU/Powerful-IoU 损失、SPD-Conv/P2 小目标层、HS-FPN
   **禁用**（已被 GAB-YOLO 占用）：GhostNet、Wise-IoU、BiFPN
4. **M1' 判决标准（预登记）**：mAP50>58.1% 有效进消融表；56~58% 换 CBAM/SE 最后一试；<56% 放弃注意力路线转轻量主干优先
5. 录用底线：**≥2 个消融验证有效模块** + 消融表 + ≥6 模型对比 + Grad-CAM/难例分析；Nano 部署是加分项不是核心
6. 可信度路线：A 跨数据集外部验证（首选 Mendeley Zhang2025 数据集，DOI 待核）> C 自建小测试集 > B aimagelab（实为公开谷歌Drive文件夹：drive.google.com/drive/folders/1C_wABDzfpdaRykVHoWSN8vAaLXs8Yaxn）+ D 数据文档化/3次重复/开源复现包
7. NEAU 数据集：邮件无回复已放弃（bsdai@neau.edu.cn，CEA2024 论文配套，百度盘需提取码）

## 5. 环境与资源

- 项目根：**E:\pig-behavior-yolo**（已从 C 盘迁入）；结果压缩包统一放 **桌面"跑的结果"文件夹**，命名 results-YY.M.DD.zip
- 用户硬件：Jetson Nano（亚博智能套件，**JetPack 4.6.3 / R32.7.3**，CUDA 10.2、TensorRT 8.2、Ubuntu 18.04；SSH jetson@192.168.1.9 已通，密码为亚博出厂默认、由用户保管不入库；冒烟测试预案：PC 导 ONNX → scp 到 Nano → trtexec 构建 engine 测速，失败则降级 v8n 基座）
- 算力：Colab 免费 T4（挂代理，标签页不能关）；备选 AutoDL（约 2 元/h）
- 用户可科学上网；+86 手机收不到 Kaggle 验证码

## 6. 文件地图

- `STATE.md` 本文件（总状态）· `LOG.md` 每日操作日志 · `README.md` 操作手册
- `paper/REVIEW_CHECKLIST.md` 评审标准七维度自查表 · `paper/problem-log.md` 问题记录（论文素材）
- `results/EXPERIMENT_LOG.md` 实验指标流水 · `results/baseline/`、`results/m1-ema/`（各含权重/曲线/混淆矩阵/metrics.json）
- `scripts/`：prepare_data.py（VOC/COCO→YOLO，--group-sep 防泄漏）、train.py、export_deploy.py
- `configs/`：yolo11-emar-n.yaml（M2 当前主线）
- `notebooks/`：colab_baseline.ipynb（基线/复跑用）、colab_compare.ipynb（对照组）、**colab_m2_emar.ipynb（当前主线）**
- `archive/`：废案归档（索引见 archive/ARCHIVE.md，含 M1/M1' 笔记本与配置、Kaggle 废案）

## 7. 待办（按优先级）

1. 🔜 **用户通读** v5 四件（英 JRTIP-paper-v5.docx + Supplementary_Material_v5.docx；中 猪行为检测-中文成稿-v5.docx + 猪行为检测-补充材料-v5.docx，中英已同口径）→ 送导师；导师通讯署名落实；v4 原件均未动
2. ✅ ~~新增段落过审稿团~~（报告 #7 已审，R1 四问当场修复；🟡 备答信素材两条：n=3 检验功效、与 [33] 同课题组平衡增强路线的比较口径）→ 通读后 submission-package 换 v5 双件
3. ✅ ~~投稿排版后实测英文版页数 ≤12~~（2026-08-08 已测：**10 页**，官方 Word 模板双栏几何 + Word 排版引擎实测，含 33 条文献；余量 2 页，bio 约 0.2 页无忧；超页预案废止。产物 paper/template/v5-jrtip-format.docx/.pdf，脚本 scripts/paginate_jrtip.py）
4. 投稿前核对：作者/单位/邮箱/bio 占位、Funding/Contributions、GitHub URL、Cover Letter 日期、Supplementary 单独上传
5. 确认功耗/FPS 测量工具名，补第 5 节方法学一句话（plan P4）
6. 有余力：Nano 上电补延迟三段分解（preprocess/inference/postprocess，审稿团 🟡 项）

## 8. 协作惯例

- 新会话恢复：`kimi resume` 选本会话；或对 AI 说"继续猪行为检测项目，读 E:\pig-behavior-yolo\STATE.md 和 LOG.md"
- 每天结束更新 LOG.md（新条目在最上）；重大决策同步本文件
- 用户是本科生、中文交流、Windows 本地 + Colab 云端训练
- 论文用英文写；APC 版面费需导师确认报销；导师通讯署名（未落实）
- **交付前审核规则（2026-07-25 生效，用户要求）**：任何交给用户执行的笔记本/脚本，交付前必须过三关——
  ① 静态审查：逐格查外部依赖（下载、路径、版本默认值变更），标注风险点
  ② 本地干跑：能本地 CPU 执行的核心逻辑（建模型、权重加载、数据转换、导出）必须在本地验证环境实跑通过
  ③ 失败预案：易错格附"报错→处置"对照说明
  历史教训：M1' 第 4 格三连错（缺权重下载 / torch2.6 weights_only / Detect nc=80→10 形状不匹配），皆因未实跑
- **文献先行审核规则（2026-07-26 生效，用户要求）**：制定策略/开发新模块前，先调研该方向近 2–3 年代表论文（3–5 篇），提取其训练协议、模块设计、评测方法，与我方方案对比并记录差异后再动工（首个成果：paper/lit-review-training.md）
- **学术诚信边界（同上）**：只借鉴"方法类别与设计思想"（加权采样、紧凑检测头等公开通用技术），
  ① 不复制文字/图表/独特命名；② 受启发的设计在论文中明确引用来源（引用是规范不是抄袭）；
  ③ 实验全独立（自有数据集、基线、消融）；④ 避免与单一论文模块组合雷同——
  我方差异化锚点：10 类多行为数据、问题诊断驱动选型、Nano 部署实测
- **额度保护规则（2026-08-01 用户设立，针对 Kimi Code 额度）**：Kimi Code 额度不足 5% 时，立即中止当前任务、完成状态固化（STATE.md/LOG.md 随时是最新的，天然可断点续传）、提醒用户。执行方式：额度仅用户侧可见（用户跑 `/usage` 查看），接近 5% 时用户告知，我立即收尾保存；低额度期我自动降级为省流模式（减少巡查频率与冗余输出）
- **模拟审稿团（2026-07-29 设立，用户要求）**：paper/REVIEW_BOARD.md；三角——R1 严苛（方法学猎手）、R2 宽松（应用派）、R3 平和（畜牧领域专家）；重大交付物与论文各章完稿必审，意见汇总为必办清单
- **提效技巧白名单/黑名单（2026-07-26 用户讨论后明确）**：白名单——TTA 评测（声明）、F1 最优阈值、
  数据清洗、精度-效率帕累托框架、每类 AP 突出弱类、Grad-CAM/难例图、Nano 实测证据；
  黑名单——挑选有利测试子集、test 集调参、只报喜不报忧（失败实验全部如实记录）
- 本地验证环境：E 盘机器已装 torch(CPU) + ultralytics（2026-07-25 建），用于②

## 更新记录

| 时间戳 | 内容 |
|---|---|
| 2026-08-18 17:55 | **"需要改的全部改完"并推送**（commit b675bd1，19 文件）：①中英 v5 功耗措辞 5+4 处（~5W→7W 总输入/5W 计算轨双口径，摘要/引言/部署/结论同步）②部署章插入三段分解段（延迟预算分解+持续运行稳定性+轨级功耗实测+CPU 瓶颈工程指引，EN 用 apply_v5_breakdown.py 锚点断言落位，ZH 改 build_paper_docx_zh_v5.py 重建）③README Key Results 同步双口径+持续运行行 ④验证全过：合规审计 20P/0F/1W/5M（摘要 216 词仍合规）、**页数复测仍 10/12（Word COM+PAGES=10，新增段落未破预算）**、旧 5W 措辞双版零残留 ⑤新文件入库：scripts/nano/（5 个测量脚本）+ results/deploy/thermal/（热节流日志+功耗样本）+ EXPERIMENT_LOG 两行实测。报告#8 Reviewer-1 两个必杀点（延迟分解/热节流）正文层面正式清零，剩余用户项：作者信息/iThenticate/投稿 |
| 2026-08-18 17:20 | **Nano 实时性补强三件套全部封账**（报告#8 Reviewer-1 两个必杀点清零）：①**延迟三段分解**（trtexec 复测 4 引擎，与论文数字一致）：M5@640 H2D 0.48/GPU 49.63/D2H 0.06/E2E 50.2ms/19.9qps、基线@640 50.02/50.6/19.8、M5@480 29.57/29.9/33.5、基线@480 30.60/30.9/32.3；CPU 侧新测（纯 Python 管线）：normalize+CHW 6.76ms（C -O2）、NMS 0.49ms（367 候选→145 保留）、PIL 解码 640 源 17.1ms/1080p 源 107.9ms——**发现"CPU 才是部署瓶颈语境，前/后处理必须 C/CUDA"**（Enqueue 开销 9.5–10.4ms 佐证），Reviewer-1 要的正是这类工程指引 ②**热节流**：12000 迭代持续 10.7min，吞吐 20.0qps 全程无衰减（p99 51.25ms）、GPU 30.5→43°C（峰 55.5）、零 throttle/EDP、GPU 频率恒定 1.408GHz ③**功耗**（INA3221 sudo 实测）：空闲 3.4W → 满载总输入 ≈7.0W（POM_5V_IN），GPU 轨 3.7W+CPU 轨 1.3W≈5.0W——**⚠️ 论文"~5W"对应的是计算轨，墙插总功率应写 ~7W，措辞待修（中英 v5 都要改）**。数据已入 results/EXPERIMENT_LOG.md + results/deploy/thermal/（thermal.log+summary+power-samples）；脚本 scripts/nano/（pre/post_bench、parse_thermal）；Nano 可关机。待办：v5 部署章补三段分解段落+功耗措辞修正（待用户定稿后执行）+新文件待提交 |
| 2026-08-18 16:40 | **GitHub 仓库修复已推送上线**（commit 6e6f893，32 文件）：报告#8 + README 四处刷新 + LICENSE 填写 + .gitignore 放行 27 个 results 核心文件（实验日志+24 metrics.json+双权重）；首次 push 因网络失败（梯子未开），用户开梯子后经 127.0.0.1:7897 代理推送成功，origin/main 已同步——Stage4 仓库问题全部清零，数据可用性声明与实物一致 |
| 2026-08-18 16:10 | **GitHub 仓库四项修复已备好待提交**（报告#8 Stage4 问题）：①.gitignore 例外放行 27 个核心文件（EXPERIMENT_LOG.md + 24 个 metrics.json（含三种子基线 baseline-r0/r1/r2）+ 双权重 m5-best.pt/baseline-e200-best.pt，weights 子目录与 results.csv 等大件仍忽略——修复"数据可用性声明与实物不符"）②README 四处：badge CC BY→MIT、状态行 v4→v5 投稿就绪（10/12 页实测）、Key Results 换 v5 三种子口径（0.606±0.008 vs 0.590±0.009，p≈0.09；recall +2.1）、论文指针 v3→v5+补充材料+results 说明、Citation 补"manuscript under review"条目 ③LICENSE 占位 [Year][Your Name]→2026 kksmks and contributors。待用户确认后一次 commit+push 收尾 |
| 2026-08-18 15:48 | **评审报告 #8：JRTIP 投稿仿真预审完成**（用户要求"模仿 JRTIP 预审"）——按期刊真实流程四关走查 v5 投稿包：Stage1 技术审查（页数 10/12✅、摘要 211 词✅、关键词 6✅、33 文献全被引✅，❌ 作者信息/bio/Funding/贡献声明全占位=退补首因；⚠️ iThenticate 未自查）；Stage2 scope 契合✅（real-time 素材齐备、与 WFE-YOLO 区分成立）；Stage3 双审稿人模拟：R1 实时方向=Major（🔧延迟三段分解缺失、热节流持续推理未测——Nano 上电半天可补）、R2 畜牧方向=Minor（标注协议出处一句话、告警路径一句话）；**Stage4 仓库核查新发现 🔴：results/ 目录零追踪（数据可用性声明与实物不符：metrics/日志/权重全未入库）、README 三处过时（v4 状态行/v3 文档指针/旧统计口径 59.6→59.3）、LICENSE [Year][Name] 占位+badge(CC BY)与文件(MIT)不一致、缺在审 citation 条目**。模拟判决：补作者信息后可送审，预计 Major Revision（补实时性分解）。需补清单已按办理人分组（用户=作者信息+投稿提交；助手=仓库四件修复待确认；Nano 上电=延迟分解+热节流） |
| 2026-08-08 23:15 | **中文版同步润色完成（6/10 处移植，4 处中文本就自然不动）**：build_paper_docx_zh_v5.py 改 6 处后重建——摘要（"三项工作让这套框架真正可用"→"三项设计选择支撑起最终结果"、"且出人意料地是全部参评模型中最快的"、尾句"如实划定"→"为整套研究收束闭环：划清何处有效何处失效"）、引言¶2（"这就是为什么"→"工程趋势因此只有一个方向"）、4.2（"回溯性地印证"→"支持"，同步英文弱化）、4.3（"两个现象值得记录"→"尤为突出"）、**4.5（"经不起审稿人推敲"→"会夸大证据"——中文版的同款元话语，必须同步）**、8 结论（"诚实地划定"→"不加粉饰地划出"）。未移植 4 处及理由：2.1 尾句（中文无双逗号插入问题）、2.3（"很少被讨论"中文自然）、4.6（"这在意料之中而非自相矛盾"本就流畅）、5 部署（中文已是主动语态"有三点实践发现值得报告"）。重建后脚本内置 14 锚点断言通过 + 新文 6 探针全中 + 旧文 6 残留零。中英 v5 人味化同口径封账，剩余=用户通读+填作者信息 |
| 2026-08-08 22:59 | **英文 v5 人味化润色（10 段，用户批准，中文版待过目后同步）**：通读全部 121 段后判定 80+ 段已是自然人学术体刻意不动，只改 10 处真 AI 腔——摘要（"Three things make..." 清单腔/"interestingly"/"honestly delimits"）、¶7（"This is why" 教科书腔）、¶15（双逗号插入语）、¶19（Still/seldom 重复）、¶45（retrospectively justifies 拗口）、¶50（"are worth noting" 典型 AI 套话→"stand out"）、**¶55（"would not survive a careful reviewer" 元话语——在审稿人面前谈审稿，防御感，改对证据陈述）**、¶57（节奏）、¶71（被动改主动）、¶86（honestly 修饰）。scripts/apply_v5_polish.py 整段替换前逐字符断言 + 含数字 token 多重集/引用零漂移校验（抓到 ¶57 破折号粘连 token 一例已修正）。复跑审计 20P/0F/1W/5M 不变、摘要词数仍合规、排版仍 10 页。逐段对照清单 paper/polish-v5-diff.md（改前/改后/理由）待用户过目 → 过目后同步中文版并重建 |
| 2026-08-08 22:44 | **JRTIP 格式合规体检（scripts/audit_jrtip_format.py，26 项机查）+ 3 处修复**：终审 20 PASS / 0 FAIL / 1 WARN / 4 MANUAL（真用户项：作者行/Funding/Author Contributions 占位 + bio）。修复（apply_v5_compliance_fix.py 全中 3/3）：①声明节标签 Conflicts of Interest→**Competing Interests**（指南规定标签名）②[2] Peden 2018 补 DOI 10.1016/j.applanim.2018.03.003（SRUC 机构库核实）③**[18] Gu 2024 文章号勘误 109524→109512**（ScienceDirect 核实，确系笔误）并补 DOI 10.1016/j.compag.2024.109512——中英同步（build_paper_docx_zh_v5.py 改 2 条重建）。WARN=11 条无 DOI 均合规（arXiv/数据集/软件/INMATEH/CVPR）。已 PASS 项：摘要 211 词/关键词 6/标题十进制≤3 级/图表顺序引用/图题注尾无句号/33 条文献全被引（修审计脚本多引用组解析 bug，[1,2]型曾漏报）/AI-Assisted 声明/动物福利/无尾注/Online Resource 1×2/GitHub 链接/SI 头部/Cover Letter real-time×9。投稿包主稿已刷新；排版 PDF 重建仍 10 页 |
| 2026-08-08 22:35 | **旧副本清理 + v5 落账补提交**：应用户要求删除 v4 及更早旧副本 10 件（git rm 9 件可追溯：英 v2/v3/v4/v4-partial/Supplementary_Material(v4)/中 v2/v3/v4/补充-v4；rm 1 件 v4-backup 系 gitignore 排除件）——paper/ 现存 docx 仅 5 件：投稿=JRTIP-paper-v5.docx + Supplementary_Material_v5.docx（投稿时转 ESM_1.pdf）+ cover-letter-jrtip.docx；导师=猪行为检测-中文成稿-v5.docx + 猪行为检测-补充材料-v5.docx。发现 08-07 v5 全套工作（中英 v5/补充 v5/报告#7/提标图/投稿包换 v5/ESM_1.pdf/9 个脚本）一直未提交，本次一并 add 落账（旧副本在 git 历史中仍可追溯） |
| 2026-08-08 22:21 | **页数实测销账：v5 = 10 页（上限 12，余量 2 页）**。应用户"专业软件"疑问核实 JRTIP 官方指南：Word 明确可投（"Word files are also accepted"），下载官方 Word 模板（media.springer.com，EIC Kehtarnavaz 签名 .doc，34KB）→ Word COM 转 docx 解析几何真源（Letter / T·B 17.8mm / L·R 16.5mm / 双栏间距 288twips / TNR 正文 10pt 行距 252 / 标题 24pt / 作者 11pt / 摘要 9pt / 图题表题 8pt / 文献 8pt）。新建 scripts/paginate_jrtip.py 灌 v5 入双栏格式：图片按栏重排（Fig.2/5 通栏 174mm、其余单栏 84mm——Fig.8 遵 08-07 决议单栏勿通栏，连续分节符实现）、表格栏宽 100%+autofit+8pt、run 级字号剥离交样式。Word 排版引擎实测 **PAGES=10（Word 计词 6751）**，导出 PDF pypdf 校验：8 图题 7 表题齐、Statements and Declarations/Online Resource 1 在位、33 条文献完整 [1]–[33]。bio（约 0.2 页）加入后仍远低于上限，超页预案（Fig.3→补充/Table 2→正文）废止。产物 paper/template/{JRTIP-WordTemplate.doc,.docx,v5-jrtip-format.docx,.pdf}；v4 测量中间件已删。注：本次先对 v4 测得 10 页后发现 v5 已成现行稿（08-07 三种子+33 文献），v5 复测同为 10 页，以 v5 为准 |
| 2026-08-07 19:45 | **submission-package 整体换 v5，投稿进入"只差填作者信息"状态**：①manuscript/换 JRTIP-paper-v5.docx、supplementary/换 Supplementary_Material_v5.docx（v4 件移除）②Word COM（powershell 全路径调用，git-bash 无 powershell 别名）转 ESM_1.pdf——pypdf 验证 2 页含 S1/S2/期刊名/0.452/0.5933 ③图分辨率复核（Springer 半色调300/组合600/线图1200，84mm单栏/174mm通栏）：Fig2/5/6 原达标，**Fig1/3/4/7 提标重出**（build_figures.py dpi 200→430 + 新建 upgrade_fig3_hidpi.py 从 results.csv 重绘 Fig3——顺带修复 Springer 违规：原 Fig3 图内含标题，已去；M5 改虚线灰度可辨；曲线走势与原图一致 M4 领基线领 M5），重出后 771–907dpi 全达标；**Fig8（1198×1417 竖版拼图）通栏仅 175dpi，定为单栏排版设计（362dpi ✅），README 注明勿通栏** ④README 全量重写：v5 结构、逐图分辨率表、检查清单更新为只剩用户项（作者信息/Funding/Author Contributions/Cover Letter 日期/实测页数/导师通讯署名）。注意：主稿 docx 内嵌图仍为低分辨率版（评审够用，生产用单独上传件；英文版勿用 build_paper_docx.py 重建——它是 v4 口径） |
| 2026-08-07 19:20 | **中文版同步 v5 完成**：新建 scripts/build_paper_docx_zh_v5.py / build_supplementary_zh_v5.py（v4 脚本原件未动）→ paper/猪行为检测-中文成稿-v5.docx + 猪行为检测-补充材料-v5.docx。同步内容：摘要/表3脚注/4.5 节三种子基线口径（val 0.5822±0.0087 / test 0.6060±0.0084、p≈0.09）、2.1（PBR-YOLO+Rahman，审稿团修复后口径）/2.2（IRFS+Crasto）/2.3（本刊先例+Luo 剪枝蒸馏）末段、7 讨论对比段、关键词 8→6、参考文献 +[27]–[33]（assert 33）、4.4 表 S2 指引、在线资源 1 表述；补充材料 S1 补 M5 active=0.452 + 新增表 S2（测试集分类别 AP50，含单次实验口径声明）。结构脚本校验 14 项锚点全过（8 图 7 表 33 文献）。中英双版 v5 同口径封账，待用户通读 |
| 2026-08-07 19:00 | **JRTIP 官方指南合规检查 + 6 处修复**（scripts/apply_v5_jrtip.py）：摘要缩写 mAP50/FPS 首现展开（211 词 ≤250）、Fig.5/8 题注尾句号删除、Declarations→Statements and Declarations、SI 提及改 "Online Resource 1"、补充材料头部加期刊名+作者占位。已合规项：关键词 6、文献 33 条全被引、图表顺序引用、IRB/知情同意/Data Availability（含 GitHub）/AI-Assisted 声明、Cover Letter real-time 论述。🔴 用户必办：作者/单位/通讯邮箱/ORCID/Funding/Author Contributions 占位填写；🟡 新挂账：图有效分辨率按组合图 600dpi 复核（README 记最弱 330dpi）、SI 投稿时转 PDF 命名 ESM_1.pdf、投稿界面单独填 Author Contributions+Competing Interests |
| 2026-08-07 18:45 | **审稿团报告 #7（v5 改动段落专项）**：R1 抓到 4 处全部当场修复（scripts/apply_v5_review7.py）——①摘要 statistically indistinguishable→comparable（n=3 t 检验不显著≠等效，D8）②2.1 对 PBR-YOLO 的缺失性声明无法确证（Elsevier 全文不可得）：核实后改写——Rahman [28] 全文确认图像级随机切分（自认 within-facility）✅，PBR-YOLO 仅摘要级证据 → 随机切分声明只挂 Rahman + "to our knowledge" 对冲 ③Discussion n=2 因果 "show that...do not transfer"→"suggest...may not transfer" ④S2 caption 补 "single-run values (seed 0)" 防与 4.5 节 0.6060 均值误读。4.5 节统计数字复核精确（SE 0.0069/t≈2.25/p≈0.088）。R3 领域核查：[33] Luo 与 [27] PBR-YOLO 同课题组、其全文确认用增强做类平衡——我方声明范围未波及，与 [33] 的路线比较列入备答信素材。🟡 备答信素材 2 条（n=3 功效、[33] 比较）；待办②审稿团项销账，剩余=用户通读 |
| 2026-08-07 18:35 | **baseline 三种子跑完并写入 v5**：AutoDL 3090 约 3.6h 跑完 seed0/1/2（val 0.5729/0.5835/0.5902，test 0.5964/0.6095/0.6120）→ **val 0.5822±0.0087 / test 0.6060±0.0084**；seed0 逐格复现旧单次 0.5964（旧跑默认 seed=0）。统计判决：M4 −0.007 在基线 1σ 内、M5 −0.016 ≈ 2SE（p≈0.09 不显著）→ "不优于基线、胜在弱类再分配+召回+效率"叙事不变。scripts/apply_baseline_3seeds.py 锚点替换 6 处全中：摘要（vs 三种子基线 0.606±0.008）、Table 3 脚注（0.6060±0.0084）、4.5 节四句重写。结果落账 results/baseline-r0/r1/r2/metrics.json + baseline-3seeds-summary.json，EXPERIMENT_LOG 加三行。待办①销账；**AutoDL 实例待用户关机**（约 2 元/h）。技术注记：cloud.py 的 SFTP push/pull 坏（子系统文件系统隔离），上传走 base64+exec、下载走 exec cat |
| 2026-08-07 13:55 | **文献补强 v5 双件 + M5 每类 AP 补测**（外部评估推动，详见根目录 JRTIP-revision-plan.md v2）：①scripts/eval_m5_perclass.py 本地 CPU 官方 val 通道补齐 M5 val active=0.452（原日志截断缺失格）+ 新测 test 每类 AP，val 0.5611/test 0.5933 与云端逐格核对偏差 ≤0.003；教训：predict+复刻 AP 因 NMS IoU 0.7 vs 官方 0.6 偏低 ~3 点勿用②scripts/apply_v5_edits.py → JRTIP-paper-v5.docx（2.1/2.2/2.3/Discussion 各补一段、4.4 补 Table S2 指引、关键词 8→6、参考文献 +[27]–[33]：PBR-YOLO/Rahman/IRFS/Crasto/Guo/YOLO-FGD/Luo 剪枝蒸馏，均网络核实）+ Supplementary_Material_v5.docx（S1 补格 + 新增 S2 测试集每类 AP，fix_supp_v5_order.py 修表序）③autodl/baseline_3seeds.py 备好（干跑通过）：baseline 三种子是剩余唯一实质实验，跑完更新 4.5 节统计。v4 原件未动，v5 待用户通读+审稿团复审 |
| 2026-08-06 00:45 | **泄露旧 Roboflow key 已吊销**：用户在 Roboflow Settings→API Keys 删除 Key 1（hMQC…，截图确认已消失）；Key 2（NRyn…）经全仓 grep 确认零出现、从未暴露，保留。待办②销账，剩余用户项=通读双版送导师/排版实测页数 |
| 2026-08-06 00:37 | **投稿材料包预组装完成**：新建 submission-package/（figures/manuscript/supplementary/cover-letter + README.md 清单）。8 图按论文图号规范重命名收齐（Fig1 分布+倍率←fig6-class-distribution、Fig2 结构←fig4-architecture、Fig3 曲线←fig5-curves、Fig4 帕累托←fig8-pareto、Fig5 Grad-CAM 拼图←fig5-gradcam-hardcase.jpg、Fig6 混淆矩阵←m4-wsample/confusion_matrix_normalized、Fig7 部署←fig9-deploy-pipeline、Fig8 泛化拼图←fig8-generalization-ext）；主稿 JRTIP-paper-v4.docx + 补充材料 + Cover Letter 双版本各一份。README 含图号↔源文件对照表、投稿前检查清单（通读/吊销 key/实测页数/图题逐字复制/通讯作者核对）、分辨率说明（全部满足 Springer 线图要求，最弱 Fig.4/Fig.7 单栏 ≥330dpi）。纯增量不动正文数字 |
| 2026-08-05 23:55 | **中文版同步 v4 完成**：build_paper_docx_zh.py 全量重写至 v4 口径 → 猪行为检测-中文成稿-v4.docx（8 图 7 表），新建 build_supplementary_zh.py → 猪行为检测-补充材料-v4.docx（表 S1）；拼图永久资产 results/analysis/fig5-gradcam-hardcase.jpg、fig8-generalization-ext.png 中英共用；同步点与英文逐项对齐（合并表/部署化正文/补充迁移/表 5-6-7 改号/图 5a5b8a8b 引用/Table 2 补引/时序阴性结果句）；结构脚本核查通过（8 图段 7 表、引用全 ≥2）；git faada57 提交。中英双版同口径封账，剩余用户项不变（通读双版/吊销 key/push 回填 URL/排版实测页数） |
| 2026-08-05 23:45 | **投稿冲刺四件套落地**：①**v4 定稿完成**（scripts/finalize_v4.py 一次性做完 manual-todo 全部手动项：Table 1+2 合并四列、部署表化正文、每类 AP 移 Supplementary_Material.docx[Table S1]、效率→T5/压力→T6/跨数据集→T7、Fig.5 左右拼图、Fig.8 上下拼图限高 7.2in；脚本审计 Fig.1-8/Table 1-7 无跳号无重复；顺手修复编号脚本残留混乱——Table 2×2/4×3/6×2、Fig 4/6/7/8 双黄蛋——与 Table 2 正文零引用；Limitations 时序画饼句改为实测阴性结果句）②**审稿团报告#6 收录**：报告#5 篇幅🔴清零，残余风险=页数贴上限（排版后实测，预案 Fig.3→补充/Table 2→正文）③**Cover Letter 双版本**（cover-letter-jrtip.md/.docx）：real-time 实质论述（延迟-分辨率权衡/INT8 缺失/融合抹平）+主动披露切分与两级泛化+补充材料声明，未点名竞品 ④**GitHub 仓库整理**：git init+首提交（8823a33，74 文件）；7 文件明文 Roboflow key 全抹除（**用户需吊销旧 key 换新**）；.gitignore 补 ext-eval/tmp/备份；requirements.txt 重写 |
| 2026-08-05 22:55 | **时序平滑模块判决：否决**。补建真 mAP 评估器 scripts/eval_temporal_map.py（复刻官方协议：box_iou+ap_per_class、IoU0.5-0.95、101点插值；原 eval 子命令只有类别分布统计无法判决）。三组参数全灭：w3v2 mAP50 −2.66（0.4078→0.3812，10 类全 ≤0）/ w5v4 −1.27 / w3v3 零翻转零效。根因：val/test 为稀疏抽帧（帧号差 50~580），IoU 跟踪跨大时间间隔失效、投票污染正确单帧标签——该技巧仅适用于密集连续帧部署场景（Nano 实时视频），论文不得主张其精度收益。**另揪出 run_temporal_inference.py 类名映射 bug**（CLS_NAMES 误用 Roboflow 展示序，与 data.yaml 字母类序不符 → 旧 compare.txt 类名整体错标、计数正确），已修复并重生成 compare.txt。注：评估输入为 conf=0.25 截断预测，绝对值低于正式 val 0.5608，相对比较公平；若论文引用绝对值需按官方协议（conf=0.001）重测。EXPERIMENT_LOG 补两行，LOG.md 补 08-05 条目 |
| 2026-08-04 18:20 | **引用体系+图形化+审稿团扩维三件套落地**：①26 条参考文献全部网络核实入文末（Springer Basic 数字制；**揪出 3 处二手转引错**：Li et al. 2022→2024、Bergamini ICPR→VISAPP 2021、YOLOv8 误配 Zenodo DOI（实属 yolov5 v7.0）已避开；牛棚无出处句→Alameer 2020 替换；正文 [1]–[26] 无缺引）②新增 5 图（类别分布+倍率、每类AP柱状、帕累托散点、部署管线、泛化断崖柱状）+图 8 混淆矩阵，全部按正文顺序重排 Fig.1–11、sans-serif+纹理灰度可辨、Springer 图题式③REVIEW_BOARD 审查维度 v2（4→10 维：新增引用/图表规范/篇幅预算/过度声明/可复现/期刊条款）+报告#5：**揪出 2 个必修**——篇幅超 JRTIP 12 页上限（11图10表→投稿排版须压至 ≤8图≤6表，方案已给）与 INMATEH 表图双呈禁令；调研确认 JRTIP 引用为 [n] 数字制、cover letter 必须论述 real-time 问题；writing-guide 已补 JRTIP/INMATEH/EcoInfo 格式规则 |
| 2026-08-04 17:05 | **v3 全量数字审计（用户要求）揪出并修复 3 个真错误**：①参数削减 −5.6%→**−4.4%**（实测权重：基线 2,591,790 / M5 2,477,646 = −4.40%，fused 口径 −4.37%；原 5.6% 与文中 2.58M/2.47M 自相矛盾，改 7 处×2 语言）②FPS"领先 yolo12n 33%"→**50%**（117.6 vs 78.4，慢 33% 的是 yolo12n）③3.3 采样公式口径错误：代码统计的是**含类图像数**而非实例数（sitting 104 张训练图、investigating 1,714 张、round(√(1714/104))=4.06→4；原文"144 实例/√(4203/144)=4"口径与算术双错），另修摘要/结论"最稀有行为 active"→"低频行为 active"（最稀有类是 sitting 144 实例）；已复核无误项：表2分布合计13,995✓、表3过采样规模5785/5889✓、三次重复均值±std（样本标准差）✓、全部 metrics.json 数字✓、每类 AP 表✓、部署/泛化数字✓、−0.006 在 1σ 内✓；双版 DOCX 已重建 |
| 2026-08-04 16:39 | **v3 双版成稿重建完成**：按评审报告#4 修复全部必修项+建议项并整体详写（叙述量约翻倍）——英文 paper/JRTIP-paper-v3.docx、中文 paper/猪行为检测-中文成稿-v3.docx（均 87 段/10 表/5 图）；表 1 定义表与表 2 分布表已补入正文、表 3b 前移 3.3、消融表加三次重复统计脚注、recall+2.1 标注 val、FLOPs 边界两处点破、M5 外集 P0.70/R0.03 补解释句、Comportamentos 注明 CC BY 4.0；**数字勘误**：M4 test mAP50-95 更正为 0.4379（曾误写 0.4300，经 metrics.json 核验），M6 补 0.4321；REVIEW_BOARD 报告#4 汇总表已逐项标 ✅ |
| 2026-08-04 15:08 | **中文成稿生成**：paper/猪行为检测-中文成稿-v2.docx（996K，五图全嵌+全部最终数字：M5 部署双档、表 3b 倍率消融）——供导师评审与后续翻译校对使用；中英双稿数字已对齐 |
| 2026-08-04 15:00 | **部署矩阵正式封账**：M5@640 50.2ms/19.7FPS、M5@480 30.0ms/33.3FPS、~5W（Jetson Nano FP16 实测）；排障全记录（导出残缺→状态污染→重启救场→非简化导出成功）；成稿表格已用正式数字重建（JRTIP-paper-v2.docx）；实验工作全部结束，进入纯写作阶段 |
| 2026-08-03 22:30 | **倍率消融完成（斧 3 落账）**：cap3 val0.5754/test0.5776、cap4 0.5816/0.6035、cap5 同 cap4——**cap5 不生效**（本数据集最大倍率只需 4，sitting 达满值）；结论"cap≥4 满收益，cap5 保守"写进 Table 3b；提醒用户关机+Nano 上电 |
| 2026-08-03 20:15 | **带图成稿生成**：paper/JRTIP-paper-v2.docx（996K，五图全嵌：结构图/训练曲线/Grad-CAM/难例/异源实况）；图 4（结构图）与图 5（训练曲线）绘制完成；倍率消融脚本就绪（m4_train.py 加 --max-factor，dataset-os-f{n} 分目录防缓存污染，f=3 干跑验证通过）；文本采用自然学术体（we 视角） |
| 2026-08-03 18:30 | **v2 双稿成稿**：paper/draft-v2-en.md（JRTIP 目标刊版，新增"恒等保持集成策略"为方法贡献、倍率消融预留位）+ paper/draft-v2-zh.md（中文评审版，供找导师争取支持）；选刊定案 JRTIP 主推（SCIE Q2 免费订阅制）；v1 作废 |
| 2026-08-03 17:30 | **选刊决策（paper/journal-choice.md）**：主推 **INMATEH**（≈0 版面费 + ESCI/Scopus + 数周回应 + WFE-YOLO 直接先例对口）；备选 IJABE（Q2 但 24 周慢）；不选 MDPI 系（APC 1.2-2 万超预算）；对修改稿影响：格式自由、收紧 Discussion、必引 WFE-YOLO |
| 2026-08-03 17:10 | **论文初稿 v1 成稿**（paper/draft-v1.md，全十章英文，~5000 词）并通过审稿团三审（报告#3）：数字一致性核对通过（修正迁移键数笔误）；必办新增：软件版本号、结构图/曲线图、M5 部署正式数字、猪场环境描述一句 |
| 2026-08-03 16:00 | **论文详细提纲成稿（paper/outline.md）**：IMRaD 十章结构 + 14 图表清单核对（9 表 5 图，大部分素材已就位；待办仅模型结构图、训练曲线拼图、M5 权重部署补测）；主线定调"效率甜点+弱类治理+泛化诚实" |
| 2026-08-03 16:45 | **斧 2 全部落账**：M5 外集 0.0361（P0.70/R0.03 域外保守预测）；外部验证四行齐（baseline 0.067 / M4 0.038 / M3 0.038 / M5 0.036——全员同量级退化，证明是领域现象非模型个案）；M5+baseline-e200 权重已拉本地（部署表正式数字待用）；用户可关机 |
| 2026-08-03 14:40 | **斧 2 结果（诚实但扎心）**：外部验证 baseline 0.067 / M4 0.038 / M3 0.038——跨农场+花斑品种双重漂移致崩（可视化铁证 ext-detections.jpg）；入 P9：写为 Generalization Analysis+Limitation+FutureWork（不宣称泛化成功），与 P7 形成"跨栏 0.15→跨场 <0.07"证据链 |
| 2026-08-03 14:15 | **斧 2 数据就位**：Comportamentos 下载完成（537MB 完好）并转换为我们类体系（696 图/1218 框五类交集，Sleeping→lying 合并、Moutend 弃）；**外部交叉验证评估进行中**（baseline/M4/M3 三权重 CPU 直测）；M5 权重评估待云端开机补 |
| 2026-08-02 23:10 | **斧 2 外部验证集核实**：选定 Roboflow《Comportamentos》（maria-dnxxx，8,151 张 8 类，CC BY 4.0，与主数据集独立来源——PigLite 论文同款外部验证集）；类映射：Walking/Eating/Lying/Investigating/Drinking→walk/eat/lying/investigating/drink（Sleeping/Moutend/No comedouro 无对应弃用）；下载需用户开梯子（562MB）；备选 behavior_pig-53jkk（7.1k） |
| 2026-08-02 22:57 | **部署矩阵成型**：640 输入 19.7 FPS / **480 输入 33 FPS**（分辨率换帧率杠杆确认）；整机功耗 ~5W（含推理）；INT8 判死（Maxwell 无原生支持）——里程碑 70% 主体完成，部署章数据完备（真板真引擎真帧率真功耗+诚实限制） |
| 2026-08-02 22:20 | **Nano 部署第二阶段**：FasterNet 引擎实测 49.8ms≈20FPS ≈ 基线（50.8ms）——**诚实发现：PConv 优势在小模型+老 TRT 融合下不显形**（部署章节如实写）；转入 INT8 量化（Nano 真正的速度杠杆）：校准集 120 张已上板，baseline INT8 引擎构建中 |
| 2026-08-02 22:05 | **Nano 冒烟测试通过**：trtexec 在 JP4.6（TRT 8.2）上成功构建 yolo11n FP16 引擎（9.2M），实测 **50.8ms ≈ 19.7 FPS**——部署链路打通；FasterNet 版引擎构建中（对比 PConv 在内存受限设备上的速度优势）；ONNX 用 opset=12 导出兼容老 TRT |
| 2026-08-01 18:00 | **冲 Q3 补强方案定稿（paper/Q3-plan.md）**：三板斧——①Nano 部署+INT8 量化（第三技术点，"PConv 结构+INT8 量化"双重轻量化）②Mendeley 外部交叉验证（泛化金标准）③采样倍率消融；明确不做 EDH 头/重基座/新注意力（范围控制）；节奏：本周 Nano → 并行 Mendeley → 下周倍率消融 → 写作 |
| 2026-08-01 12:35 | **M5 三次重复完成**：seed0/1/2 → val 0.5620±0.0079 / test 0.5904±0.0086（与基线差 0.006 在 1σ 内）——"精度相当、更轻更快"叙事成立；质量门两个必做只剩 Nano 实测；提醒用户关机 |
| 2026-08-01 11:00 | **Q3/Q4 质量门评审（REVIEW_BOARD 报告#2）**：判决"当前=Q4悬/Q3不够"；叙事从"提精度"改写为"效率甜点+稀有类治理"（test 差异不显著+参数-5.6%+FPS 领先+active+11.3）；补强清单：Nano 实测🔴、M5 重复×2🔴、TTA/F1🟡、外部验证🟡 |
| 2026-08-01 10:45 | **里程碑 60%：三次重复完成**。统计 val 0.5790±0.0054 / test 0.5987±0.0062（seed0 与 M4 首跑完全一致）；**诚实发现：test 均值仅超基线 +0.002，总分改进在噪声边缘，论文须以弱类改善+召回+效率为主线呈现**；用户设立余额保护规则（<5% 中止保存+提醒）；实例已自动脱 GPU，提醒用户完全关机 |
| 2026-07-29 14:20 | **排雷：重复训练险用错数据**——压力测试残留的 gsplit 过采样集（dataset-os）被复用，巡查中从验证集图片数（764≠1123）当场识别；已停训清缓存重启，现数据正确（随机切分）；教训固化：**dataset-os 缓存目录跨任务必须清理**，任务启动前核对扫描行数据量 |
| 2026-07-29 14:00 | **效率基准实测（3090）**：baseline 112.8 / M4 112.1 / **M5 117.6 FPS（最快）** / **yolo12n 78.4（慢 33%）**——M5 效率王地位+1，yolo12n 精度王代价是速度；M4 权重已拉本地；**3 次重复训练启动**（seed 0/1/2，约 4.5h，cron 6b73be85 监控中） |
| 2026-07-29 13:20 | **审稿团必办两项清零**：行为定义表+标注协议+伦理声明（paper/tables/behavior-definitions.md，依据 aimagelab 词表核实，active 类来源注明）；难例检测图产出（results/analysis/detections/）——抓到 fight/lying 混淆典型误检例（fight0.84 实为躺卧），论文错误分析图素材到手 |
| 2026-07-29 13:00 | **模拟审稿团设立并开首评**（paper/REVIEW_BOARD.md）：R1 严苛/R2 宽松/R3 平和三角；首评发现 4 项必办（3次重复、行为定义表+伦理声明、Cover Letter 主动披露切分、检测对比图）+ 2 项加固；最硬防线=M6 阴性对照（基座选择被数据验证） |
| 2026-07-29 12:50 | **分析包开工（65%）**：每类 AP 对比表编成（paper/tables/per-class-ap.md，含 val/test/压力测试三层）；Grad-CAM 本地跑通并出 3 组对比图（results/analysis/gradcam/）——基线注意力紧咬猪身、M3 略发散但对位，可直接做论文图；技术要点记录：ultralytics 加载后参数默认全冻结，Grad-CAM 前必须 requires_grad_(True) |
| 2026-07-29 12:29 | **压力测试三行凑齐**：baseline-gs val0.075/test0.155、M4@gsplit val0.139/test0.145、M5@gsplit val0.107/test0.153；关键发现：**异源难场景下 M4(val) 是基线 2 倍**——采样对泛化的增益在压力测试下获支撑；专章写法定为"全员退化（诚实）+ 采样显著缓解（亮点）"；cron e80e49db 已关闭，提醒用户关机 |
| 2026-07-29 10:40 | **压力测试两枪启动**（M4/M5 @ dataset-gsplit，过采样 438 批验证中）；巡查 cron e80e49db 已挂；主表沿用随机帧切分结果，此两枪仅供"泛化压力测试"专章 |
| 2026-07-29 10:30 | **乌龙自纠+真发现**：所谓"数据集缩水"系本人计数方法错误（wc -l 漏数尾行），MD5 校验证明云端数据完整无损；真发现是**序列切分下的泛化鸿沟**（val 0.075/test 0.1545 vs 随机 0.57）。**用户拍板 B 方案**：主表沿用随机帧切分结果（不重跑），序列切分作"泛化压力测试"专章披露；重启 M4/M5@gsplit 补齐压力测试三行 |
| 2026-07-29 09:55 | **最深的雷：云端数据集导出缩水 40%**（云端 train 仅 5,945 框 vs 本地完整版 9,881 框；全集 10,059 vs 13,995）——此前全部云端训练都在缩水集上进行；已停掉错误 M4 训练（0 进程），正推送本地完整 dataset.zip（379MB）到云端，随后重建数据集+重切分+三件套重跑；教训入 P8（完整性校验要核框数）；顺带：新切分基线崩坏（0.075）主因大概率源于此（注：此条后被 10:30 条目纠正为计数乌龙） |
| 2026-07-29 09:15 | **新切分三连跑启动**：make_gsplit.py 云端执行成功（4116/764/740，零泄漏验证通过）；旧过采样集已清（防复用漏数据）；baseline-gs → m4 → m5 串行训练中（第一枪 epoch 8/200，258 批=新切分生效）；巡查 cron 6c20d481 已挂 |
| 2026-07-29 09:08 | **重大发现：源数据集序列级泄漏**——14/14 序列在 train/valid/test 全重叠（绝对数字高估、相对比较仍成立）；处置：按序列重切（73/14/13，本地模拟零泄漏验证通过，make_gsplit.py 已备，云端硬链接零上传）；**核心三件套（基线/M4/M5）需按新切分重跑**，论文数字以重切后为准；baseline_train.py 已加 --data/--name；P7 已入 problem-log |
| 2026-07-27 21:17 | **M6 判决：采样增益未迁移**（test 0.5994 < 裸 yolo12n 0.6135）——注意力架构原生抗不均衡更强，重采样反致过拟合；**冠军确定留在 M4/M5（yolo11n 基座）**，M6 作阴性对照写入 Discussion（模块选型被数据验证）；**里程碑 50%：消融阶梯完整**（基线/M4/M3/M5/M6 + 对照组 4 模型）；cron 9e663c9c 已关闭，提醒用户关机 |
| 2026-07-27 19:45 | **M6（yolo12n+加权采样）训练启动**（epoch 8/200 验证中，~10 it/s，约 2h）；巡查 cron 9e663c9c 已挂；判决线 test≥0.61 |
| 2026-07-27 19:30 | M6 文献审核完成（paper/lit-review-yolo12.md）：**建议换 yolo12n 为基座**——NeurIPS 2025 正会、TRT 部署野外已验证、农业圈已接受（GTDR-YOLOv12）；决策：M6=yolo12n+加权采样（零结构改造，~2 元），FasterNet 不改 yolo12（机制冲突）；m6_train.py 已备好（判决线 test≥0.61）；部署双路冒烟（yolo12n 与 M5，谁上 Nano 用谁） |
| 2026-07-27 19:22 | **里程碑 45%：对照组全部收工**。最终榜（test）：yolo12n 0.6135（王）/ M4 0.6035 / RT-DETR-l 0.6008 / yolov5n 0.6001 / 基线 0.5964 / M5 0.5932 / yolov8n 0.5877 / M3 0.5691；规模：v12n 2.56M/6.3G、v5n 2.50M/7.1G、v8n 3.01M/8.1G、rtdetr ~32M/103G。**战略发现：yolo12n 同体积更强，候选 M6 新基座**；cron b02ae2c9 已关闭，提醒用户关机 |
| 2026-07-27 11:52 | **对照组 fleet 训练启动**（rtdetr-l→yolov8n→yolo12n→yolov5n 串行，全程约 6h ≈ 8 元）；rtdetr-l.pt 下载限速（GitHub 国内 30KB/s）起步延迟 ~30 分钟；挂巡查 cron b02ae2c9（30 分钟/次，完成自动拉数出表并提醒关机） |
| 2026-07-27 11:35 | **Nano SSH 直连打通**（jetson@192.168.1.9，亚博默认密码）；JetPack 版本确认为 **4.6.3**（CUDA 10.2 / TRT 8.2 / Ubuntu 18.04）——部署按老工具链 trtexec 路线规划；挂账近一周的 JetPack 待办关闭 |
| 2026-07-27 11:17 | aimagelab annotated.tar 下载完成（3.1GB 完整）并破解格式：output.json 按对象逐帧 bbox+behaviour 标注（词表与 Roboflow 一致，如 investigating）；**重大发现：Roboflow 数据命名(2019_11_15_000033_x)与 aimagelab 序列完全一致——两者同源**。推论：①数据集 provenance 可追溯（data card 强化）②aimagelab 不能当独立外部验证集（需 Mendeley/自建）③可按文件名做精确的序列级泄漏审计（优于感知哈希）④待解包视频帧（color.mp4）备用 |
| 2026-07-27 10:59 | 第 9 格开工：对照组文献审核完成（TriPerceptNet/MEI-YOLOv11/玉米表型等 fleet 依据），四选定 **YOLOv5n / YOLOv8n / YOLOv12n / RT-DETR-l**（FasterRCNN/SSD 属效率淘汰项不跑）；compare_fleet.py 写好（原始数据、200+patience30、val+test 双评估、异常容错）；aimagelab annotated.tar 后台下载中（371M/3G，代理限速） |
| 2026-07-27 02:07 | **里程碑 40%：M5 成功**（114 轮早停）：test mAP50 **0.5932** / 0.43，val 0.5608——仅低基线 0.32 点换参数 -5.6%，"既准又轻"成立，**最终模型候选诞生**；nose-to-nose 0.71 反超基线；巡查 cron f6c67f03 已关闭；提醒用户关机 |
| 2026-07-26 22:55 | **M5 训练已由助手远程全自动启动**（推脚本+MD5校验+nohup启动+验证日志推进）；挂自动巡查 cron f6c67f03（每 30 分钟检查 m5.log：完成则拉结果判决并提醒关机，异常则诊断报告）；自动化闭环成立：用户仅需开机 |
| 2026-07-26 22:45 | 建立 PROGRESS.md 里程碑体系（20 格×5%，当前 35% 第 8 格进行中；用户要求提升获得感） |
| 2026-07-26 22:38 | M3 test 补测完成（本地 CPU）：**test mAP50 0.5691 / 0.4009**（val→test +3.2，与基线 test 偏易一致）；四方表齐全；M5（M4采样+FasterNet 组合）组装完成并本地干跑验证（过采样 3936→5889、迁移 316/99/0、前向 OK），autodl/m5_train.py 待用户跑 |
| 2026-07-26 15:40 | **云端直连打通**：scripts/cloud.py（paramiko，密码仅环境变量内联、不落盘）可执行 status/exec/pull/push；M4 训练中（epoch 17/200，每轮 369 批 = 过采样生效）；以后结果由助手直接拉取分析，用户无需打包下载 |
| 2026-07-26 15:14 | 基线@200 终局：val 0.5729 / **test 0.5964**（157 轮早停 best@127，基线 100 轮已收敛）；M4（类别加权采样）开发完成并本地验证：sqrt 反比倍率封顶 5、稀有类 sitting104→416/drink147→446/active167→508、训练图 3936→5889、硬链接零磁盘、val/test 不动、模型零改动；autodl/m4_train.py 待用户跑（判决线：test≥0.61 且弱类 AP 升） |
| 2026-07-26 12:41 | M3@200 终局 mAP50 **0.5371**（续训 +2.95 点，欠训假说证实但未达 0.56 线）；参数确认 2.47M/6.5G（与本地预算一致）；每类 AP 暴露 sitting 0.233（28 实例）/active 0.372/standing 0.429——**M4 加权采样正当性进一步强化**；下一步：基线 200 轮 + M4 开发；M3 记为"部分有效" |
| 2026-07-26 12:12 | 明确提效技巧白名单（TTA/F1阈值/数据清洗/帕累托框架/每类AP/Grad-CAM/Nano实测）与黑名单（挑测试子集/test调参/报喜不报忧），用户认同；写入诚信边界 |
| 2026-07-26 11:53 | 评测协议 v2（用户要求防过拟合）：①训练后强制读 results.png 判过拟合 ②报告指标改以 held-out test 集为准（两个训练脚本已内置 val+test 双评估，新 MD5 已发用户）③外部验证+3 次重复保留；协议写入 README |
| 2026-07-26 11:43 | 立"文献先行审核规则"（定策略/开发前先调研代表论文对比方案）与"学术诚信边界"（只借鉴思想、明确引用、实验独立、避免单一论文雷同）（用户要求） |
| 2026-07-26 11:40 | 训练轮数文献调研定协议：**200 轮 + patience 30 为统一协议**（YOLO-11 综述/TalTech 实测 237 轮后递减/RSD-YOLO 300+50 等佐证）；M3 首轮结果 mAP50 0.5076（100 轮未收敛，75→100 仍 +3.6）；决定 M3 续训 +100 轮凑 200 验证欠训假说，基线按新协议重跑（autodl/baseline_train.py，200+patience30） |
| 2026-07-26 11:27 | M3 首轮训练进行中（用户报 70+ 轮未破 0.5）；诊断定性：**100 轮预算 + 半从零模块 = 结构性吃亏**（M2 终点仍在爬坡佐证，文献训 200-300 轮）；对策：m3_train.py 加续训功能（--weights/--lr0/--name，dry-run 验证通过），首轮跑完热重启续 50 轮凑满 150；基线后续也按 150 轮重跑保公平 |
| 2026-07-25 23:07 | 训练方法文献调研（WFE-YOLO 全文 + 不均衡综述）：**超参冻结用 ultralytics 默认**（对手全用默认）；路线图 v2——M4 定为**类别加权采样**（仿 YW-Dataset，模型无关最安全）、M3.1 FCGB 内嵌式（选做）、M5 紧凑检测头（效率主战场，对手参数-24% 在此）；笔记 paper/lit-review-training.md |
| 2026-07-25 22:06 | M3（FasterNet 轻量主干 v2）开发完成并两轮本地迭代：v1 expand=2 增肥被本地拦截（参数-2.5%/FLOPs+20.8%）→ v2 P2保留原版+expand=1 → **参数 2.48M(-5.6%)/FLOPs 6.59G(-0.3%)/迁移316键/前向OK**；autodl/m3_train.py dry-run 通过，待用户上 AutoDL 实跑；效率主张转向"Nano 实测 FPS"（PConv 内存访问优势） |
| 2026-07-25 21:35 | M2 终局否决（mAP50 0.4988，-7.2；未发散但收敛被拖慢，100 轮未追平）；三轮注意力实验全负 → **注意力路线正式关闭**；M2 三件套归档；战略转向 M3 FasterNet 轻量主干为一号创新点；AutoDL 首跑成功（流程跑通，成本 ~2 元/轮） |
| 2026-07-25 19:47 | 用户选定 **AutoDL** 为主训练平台；发现本机代理 127.0.0.1:7897 可用并直接下好数据集 `data/dataset.zip`（379MB，11252 条目完整）；新建 autodl/ 包（README 手册 + setup.sh + m2_train.py），m2_train.py 本地 dry-run 验证通过（448/57/0） |
| 2026-07-25 18:38 | 用户 Colab 免费额度跑一半耗尽（滚动约 24h 恢复，无固定时刻）；M2 笔记本升级为 **Drive 持久化 + 自动断点续训**（重跑自动从 last.pt 继续，进度不丢）；备选：AutoDL 付费约 2 元/h |
| 2026-07-25 17:00 | 废案归档至 archive/（M1/M1' 笔记本+配置、Kaggle 废案、单格备用版）；新建 archive/ARCHIVE.md 索引与 paper/problem-log.md 问题记录（P1-P6 论文素材） |
| 2026-07-25 16:38 | M1' 于 epoch37 叫停否决（0.338，落后 M1 同期 8 点）；两轮失败根因定性：**随机初始化乘法门控污染预训练特征**；建成 M2（EMAR 残差封装@P3，本地实跑验证通过：448键/缺失57/多余0、残差能量比2.25、前向OK），notebooks/colab_m2_emar.ipynb 待用户运行 |
| 2026-07-25 15:45 | 本地验证环境就绪（torch2.1.1+ultralytics8.4.105）；M1' 第4格逻辑本地实跑**全部通过**：权重迁移成功448键/缺失57键（EMA 6 + Detect分类头 51）/多余0，前向自检 OK（验证脚本 data/tmp/validate_m1p.py） |
| 2026-07-25 15:34 | 立"交付前审核三关"规则（用户要求）；开建本地 CPU 验证环境；修复 M1' 第 4 格三连错（下载/weights_only/Detect 形状过滤） |
| 2026-07-25 15:22 | 建立本文件；写入更新协议（实时更新 + 时间戳硬性规则） |
| 2026-07-25 14:59 | 项目迁入 E 盘；NEAU 放弃，定可信度四路线；建 colab_compare.ipynb |
| 2026-07-25 14:31 | M1 判决否决；建 M1' 修正版笔记本与配置；建 REVIEW_CHECKLIST.md |
| 2026-07-19 | 基线完成（mAP50 57.06%）；混淆矩阵诊断；建 EXPERIMENT_LOG |
