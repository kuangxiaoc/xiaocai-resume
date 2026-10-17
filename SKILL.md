---
name: xiaocai-resume
description: 根据职位描述（JD）从个人素材库生成针对性的 1 页 A4 LaTeX 简历 PDF。跨 agent（Claude Code / Codex / WorkBuddy）。首次使用会引导用户建立素材库 profile.yaml，之后按 JD 裁剪改写、手写 tex、编译校验出 PDF。
---

# Resume Builder

## 它做什么
输入 JD（文本或 URL）→ 定位用户素材库 → 筛选 + 改写 + 排序 → 手写
`resume.tex` → 编译校验 → 在当前工作空间输出
`output/<user>-<slug>-<日期>/resume.pdf`。

## 边界
- skill 本体（本目录）：契约 / 模板 / 脚本 / 文档，不含真实个人信息。
- 用户数据不放进 skill 本体。默认全局素材库位于
  `~/.agents/resume-builder/profiles/<user>/`；当前工作空间可以使用
  `profiles/<user>/` 覆盖或补充；生成结果始终位于当前工作空间的 `output/`。

## 核心原则

- Agent 负责理解 JD、做内容取舍、改写事实和判断质量；脚本只负责环境检查、目录创建和编译等机械动作。
- `profile.yaml` 是事实源。只能基于其中已有事实改写，不能为了匹配 JD 补写经历。
- 编译成功不等于简历完成。Agent 必须检查内容和页面，发现问题后继续修改并重新编译。
- 信息不足、事实依据不明确或存在多个合理方案时，先询问用户，不要猜测。

## 使用流程

### 0. 确认素材库

素材库放在用户目录，不随 skill 安装、也不随工作空间变化，因此跨工具、跨工作
目录都能读到同一份。定位用确定性脚本，不要靠猜路径：

```bash
node <skill>/scripts/resume.mjs find-profile [<user>]
```

退出码含义：`0` = 唯一命中；`1` = 未找到（脚本会列出已存在的素材库标识）；
`2` = 工作空间与全局各有一份，必须先问用户本次用哪一个。不传 `<user>` 时只做
存在性探测并列出标识。

定位优先级（脚本已实现，agent 不得偏离）：

1. 用户明确指定的 profile 路径；
2. 当前工作空间的 `profiles/<user>/profile.yaml`；
3. 全局素材库 `~/.agents/resume-builder/profiles/<user>/profile.yaml`；
4. 用户明确提供的其他简历、资料或 PDF 路径。

不要把个人资料复制到 skill 安装目录。当前工作空间的 profile 可以是全局 profile
的派生版本，用于不同岗位方向；不要静默合并互相冲突的资料。
如果上述位置都没有可用素材，才引导建立素材库。

#### 建立素材库

1. 询问用户粘贴个人经历，或提供旧简历、资料文件或 PDF 路径。
2. 询问用户希望保存到当前工作空间，还是全局目录
   `~/.agents/resume-builder/profiles/<user>/`。用户未指定时，优先建议全局目录，
   以便其他工作空间复用。
3. 按 `contracts/profile.schema.json` 整理为选定目录下的 `profile.yaml`，包含
   `meta`、`summary`、`education`、`experience`、`projects`、`skills`、
   `awards`、`open_source` 等字段；论文专利进 `publications`，暂不归类的进
   `extras`。不必一次填全，缺的字段先空着。
4. 为经历和 bullet 添加 `tags`（例如 `llm`、`backend`、`rag`、`python`）。
   tags 是自由文本，没有受控词表；用词一致性靠复用已有 tag 维持，不做拼写校验。
5. 请用户提供证件照，放在所选 profile 目录；没有照片时可以先不放。
6. 可选执行 `node <skill>/scripts/resume.mjs check-profile <profile.yaml>`
   （内部转发给 `check_profile.py`，检测不到 Python 时自动跳过）。
   它只校验字段存在性，不校验内容质量，也不会因缺可选字段报错。

#### 追加素材（已有素材库时）

素材库是长期累积的，不是一次填完。用户随时会说「加点东西」，此时：

1. 如果用户给了明确位置，直接写进对应 profile；只给素材内容时，agent 按
   `contracts/profile.schema.json` 判断归属字段后写入，并告知落在哪个字段。
2. 归属判断不清时，放进 `extras`（`type` 自由描述），不要新造顶层字段——
   顶层虽允许扩展，但只有 schema 里声明的字段才会被稳定读取。
3. 证明材料（论文 PDF、报告）放进所选 profile 目录的 `attachments/`，并在
   `attachments` 清单登记文件名；论文同时在 `publications` 里记一条，
   `status` 写当前真实状态。
4. 追加后重跑 `check-profile` 确认结构没写坏；写入位置与原素材冲突时先问用户。

### 1. 环境自检

执行：

```bash
node <skill>/scripts/resume.mjs check-env
```

如果失败，按照脚本输出安装最小编译环境（系统级安装先告知用户），安装后
重新执行。不得跳过失败的环境检查。

