# FLOWSTATE

一个零预算的双语（中文 / English）个人站点，由两条内容线组成：**汽车**与**文学**。
静态生成、暗色极客编辑风、无后端。

> A zero-budget bilingual personal site by **Sayo//n4ra**, in two tracks —
> **automotive writing** and **fiction**. Static, dark, minimal-editorial, no backend.

---

## 0. 两条内容线 / Two tracks

| | 汽车 Automotive | 文学 Fiction |
| --- | --- | --- |
| 路由 | `/zh/automotive/` · `/en/automotive/` | `/zh/fiction/` · `/en/fiction/` |
| 内容 | 汽车文化、改装研究、驾驶体验、车辆测评、随笔 | 同人文、短篇小说、微型小说、连载 |
| 强调色 | 铜金 `#c98b52` | 冷蓝灰 `#8f9dd0` |
| 版式 | 横向摄影比例、杂志网格 | 竖向书籍比例、衬线长文 |
| 特殊 | — | 同人声明、内容分级、单语言作品 |

两条线共用同一套页头、导航、语言切换与页脚；切换时只替换强调色与排版细节。

---

## 1. 技术栈 / Stack

| 项 | 选择 | 原因 |
| --- | --- | --- |
| 框架 | **Astro 6**（静态输出） | 默认零 JS、构建快、Markdown 原生支持 |
| 语言 | **TypeScript**（strict） | 内容模型有类型校验 |
| 内容 | **Markdown + 内容集合（zod 校验）** | 写作只写 `.md`，不碰模板 |
| 样式 | **原生 CSS**（自定义属性 + 组件级 scoped style） | 无 Tailwind、无 CSS-in-JS |
| 字体 | Google Fonts（Archivo / Inter / JetBrains Mono），本地回退 | 免费；断网自动回退系统字体 |
| 包管理 | pnpm（配合 Node 24） | 安装快、锁文件严格 |
| 成本 | **0 元** | 开源工具 + 免费静态托管 |

运行时依赖只有 Astro 一个包。

---

## 2. 目录结构 / Structure

```
automotive-journal/
├─ astro.config.mjs          # 站点配置（site、markdown、构建格式）
├─ dev.ps1                   # 本机免 PATH 的一键启动脚本
├─ package.json
├─ pnpm-workspace.yaml       # pnpm 布局与构建脚本白名单
├─ tsconfig.json
├─ public/
│  ├─ favicon.svg
│  └─ images/placeholder-0*.svg   # 自制占位图，无第三方素材
├─ scripts/
│  ├─ shot.mjs               # 开发辅助：按真实移动视口截图（可选）
│  └─ pdf2md.py              # PDF / Word → Markdown 导入工具
└─ src/
   ├─ content.config.ts      # 两个内容集合的 schema
   ├─ content/
   │  ├─ automotive/zh/*.md  ├─ automotive/en/*.md
   │  ├─ fiction/zh/*.md     └─ fiction/en/*.md
   ├─ layouts/Base.astro     # 页头 / 导航 / 语言切换 / 页脚
   ├─ components/
   │  ├─ ArticleCard.astro   # 汽车文章卡片
   │  └─ StoryCard.astro     # 小说卡片（含分级角标）
   ├─ lib/
   │  ├─ site.ts             # 站名、标语、作者、栏目常量
   │  ├─ i18n.ts             # 双语字典、汽车栏目、文学体裁
   │  └─ articles.ts         # 读取、排序、字数、日期、译文查找
   ├─ pages/
   │  ├─ index.astro         # / → 302 到 /zh/
   │  └─ [lang]/
   │     ├─ index.astro                    # 双栏目入口首页
   │     ├─ automotive/index.astro         # 汽车列表 + 栏目筛选
   │     ├─ automotive/[slug].astro        # 汽车文章
   │     ├─ fiction/index.astro            # 书架 + 体裁筛选
   │     ├─ fiction/[slug].astro           # 小说阅读页
   │     └─ about/index.astro              # 关于
   └─ styles/global.css      # 设计令牌 + 基础样式（含文学配色）
```

---

## 3. 本地运行 / Run locally

### 3a. 本机直接运行（推荐，无需配置环境变量）

