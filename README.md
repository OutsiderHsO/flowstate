# AUTOMOTIVE JOURNAL

一个零预算的双语（中文 / English）个人汽车文化博客。静态生成、暗色极客编辑风、无后端。

A zero-budget, bilingual personal automotive-culture journal. Static, dark, minimal-editorial, no backend.

---

## 1. 技术栈 / Stack

| 项 | 选择 | 原因 |
| --- | --- | --- |
| 框架 | **Astro 6**（静态输出） | 默认零 JS、构建快、Markdown 原生支持 |
| 语言 | **TypeScript**（strict） | 内容模型有类型校验 |
| 内容 | **Markdown + 内容集合（zod 校验）** | 写文章只写 `.md`，不需要碰模板 |
| 样式 | **原生 CSS**（自定义属性 + 组件级 scoped style） | 无 Tailwind / 无 CSS-in-JS，依赖最少 |
| 字体 | Google Fonts（Archivo / Inter / JetBrains Mono），本地回退 | 免费；断网时自动回退系统字体 |
| 包管理 | pnpm（配合 Node 24） | 安装快、锁文件严格 |
| 成本 | **0 元** | 开源工具 + 免费静态托管 |

运行时依赖只有 Astro 一个包。

---

## 2. 目录结构 / Structure

```
automotive-journal/
├─ astro.config.mjs          # 站点配置（site、markdown、构建格式）
├─ package.json
├─ pnpm-workspace.yaml       # pnpm 布局与构建脚本白名单
├─ tsconfig.json
├─ public/
│  ├─ favicon.svg
│  └─ images/placeholder-0*.svg   # 自制占位图，无第三方素材
├─ scripts/
│  └─ shot.mjs               # 开发辅助：按真实移动视口截图（可选）
└─ src/
   ├─ content.config.ts      # 内容集合 schema
   ├─ content/journal/
   │  ├─ zh/*.md             # 中文文章
   │  └─ en/*.md             # 英文文章
   ├─ layouts/Base.astro     # 页头 / 导航 / 语言切换 / 页脚
   ├─ components/ArticleCard.astro
   ├─ lib/
   │  ├─ site.ts             # 站点名、标语、作者
   │  ├─ i18n.ts             # 双语字典 + 栏目定义
   │  └─ articles.ts         # 读取、排序、阅读时长、日期格式化
   ├─ pages/
   │  ├─ index.astro         # / → 302 到 /zh/
   │  └─ [lang]/
   │     ├─ index.astro      # /zh/ /en/  首页
   │     ├─ journal/index.astro        # 文章列表 + 栏目筛选
   │     ├─ journal/[slug].astro       # 文章详情
   │     └─ about/index.astro          # 关于
   └─ styles/global.css      # 设计令牌 + 基础样式
```

---

## 3. 本地运行 / Run locally

前置：Node.js ≥ 22（本项目在 v24 上验证），pnpm ≥ 10。

### 3a. 本机直接运行（推荐，无需配置环境变量）

本机的 Node 与 pnpm 由 DSH 内置运行时提供，**不在系统 PATH 里**，所以直接敲 `pnpm dev`
会报 `无法将"pnpm"项识别为 cmdlet`。仓库根目录已附 `dev.ps1`，它会自动使用内置运行时：

```powershell
cd C:\Users\admin\Documents\deepseek-harness\default-workspace\automotive-journal

.\dev.ps1              # 启动开发服务器 → http://localhost:4321
.\dev.ps1 build        # 生产构建，输出到 dist\
.\dev.ps1 preview      # 预览已构建的 dist\
.\dev.ps1 install      # 重新/首次安装依赖
```

如果提示「禁止运行脚本」，改用：

```powershell
powershell -ExecutionPolicy Bypass -File .\dev.ps1
```

> 脚本不会修改 PATH、不会全局安装任何东西。需要时可以直接编辑其中的 `$Node` / `$Pnpm` 路径。

### 3b. 在你自己的机器上（已装 Node + pnpm）

```bash
cd automotive-journal
pnpm install
pnpm dev            # http://localhost:4321
pnpm build          # 输出到 dist/
pnpm preview        # 本地预览构建结果
```

> **注意**：`pnpm-workspace.yaml` 里显式允许了 `esbuild` 与 `sharp` 的安装脚本（pnpm 默认拦截）。
> 如果你在其它机器上克隆后安装，pnpm 会提示 `Ignored build scripts` —— 运行 `pnpm approve-builds`
> 并允许这两个包即可。

---

## 4. 写一篇新文章 / Add an article

在 `src/content/journal/zh/` 与 `src/content/journal/en/` 各放一个同名 `.md`：

