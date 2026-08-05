# 论文写作规范手册（本项目专用，2026-08-03）

## 一、AI 审查怎么过（合规正道，不是躲检测）

### 政策底线（已核实）

- MDPI/Frontiers：AI 工具**不能署名作者**；实质性使用须在 **Acknowledgments 和 Materials/Methods 声明**；作者对全部内容负责
- 期刊查重普遍要求 <15%（优质刊 <10%）；部分已加 AIGC 率检测
- 结论：**可以合法用 AI 辅助，必须声明，内容必须真实**

### 我们的天然优势（诚实资本）

本文全部数字、图表、失败记录、问题排查均出自真实实验（见 EXPERIMENT_LOG / problem-log），
不存在"编数据"空间——**内容真实是过一切审查的根**。

### 写作分工（防 AI 腔）

1. 助手基于真实素材起草（数字一律来自实验日志，禁止编造）
2. **用户通读改写一遍**：换成自己的表达习惯、删掉读不懂的句子——这是 humanize 的本质
3. AI 腔特征黑名单（见一条删一条）：
   - 空洞排比："not only... but also..." / "plays a crucial role in..."
   - 过渡词堆砌：Moreover/Furthermore/In addition 连用
   - 无信息强调句："It is worth noting that..."（要么删要么给实质内容）
   - 过长定语从句、每个段落结构雷同
4. 投稿前用 iThenticate/AIGC 工具自测一遍，但别为指标反向注水

## 二、结构与各章要点（IMRaD）

| 章 | 要点 |
|---|---|
| Abstract | 四要素：痛点 → 方法 → 关键数字（test mAP/FPS）→ 部署意义；≤200 词；不写正文没有的数字 |
| Introduction | 漏斗：猪行为监测意义 → 现有工作 → 缺口（重模型/弱类/部署）→ 本文三贡献 |
| Related Work | 用自己的话综述；引 30–50 篇，近 3 年占一半；引目标期刊论文 2–3 篇 |
| Methods | 可复现为准：数据集（来源/许可/QC/切分策略+压力测试披露）→ 基线 → 模块（配图）→ 训练协议 |
| Results | 只摆事实：消融表、对比表、每类 AP、曲线、Grad-CAM；不评论 |
| Discussion | 意义 + 泛化分析（序列/跨场两档证据）+ Limitation（sitting 样本少、跨场退化）+ Future Work |

## 三、文字与格式规范

- **时态**：Methods/Results 过去时；Introduction 现状/普遍事实现在时；Conclusion 现在时
- **数字**：mAP 统一保留 1 位小数（%）；均值±标准差格式统一；全文同一指标精度一致
- **图表**：caption 自明（不看正文能懂）；表格用三线表；图 ≥300dpi；图中字号 ≥8pt 且全篇一致
- **术语**：全文统一（behaviour/behavior 选一种拼写；dataset/data set 统一）
- **引用格式**：按期刊模板（MDPI 用数字编号）；只用 Zotero 管理，杜绝手打

## 四、必备声明段（MDPI 模板，一个不能少）

- Author Contributions / Funding / Institutional Review Board（用"仅公开数据无动物干预"那句）
- Informed Consent / **Data Availability**（数据集+代码链接）/ Conflicts of Interest / **AI 使用声明**

## 五、投稿时特别注意

1. **Cover Letter 主动披露**切分策略与压力测试（审稿团 R1-1 防线，别等被揪）
2. 导师通讯作者身份、单位英文名称、ORCID 提前备齐
3. 投前跑一遍模拟审稿团终审（REVIEW_BOARD.md 流程）
4. 一稿一投，别同时投多家

## 六、JRTIP 硬规则（2026-08-04 调研自官方投稿指南原文）

1. **12 页上限**（双栏、含参考文献与作者 bio）——超页直接退稿不进审稿。投稿排版目标：≤8 图 ≤6 表
2. **引用：数字编号 [1]**，按出现顺序连续编号；Springer Basic 格式（姓前名后、作者后冒号、刊名 ISSN LTWA 缩写、年份句末括号）；**DOI 有则必给**（full link 形式）
3. **Cover Letter 必须说明解决了什么 real-time 问题**；"只报处理时间/速度不算充分讨论实时性"——Jetson 部署、延迟、功耗是核心素材
4. **图规范**：矢量 EPS 优先（线图 ≥1200 dpi、半色调 ≥300 dpi、组合 ≥600 dpi）；图内 Helvetica/Arial 2–3 mm；图内不得放标题；图宽单栏 84 mm / 通栏 174 mm；图题写正文里、粗体 Fig. + 编号（无点后缀）、末尾无句号；在线彩图免费，但转灰度后须仍可辨（线型/纹理不止靠颜色，对比度 ≥4.5:1）
5. **表规范**：阿拉伯编号、表题在表上方、表注上标小写字母
6. **作者 bio 必需**（计入 12 页）
7. LaTeX 投稿用 Springer Nature 模板 sn-jnl.cls + [iicol] 双栏 + 数字型 bst

## 七、备选刊格式差异（转投时必须切换）

- **INMATEH**：著者-年份制 (Werner et al., 2005)；文献表按字母序带 [n]；≥10 篇且 ≥3 篇近 3 年；摘要和结论禁引用；≤10 页单栏 Arial 10pt；**"同一数据不得同时以表和图呈现"**（我们的图1/4/10 与对应表须二选一）
- **Ecological Informatics**（Elsevier，冲刺）：著者-年份制，与 JRTIP 数字制不兼容——建议用 Zotero/BibTeX 管理文献以便一键切换
