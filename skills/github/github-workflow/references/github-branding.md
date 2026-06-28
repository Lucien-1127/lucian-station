# GitHub 專案品牌化與文件基礎建設

## 適用情境

當需要將 GitHub 倉庫從「原始碼存放處」升級為「成熟開源專案門面」時：

- 建立 **GitHub Pages** 文件站（MkDocs Material）
- 建立 **GitHub Wiki** 內容
- 升級 **README** 為雙語並附 badges
- 建立 **Profile README**（`username/username`）
- 建立 **Issue/PR 模板**
- 建立 **GitHub Actions CI/CD** 部署管線

---

## 1. MkDocs GitHub Pages 建置

### 安裝

```bash
pip install mkdocs mkdocs-material mkdocs-git-revision-date-localized-plugin mkdocs-minify-plugin
```

### 建置流程（多步驟，先 build 再 refine）

```bash
# Step 1 — 建立 mkdocs.yml
# Step 2 — 首次 build
mkdocs build --strict
# → 如果報錯，修正後重複 Step 2
# → 常見錯誤：nav 中參考了不存在的檔案、custom_dir 路徑不存在、plugin 未安裝

# Step 3 — build 通過後，確認 site/ 目錄產生
# Step 4 — 加入 .gitignore（排除 site/）
# Step 5 — 建立 GitHub Actions 部署工作流
# Step 6 — 推送後在 Settings → Pages → Source 選 GitHub Actions
```

### mkdocs.yml 關鍵設定

```yaml
site_name: 專案名稱
site_url: https://<owner>.github.io/<repo>/
repo_url: https://github.com/<owner>/<repo>

theme:
  name: material
  language: zh-TW           # 繁體中文
  features:
    - navigation.tabs
    - navigation.expand
    - navigation.top
    - search.suggest
  palette:
    primary: indigo
    accent: deep orange

markdown_extensions:
  - admonition
  - pymdownx.details
  - pymdownx.superfences
  - footnotes
  - toc:
      permalink: true

plugins:
  - search
  - git-revision-date-localized
  - minify:
      minify_html: true
```

### 已知陷阱

- `!!python/name:material.extensions.emoji.twemoji` 是有效 PyYAML 語法但被 linter 報錯 — 可安全忽略
- `custom_dir` 若未使用主題覆蓋就不能設定，否則 `mkdocs build --strict` 報錯
- **中文檔案路徑在 nav 中可直接用相對路徑**，MkDocs Material 支援 UTF-8 檔案名
- 中文目錄的 nav 條目必須逐一列出檔案路徑，**不能用通配符或預留字串**（如 `(更多詞條...)`），否則 `--strict` 模式會報 `A reference to 'xxx' is included in the nav configuration, which is not found in the documentation files` — 解決方式：列出所有檔案，或移除該 nav 條目
- 首次建立用 `mkdocs build --strict` 驗證所有 nav 連結正確
- **`site/` 目錄容易被意外 `git add`** — build 後一定要先加 `.gitignore` 再 commit（`site/` 加上 `git rm -r --cached site/` 清除已暫存內容）

### .gitignore

```
site/   ← MkDocs build 產出，永遠不提交
```

### GitHub Actions 部署（gh-pages.yml）