生成 `resume.tex` 时，用 `check-env` 输出里的“推荐字体”替换模板中的
`<CJK_FONT>`。字体是否可用只能以实际探测为准，不要按操作系统假设。

### 2. 获取并分析 JD

询问目标岗位的 JD 文本或 URL。URL 无法访问时请用户粘贴文本。读取
`profile.yaml`，先提取岗位名称、公司名称、核心能力、必备技术栈、加分项、
业务领域、经验要求和语言要求，并区分“必须匹配”“强相关”“可选加分”。

从素材库筛选并排序相关条目。优先选择能直接证明岗位核心能力、技术匹配度高、
成果清晰、与岗位相关且能在一页内表达的经历；不要单纯按关键词命中数量排序。
替换 `skeleton.tex` 中的 `<POSITION_LINE>`。

### 3. 改写内容

允许调整句式、合并同一经历中的已有事实、重排 bullet，以及使用 JD 中更准确
的同义术语。禁止增加素材库中不存在的技术栈、指标、职责、团队规模、时间、
公司或项目事实；不得把“参与”改成“负责”，把“协助”改成“主导”，或把课程
项目改成商业项目。

对每条最终 bullet 反向核对：其中每个事实是否都能在 `profile.yaml` 找到依据。
无法确认时删除该表述或询问用户。

### 4. 生成并编译

1. 用脚本创建输出目录：
   `node <skill>/scripts/resume.mjs new-output <user> <slug>`
2. 参考 `templates/skeleton.tex` 和 `contracts/latex-rules.md`，手写
   `output/.../resume.tex`。
   如果素材库来自全局目录，照片和附件引用必须使用从当前输出目录指向
   `~/.agents/resume-builder/profiles/<user>/` 的正确路径；不要复制整份素材库。
3. 编译：
   `node <skill>/scripts/resume.mjs build output/.../resume.tex`
4. 校验：
   `node <skill>/scripts/resume.mjs validate output/.../resume.pdf`

脚本失败时必须读取错误信息或日志，修复 `resume.tex` 或环境后重跑，不能跳过
或隐瞒。脚本只提供基础编译证据，不替代 Agent 的内容判断。

### 5. Agent 自检与迭代

编译后，Agent 必须检查：

- PDF 确实生成、可打开且为 1 页 A4；
- 姓名、联系方式、目标岗位、教育经历和核心经历完整且正确；
- 没有残留占位符、空字段、异常符号或未经素材支持的表述；
- 高相关经历优先，内容没有重复，页面没有溢出、大面积空白或明显拥挤；
- 中英文、数字、字体和层级清晰可读。

如果结果不合格，按 `contracts/latex-rules.md` 第 6 节的顺序迭代：删除低相关
经历，删除或合并重复 bullet，缩短低价值描述，减少非核心技能，最后才调整间距
或字号。每次修改后重新编译并重新检查；不得用极端缩小字号掩盖内容过多。
`summary` / `awards` / `open_source` / `publications` / `extras` 默认不进简历，
除非直接命中岗位核心要求——素材库字段多不等于要渲染的内容多。

### 6. 交付

告知用户生成的 PDF 路径。匹配分析默认不主动输出；用户需要时再提供
“命中 / 不足 / 建议”三段分析。

## 需要询问用户的情况

- 所有候选位置都没有 `profile.yaml`，且用户尚未提供足够素材；
- 存在多个 profile，但无法确定本次使用哪一个；
- 需要在当前工作空间 profile 和全局 profile 之间选择或合并；
- JD URL 无法访问，且用户没有提供 JD 文本；
- 岗位名称、用户标识或目标语言无法确定；
- 素材与 JD 关联很弱，或某条表述的事实依据不足；
- 用户要求加入素材库中不存在的技术、指标或经历（应先写入素材库再使用）；
- 用户追加素材，但归属字段不唯一、或与已有素材冲突；
- 一页内存在多个合理取舍，Agent 无法依据相关性和证据强度做出唯一选择。

## 护栏
- 不改 `templates/resume.cls`，也不擅自覆盖用户已有 profile。
- 不手写 output 目录名或日期，必须使用 `new-output` 子命令。
- 不编造经历或数据，只改写素材库中的事实。
- 不新造 schema 之外的顶层字段；无法归类的素材放 `extras`。
- 不删除用户已积累的素材，只按 JD 决定本次简历是否呈现。
- 必须 1 页 A4。
- 默认不输出 `age`、`gender` 等非必要个人信息，除非用户明确要求。
- 不把全局素材库复制到 skill 仓库或当前输出目录；只按需引用照片和附件。

## 依赖
脚本层需要 **Node.js**（纯标准库，无第三方依赖），macOS / Linux / Windows 原生终端均可运行。
最小编译环境：`xelatex` 引擎 + 中文宏包 `ctex`/`xeCJK`/`xeCJKfntef`/`zhnumber` + 中文字体（见 1.5 的平台字体表）。先跑 `node <skill>/scripts/resume.mjs check-env` 自检，缺啥按指引装。`check_profile.py` 可选依赖 `pyyaml`（经 `check-profile` 子命令转发，无 Python 时自动跳过）。