```markdown
---
title: "标题（含特殊字符时务必加引号）"
dek: "一句话摘要，显示在卡片与详情页顶部"
published: 2026-10-01
category: culture        # culture | modification | driving | review | essay
tags: [标签1, 标签2]
image: /images/your-photo.webp      # 可选，放 public/images/
imageAlt: "图片说明（可访问性必需）"
featured: false          # true 会占据首页封面位
draft: false             # true 则不出现在构建结果中
translationKey: my-slug  # 中英两篇用同一个 key，语言切换才能互相跳转
---

正文 Markdown。
```

文件名即 URL：`zh/xxx.md` → `/zh/journal/xxx/`。

### 关于图片

- 只使用**你自己拍摄或已获授权**的图片；本仓库的 `placeholder-*.svg` 为自制矢量占位图。
- 放进 `public/images/`，正文用 `/images/文件名` 引用（不要外链热链）。
- 建议宽 ≥ 1600px，使用 WebP/AVIF 以控制体积。

---

## 5. 设计约定 / Design conventions

所有视觉参数集中在 `src/styles/global.css` 的 CSS 变量里：

| 令牌 | 值 | 用途 |
| --- | --- | --- |
| `--bg` | `#0a0a0a` | 主背景 |
| `--bg-sunken` | `#060607` | 页脚 / 代码块 |
| `--ink` | `#ececec` | 正文 |
| `--ink-muted` / `--ink-faint` | `#9a9a9f` / `#6b6b70` | 次级信息 |
| `--accent` | `#c98b52` | 铜金点缀（序号、下划线、强调） |
| `--font-display` | Archivo 900 | 冲击力标题 |
| `--font-mono` | JetBrains Mono | 元信息、标签、编号 |
| `--font-serif` | Iowan/Georgia/宋体 | 导语与引用 |

原则：**除图片外不堆砌车辆元素**。秩序感来自编号（`01 —`）、细分割线、等宽字体元信息与克制的单一强调色。
装饰性图片一律加暗角与渐变叠加，保证叠加文字可读。

---

## 6. 部署 / Deploy（全部免费）

项目输出纯静态文件到 `dist/`，三种零成本方案任选：

### A. GitHub Pages（推荐，完全免费）

1. 在 GitHub 新建一个**公开**仓库（需要你自己登录并创建 —— 这一步我不代做）。
2. 推送代码：
   ```bash
   git remote add origin https://github.com/<你的用户名>/automotive-journal.git
   git branch -M main
   git push -u origin main
   ```
3. 在仓库 **Settings → Pages → Build and deployment** 里选择 **GitHub Actions**，
   添加 Astro 官方 workflow（参考 <https://docs.astro.build/en/guides/deploy/github/>）。
4. 修改 `astro.config.mjs` 的 `site` 为 `https://<用户名>.github.io/automotive-journal/`，
   并同步设置 `base: '/automotive-journal/'`（若用项目子路径部署）。
5. 推送到 `main` 即自动构建发布。

### B. Cloudflare Pages

在 Cloudflare 控制台连接同一个仓库：构建命令 `pnpm build`，输出目录 `dist`。
免费额度对个人博客绰绰有余。需要你在网页上完成授权。

### C. Netlify / Vercel

同为免费静态托管，导入仓库后选 Astro 预设即可。

> 域名：`*.github.io` / `*.pages.dev` 子域名足以起步，**无需购买域名**。

---

## 7. 已知限制与注意事项

- **Git 安装**：本机原本没有 Git。已安装便携版 MinGit 到 `C:\Users\admin\.tools\git`，
  未修改全局 PATH 与全局 git 配置。同样不在 PATH 中，需要时直接写全路径：
  ```powershell
  & "C:\Users\admin\.tools\git\cmd\git.exe" status
  & "C:\Users\admin\.tools\git\cmd\git.exe" log --oneline
  ```
  想长期方便，可执行一次（仅当前用户，可撤销）：
  ```powershell
  [Environment]::SetEnvironmentVariable('Path', [Environment]::GetEnvironmentVariable('Path','User') + ';C:\Users\admin\.tools\git\cmd', 'User')
  ```
- **内容均为占位**：所有文章都是版式示例，不是真实测评；首页与页脚都有明确标注。
- **未使用的预留**：`readingTime` 的中文算法按字符数估算，英文按词数估算，仅作参考。
- **字体需联网**：Google Fonts 加载失败时会回退到系统字体，不影响可用性。
- 未包含（按需求刻意省略）：数据库、登录、评论、会员、付费 API、统计脚本。

---

## 8. 许可 / License

代码：可自由用于个人项目。文章内容与图片版权归作者所有。
本仓库不包含任何第三方受版权保护的图片、文章或商标。