```yaml
on:
  push:
    branches: [main]
    paths: ['docs/**', 'mkdocs.yml', '.github/workflows/gh-pages.yml']

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: {fetch-depth: 0}
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install mkdocs-material mkdocs-git-revision-date-localized-plugin mkdocs-minify-plugin
      - run: mkdocs build --strict
      - uses: actions/upload-pages-artifact@v3
        with: {path: site}
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: {name: github-pages, url: ${{steps.deployment.outputs.page_url}}}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

### 啟用 Pages

1. 推送 mkdocs.yml + docs/ + gh-pages.yml
2. 去 Repo → Settings → Pages → Source 選 **GitHub Actions**
3. 或推送後 Actions 自動跑完即部署完成

### CI 失敗修復流程

當 GitHub Actions 的 `mkdocs build --strict` 步驟失敗時：

1. 本機執行 `mkdocs build --strict` 復現錯誤
2. 修正 nav 連結、檔案缺失、`.md` 副檔名問題
3. 本機確認 build 通過後再推送
4. 推送會自動觸發新的 Actions 工作流

**注意**：Actions 需要登入才能看完整 logs（`Sign in to view logs`）。但 error annotation 摘要通常已足夠判斷錯誤類型。若需詳細 logs，先本機復現。

---

## 2. 雙語 README 模式

### docs/index.md（MkDocs 入口頁）

建議在 `docs/` 根目錄建立 `index.md` 作為 MkDocs 網站首頁。內容為專案簡介 + 各層級文件導覽連結。

Markdown 與 MkDocs 都能解析頂層 `docs/index.md` 為 `/` 路徑，不衝突。

### 結構

```markdown
<details open>
<summary><b>🇬🇧 English</b></summary>

(英文完整內容，含 overview、架構圖、快速開始、API、引用)

</details>

<details>
<summary><b>🇹🇼 繁體中文</b></summary>

(繁體中文完整內容，與英文對應)

</details>
```

- `open` 屬性讓英文區塊預設展開，中文折疊
- badges 放在最頂端（語言切換之外），共用同一組 badge
- 中英文各有獨立的儲存庫結構說明、快速開始

---

## 3. GitHub Wiki（未初始化時的替代方案）

如果 `https://github.com/<owner>/<repo>.wiki.git` clone 不到（`Repository not found`），表示 Wiki 從未被啟用。此時：

1. 在 `docs/wiki/` 下建立內容
2. README 中加一行導覽連結
3. 等 Wiki 啟用後再搬過去

### 連結注意

`[Home](Home.md)` 在本地正常，搬到真正 Wiki 時要改成 `[Home](Home)`（不帶副檔名）。

### Wiki 頁面連結到主 docs/ 時的處理

Wiki 頁面（`docs/wiki/`）若要參照主 `docs/` 目錄的文件，**不能使用相對路徑**（如 `../00_入口與總覽/00_開始閱讀_入口導覽_v2.1.0.md`），因為 MkDocs 的 strict mode 會報錯：「target is not found among documentation files」。

解決方式：用**完整 GitHub 連結**指向主倉庫：

```markdown
[入口導覽](https://github.com/<owner>/<repo>/blob/main/docs/00_入口與總覽/00_開始閱讀_入口導覽_v2.1.0.md)
```

**原因**：`docs/wiki/` 在 MkDocs 中被視為獨立子目錄，其相對路徑不會向上解析到 `docs/` 根目錄。

### 跨頁面相對連結

`docs/wiki/` 內的頁面互連用 `.md` 副檔名（如 `[快速開始](Quickstart.md)`）。若未來搬到 GitHub Wiki 須移除 `.md`。  

**寫作建議**：先寫內容時全用 `.md` 版本，搬遷時一次 batch sed 取代。

---

## 4. Profile README（`<username>/<username>`）

### 建立方式

```bash
gh repo create <username>/<username> --public --description "個人品牌"
```

或手動在 GitHub.com → New repository → 倉庫名 = 使用者名稱 → Public → Add a README file。

### 內容建議

```markdown
# 品牌名稱

> 一句話定位。

### 🌟 核心專案

| 專案 | 說明 |

### 🔬 研究方向

### 🏗️ 技術棧

---

> 📧 email · 地點
```

---

## 5. Issue/PR 模板

```
.github/
├── ISSUE_TEMPLATE/
│   ├── 01_bug_report.md
│   ├── 02_feature_request.md
│   ├── 03_hallucination_report.md   # 法律 AI 專用：幻覺回報
│   └── config.yml
├── PULL_REQUEST_TEMPLATE.md
└── FUNDING.yml
```

---

## 6. SECURITY.md / FUNDING.yml

```yaml
# FUNDING.yml
github: [username]
custom: ['https://buymeacoffee.com/username']
```