本机的 Node 与 pnpm 由 DSH 内置运行时提供，**不在系统 PATH 里**，直接敲 `pnpm dev` 会报错。
仓库根目录的 `dev.ps1` 会自动使用内置运行时：

```powershell
cd C:\Users\admin\Documents\deepseek-harness\default-workspace\automotive-journal
.\dev.ps1              # 启动开发服务器 → http://localhost:4321
.\dev.ps1 build        # 生产构建，输出到 dist\
.\dev.ps1 preview      # 预览已构建的 dist\
.\dev.ps1 install      # 首次/重新安装依赖
```

如果提示「禁止运行脚本」，或担心当前目录不对，用绝对路径调用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\admin\Documents\deepseek-harness\default-workspace\automotive-journal\dev.ps1" dev
```

> 脚本不改 PATH、不全局安装任何东西。开发服务器固定绑定 `127.0.0.1`
> （Astro 在 Windows 上默认只监听 `[::1]`，会导致 `127.0.0.1:4321` 打不开）。

### 3b. 在你自己的机器上（已装 Node + pnpm）

```bash
cd automotive-journal
pnpm install
pnpm dev            # http://localhost:4321
pnpm build          # 输出到 dist/
pnpm preview
```

> `pnpm-workspace.yaml` 已显式允许 `esbuild` 与 `sharp` 的安装脚本（pnpm 默认拦截）。
> 若克隆后提示 `Ignored build scripts`，运行 `pnpm approve-builds` 允许这两个包。

---

## 4. 写内容 / Authoring

> **想直接开始写？** 跳到 [4.0 投稿工作流](#40-投稿工作流--the-authoring-loop)。
> 下面的 4.1 / 4.2 是字段说明，工具会自动帮你填好。

### 4.0 投稿工作流 / The authoring loop

日常只有四步，都能用一条命令完成：

```powershell
cd C:\Users\admin\Documents\deepseek-harness\default-workspace\automotive-journal

# ① 新建一篇（自动生成 frontmatter，默认 draft: true 不会发布）
python scripts/newpost.py new --track fiction --type shortstory --lang zh --title "我的新短篇"

# ② 用编辑器打开生成的 .md，写入正文、补上 dek（简介）
#    文件位置会打印出来，例如 src\content\fiction\zh\my-new-story.md

# ③ 修改元数据（标题 / 简介 / 分级 / 标签…）
python scripts/newpost.py edit my-new-story --dek "一句话简介" --tags "小说,都市" --rating T

# ④ 发布并推送
python scripts/newpost.py publish my-new-story
.\publish.ps1 -Push
```

**`publish.ps1` 会做什么**（顺序固定，任一步失败就停下，绝不半途发布）：

1. 检查全部文章的 frontmatter、编码、章节重复；
2. 构建站点 —— 构建失败就不继续；
3. 列出**仍是草稿**的文章，避免你以为发了其实没发；
4. 加 `-Push` 时才提交并推送；不加则只在本地验证。

### 4.0b 常用命令速查

```powershell
# 看所有文章的状态（LIVE / draft）
python scripts/newpost.py list

# 只看文学 / 只看中文
python scripts/newpost.py list --track fiction --lang zh

# 看某一篇的完整内容
python scripts/newpost.py show leviathan-ch3

# 连载新章节（part 自动编号，支持 12.5 这种小数）
python scripts/newpost.py new --track fiction --type serial --series leviathan `
    --part 14 --lang zh --title "第十四章标题"

# 用现成的正文文件替换（会自动去掉 BOM）
python scripts/newpost.py edit my-story --body .\草稿.md

# 临时下架（改回草稿，不会删除文件）
python scripts/newpost.py unpublish my-story

# 只检查不修改
python scripts/newpost.py lint
```

### 4.0c 编辑已有文章的两种方式

| 场景 | 做法 |
| --- | --- |
| 改**正文** | 直接用编辑器改 `.md` 文件（推荐；保留全部格式） |
| 改**元数据** | 用 `python scripts/newpost.py edit <slug> --某字段 "新值"`，只动那一个字段，其余原样保留 |
| 整体替换正文 | `edit <slug> --body 新正文.md` |

`<slug>` 支持模糊匹配：写 `ch12` 就能找到 `leviathan-ch12.md`；
如果匹配到多篇，工具会列出来让你写完整些，**不会猜**。

### 4.1 汽车文章

放进 `src/content/automotive/zh/` 与 `src/content/automotive/en/`，同名 `.md`：

```markdown
---
title: "标题（含特殊字符时务必加引号）"
dek: "一句话摘要"
published: 2026-10-01
category: culture        # culture | modification | driving | review | essay
tags: [标签1, 标签2]
image: /images/your-photo.webp
imageAlt: "图片说明（可访问性必需）"
featured: false
draft: false
translationKey: my-slug  # 中英共用一个 key，语言切换才能互跳
---

正文 Markdown。
```

### 4.2 文学（同人 / 原创）

放进 `src/content/fiction/zh/` 或 `src/content/fiction/en/`：

```markdown
---
title: "深夜回程的第三站"
dek: "一句话简介（会显示在卡片与详情页顶部）"
published: 2026-10-12
genre: shortstory        # fanfiction | shortstory | flash | serial
nature: fanwork          # fanwork（同人，显示声明）/ original（原创）
fandom: "原作名"          # 仅 nature: fanwork 时填写
rating: T                # G | T | M | E → 显示分级角标与提示
status: complete         # complete | ongoing
series: "系列名"          # 可选，多篇同系列会标注
part: 1                  # 可选，第几部分
tags: [都市, 夜行]
image: /images/your-cover.webp
imageAlt: "封面说明"
featured: true
draft: false
translationKey: night-platform   # 可选！不填就是单语言作品
---

正文。
```

**同人作品的自动声明**：只要 `nature: fanwork`，阅读页就会显示非商业声明块
（角色与世界观版权归原作者），并在卡片上打「同人」标记。这不是可选项，是有意固化的。

### 4.3 关于译文可选

`translationKey` 在文学集合里是**可选**的。规则：

- 填了 `translationKey` 且另一语言存在同 key 作品 → 语言切换直接跳过去；
- 只有一种语言，或另一语言没有同 key → 语言切换落到该语言的**书架首页**，
  并在作品页显示「这篇暂时只有中文/英文版本」。

不会出现 404。这也是为什么中文作品不会出现在英文站列表里。

### 4.4 从 PDF / Word 导入已有文章

已有作品存在 PDF 里时，不用手打。`scripts/pdf2md.py` 会提取正文、
重建段落、并生成带好 frontmatter 的 `.md`：

```powershell
# 先预览，不写文件
python scripts/pdf2md.py 我的小说.pdf --track fiction --lang zh --slug my-story --dry-run

# 确认无误后正式写入 src/content/fiction/zh/my-story.md
python scripts/pdf2md.py 我的小说.pdf --track fiction --lang zh --slug my-story
```

参数说明：

| 参数 | 说明 |
| --- | --- |
| `--track` | `fiction` 或 `automotive` |
| `--lang` | `zh` 或 `en` |
| `--slug` | 输出文件名（不含扩展名）；不填则从标题自动生成 |
| `--title` | 手动指定标题（覆盖自动识别） |
| `--dry-run` | 只打印结果，不写文件 |

**它的行为**：
- PDF 用**位置感知**提取（读取每行 y 坐标），用行距判断段落分隔，否则 PDF 会把所有段落压成一整块；
- 自动识别首行标题，并在生成时移入 frontmatter；
- 生成的文件默认 `draft: true`，**不会立刻发布**；
- 已存在同名文件时**拒绝覆盖**。

**限制**：只支持文字版 PDF。扫描件（图片型 PDF）提不出文字，脚本会明确报错并建议先 OCR。
导入后请务必通读一遍——诗歌、对话、列表的换行可能仍需手动调整。

依赖：`pip install pypdf python-docx`（本机已装好）。

### 4.4b 导入整本多章小说（重要）

单篇用上面的 `pdf2md.py`；**有章节结构的长篇用 `novel_import.py`**，它一次生成每章一个文件。

```powershell
# 预览：列出识别到的章节与字数，不写文件
python scripts/novel_import.py 利维坦.pdf --series leviathan --title 利维坦 --dry-run

# 正式写入 src/content/fiction/zh/leviathan-ch1.md … ch13.md
python scripts/novel_import.py 利维坦.pdf --series leviathan --title 利维坦 --write
```

`--series` 是文件名前缀，同一部作品的各章共用同一个 `series` 值，
书架会自动把它们**合并成一个作品**并生成章节目录，而不是铺满十几张封面。

**导入器处理的四个真实坑（都已在 `利维坦` 上验证）**：

| 问题 | 现象 | 处理 |
| --- | --- | --- |
| 部首替换 | 门→`⻔`、车→`⻋`、风→`⻛` 等 22 个字 | `repair_cjk.py` 逐字映射 + 校验，全篇 4059 处修复为 0 残留 |
| NFKC 连带破坏标点 | 全角 `，：（）…` 被转成半角 | 只对部首字符做 NFKC，并校验标点数不减少 |
| 段落全部粘连 | 章节开头的「地点／时间」粘进正文 | 场景标签独立成段并渲染为斜体 slug 块 |
| 文本顺序错乱 | 按 y 坐标排序反而倒序 | 改用 pypdf 默认提取顺序 |

**质量校验**：导入后 1439 行原文中只有 27 行未出现在正文里，且全部是章节标题行
（已移入 frontmatter）。**正文零丢失。**

### 4.4c 连载作品的排序与导航

- `series` 为同一部作品名（不要带“第1部/第2部”，否则会被当成两部作品）；
- `part` 决定章节顺序，是**小数**类型，所以 12 与 13 之间可以插一章 `12.5`；
- 章节目录在书架封面下，阅读页底部有「上一章 / 下一章」。

### 4.5 关于图片

- 只使用**你自己拍摄/绘制或已获授权**的图片。仓库里的 `placeholder-*.svg` 均为自制矢量占位图。
- 放进 `public/images/`，用 `/images/文件名` 引用，不要外链热链。
- 建议宽 ≥ 1600px，使用 WebP/AVIF 控制体积。

---

## 5. 设计约定 / Design tokens

全部集中在 `src/styles/global.css`：

| 令牌 | 值 | 用途 |
| --- | --- | --- |
| `--bg` / `--bg-sunken` | `#0a0a0a` / `#060607` | 主背景 / 页脚与代码块 |
| `--ink` / `--ink-muted` / `--ink-faint` | `#ececec` / `#9a9a9f` / `#6b6b70` | 正文 / 次级 / 弱化 |
| `--accent` | `#c98b52`（铜金） | **默认（汽车）强调色** |
| `--accent`（fiction） | `#8f9dd0`（冷蓝灰） | 由 `body[data-track='fiction']` 覆盖 |
| `--font-display` | Archivo 900 | 冲击力标题 |
| `--font-mono` | JetBrains Mono | 元信息、编号、标签 |
| `--font-serif` | Iowan / Georgia / 宋体 | 导语、小说正文标题 |

原则：**除图片外不堆砌车辆元素**。秩序来自编号（`01 —`）、细分割线与等宽元信息。
小说页刻意换用衬线体、更宽行高与居中的场景分隔符——是阅读，不是扫描。

### 霓虹系统 / Neon

只在**汽车板块**启用，走 Speedhunters 那类「克制的边缘光」路线，不是夜店招牌。
主色：紫罗兰 `#a855f7` + 电青 `#22d3ee`。

| 开关 | 位置 | 作用 |
| --- | --- | --- |
| `FEATURES.neon` | `src/lib/site.ts` | 全站开关，设 `false` 即完全关闭 |
| `--neon-boost` | `global.css` | 强度系数，`0` 关闭 / `1` 正常 |
| `data-track` | `<body>` | 只有 `automotive` 打开，文学与关于页为 0 |
| `prefers-reduced-motion` | 系统设置 | 用户开启减弱动效时自动关闭 |

所有发光效果都乘以 `--neon-boost`，所以关闭时**渲染结果与纯设计完全一致**，
不会有残留边框或空阴影。新增组件想用霓虹，套现成工具类即可：

```html
<h1 class="neon-text">标题</h1>          <!-- 文字光晕 -->
<a class="neon-frame">…</a>              <!-- 图片边框光，悬停才出现 -->
<span class="neon-chip">T</span>         <!-- 发光小标签 -->
```

### 功能开关 / Feature flags

`src/lib/site.ts` 的 `FEATURES` 对象集中管理未来功能的开关，
已预留 `readingProgress`、`prevNext`、`rss`、`wordCountOnCards`。
再加新开关时**只改这里**，不要在各组件里散落条件判断。

---

## 6. 建库与部署 / Publish

“建库”指把本地代码放到网上，让别人能访问。**只需做一次**，之后每次投稿自动更新。

### 第一步：在 GitHub 建仓库（你自己操作，约 2 分钟）

1. 打开 <https://github.com/new>
2. **Repository name** 填 `flowstate`（或任何你喜欢的名字）
3. 可见性选 **Public**（免费托管 Pages 需要公开仓库）
4. **不要**勾选 “Add a README file” / “Add .gitignore”（本地已有，会冲突）
5. 点 **Create repository**，复制页面上显示的仓库地址，形如
   `https://github.com/<用户名>/flowstate.git`

### 第二步：把本地代码推上去（把地址发我，我来做）

```powershell
$Git = "C:\Users\admin\.tools\git\cmd\git.exe"
& $Git remote add origin https://github.com/<用户名>/flowstate.git
& $Git push -u origin main
```

> 首次推送会弹出 GitHub 登录窗口。**密码那一栏要填 Personal Access Token**，
> 不是账户密码（GitHub 早已不支持密码推送）。生成方式：
> GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
> → Generate new token → 勾选 `repo` → 复制生成的字符串。

### 第三步：让 Cloudflare 自动发布（推荐）

登录 Cloudflare 后：

1. **Workers & Pages** → **Create** → **Pages** → **Connect to Git**
2. 授权并选择 `flowstate` 仓库
3. 构建设置填：
   | 项目 | 值 |
   | --- | --- |
   | Framework preset | **Astro** |
   | Build command | `pnpm build` |
   | Build output directory | `dist` |
   | 环境变量 | `NODE_VERSION` = **22**（重要，默认版本可能太旧） |
4. **Save and Deploy**

几分钟后你会得到 `https://flowstate-xxx.pages.dev`。之后**每次 `.\publish.ps1 -Push`，
Cloudflare 会自动重新构建并上线**，不需要再手动操作。

### 第四步：改掉占位域名（部署后做一次）

`astro.config.mjs` 里的 `site` 目前是 `https://example.github.io`，
换成你的真实地址（例如 `https://flowstate-xxx.pages.dev`），否则分享链接和 SEO 会指向错误域名。

### 备选：GitHub Pages

不想用 Cloudflare 的话：仓库 **Settings → Pages → Source 选 GitHub Actions**，
再添加 Astro 官方 workflow（<https://docs.astro.build/en/guides/deploy/github/>）。
若仓库名不是 `<用户名>.github.io`，还要在 `astro.config.mjs` 加 `base: '/flowstate/'`。

> `*.pages.dev` / `*.github.io` 子域名足够起步，**无需购买域名**。

---

## 6b. 日常投稿（部署完成后）

```powershell
python scripts/newpost.py new --track fiction --type shortstory --lang zh --title "..."
# 写正文、补 dek
python scripts/newpost.py publish <slug>
.\publish.ps1 -Push          # 检查 → 构建 → 推送 → Cloudflare 自动上线
```

网站通常 **1～2 分钟**内更新。想先本地看效果：`.\dev.ps1 dev`。

---

## 7. 已知限制

- **Git 安装**：本机原本没有 Git，已装便携版 MinGit 到 `C:\Users\admin\.tools\git`，
  未改全局 PATH 与全局 git 配置。用法：
  ```powershell
  & "C:\Users\admin\.tools\git\cmd\git.exe" status
  ```
- **内容均为占位**：所有文章与小说都是版式示例，不是真实测评，也不是已发表作品。
- **`site` 仍是占位**：`astro.config.mjs` 里是 `https://example.github.io`，部署前必须改。
- **字体需联网**：Google Fonts 失败时回退系统字体，不影响可用。
- **未包含**（按需求刻意省略）：数据库、登录、评论、会员、付费 API、统计脚本。

---

## 8. 版权与同人声明

- 代码可自由用于个人项目。
- 文章、小说与自制图片版权归 **Sayo//n4ra** 所有。
- 同人作品为非商业创作，所涉原作角色与世界观版权归原作者及权利方所有，本站不主张所有权。
- 本仓库不包含任何第三方受版权保护的图片、文章或商标。
