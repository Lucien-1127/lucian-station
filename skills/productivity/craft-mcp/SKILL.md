---
name: craft-mcp
description: Craft.do MCP 讀寫整合 — 文件建立、排版、區塊操作、任務管理。支援 120+ 頁面主題、字型、分隔線、callout、程式碼區塊、表格、rich link。SSE HTTP MCP。
user-invocable: true
---

# Craft MCP — 排版與讀寫整合

> Craft 空間：霆's Space (0496fbaf-ff73-6358-c368-f8ed687048af)
> MCP 端點：`https://mcp.craft.do/links/8mNbuav3mqS/mcp`
> 時區：Asia/Taipei

---

## MCP 設定

```yaml
# config.yaml 中 mcp_servers:
mcp_servers:
  craft:
    url: "https://mcp.craft.do/links/8mNbuav3mqS/mcp"
```

## 可用工具

| 工具 | 功能 |
|:-----|:------|
| `craft_read` | 讀取／搜尋文件、列出 folders/docs/collections、explore themes/washi |
| `craft_write` | 建立／更新文件、blocks、tasks、collections、comments |
| `blocks_revert` | 復原上一次寫入 |

---

## 文件操作

### 建立文件

```
documents create --title "標題" [--destination unsorted|templates] [--folder <folderId>]
```

回傳 rootBlockId + Craft app link，之後用該 rootBlockId 新增內容。

### 加入內容

```
blocks add --id <rootBlockId> --markdown "內容"
blocks add --id <rootBlockId> --position start|end
blocks add --siblingId <blockId> --position before|after
```

### 更新內容

```
blocks update --id <blockId> --markdown "新內容"
blocks update --id <blockId> --json '[{"id":"...","listStyle":"task"}]'
```

### 刪除

```
blocks delete --id <blockId>
```

---

## 排版系統

### Markdown 擴充語法

| 語法 | 效果 |
|:-----|:------|
| `<callout>文字</callout>` | Callout 高亮區塊（focus block） |
| `+ 標題` | 可折疊 Toggle 列表 |
| `> 引用` | Blockquote |
| `---` | 分隔線（三條 dash） |
| `# H1` ~ `###### H6` | 標題 |
| `**粗體**` `*斜體*` `~~刪除線~~` | 文字樣式 |
| `- 項目` `1. 編號` | 列表 |
| `` `代碼` `` ` ``` ` | 行內／區塊程式碼 |
| `[文字](url)` | 連結 |
| `$LaTeX$` `$$LaTeX$$` | 數學公式（inline／block） |

### 10 種 Block Type（JSON 模式）

| Type | 說明 | Insert JSON |
|:-----|:-----|:------------|
| `text` | 段落／列表／任務 | `{"type":"text","markdown":"...","listStyle":"bullet\|numbered\|toggle\|task"}` |
| `page` | 子頁面（可當卡片） | `{"type":"page","markdown":"Title","content":[...]}` |
| `code` | 程式碼 | `{"type":"code","rawCode":"...","language":"python"}` |
| `image` | 圖片 | `{"type":"image","url":"..."}` |
| `video` | 影片 | `{"type":"video","url":"..."}` |
| `table` | 表格 | `{"type":"table","markdown":"\|A\|B\|\\n\|---\|---\|\\n\|1\|2\|"}` |
| `line` | 分隔線 | `{"type":"line","lineStyle":"strong\|regular\|light\|extraLight\|pageBreak"}` |
| `richUrl` | 連結卡片 | `{"type":"richUrl","url":"...","title":"...","description":"..."}` |
| `file` | 檔案附件 | `{"type":"file","url":"..."}` |
| `drawing` | 手繪 | （update only） |
| `whiteboard` | 白板 | （create via craft_write） |

### 區塊共用欄位

```
indentationLevel: 0–5      # 縮排層級
listStyle: none|bullet|numbered|toggle|task
decorations: []            # 裝飾: "quote"(焦點), "callout", "card" 等
color: "#RRGGBB"           # 文字顏色
backgroundColor: "#RRGGBB" # 區塊背景色（highlight）
textAlignment: left|center|right
font: system|system-serif|system-rounded|system-mono
textStyle: body|h1|h2|h3|h4|h5|h6|caption|page
cardLayout: {}             # 卡片佈局設定
taskInfo: {}               # 任務資訊（schedule, deadline, repeat, state）
```

---

## 🎨 Craft 排版設計系統（完整指南）

> 核心哲學：Craft 是「文件級排版」而非「頁面級排版」。每個 block 都是可移動、可樣式的獨立單元。

### 一、設計原則（適用於 Craft）

| 原則 | 在 Craft 中的實踐 |
|:-----|:-----------------|
| **層級 Hierarchy** | H1 → H2 → H3 → body 的尺寸階梯；卡片尺寸差異化 |
| **留白 White Space** | 善用 line separators 與段落間距，不過度堆砌 block |
| **對比 Contrast** | 淺色背景配深色文字閱讀最佳（法律文件）；深色配淺色程式碼主題 |
| **重複 Repetition** | 同一份文件用單一 theme + 單一字型，不混搭 |
| **韻律 Rhythm** | 每 section 之間用相同間距的分隔線，創造閱讀節奏 |
| **統一 Unity** | 空間內所有文件設定統一的預設樣式（Space Settings → Default Style） |
| **平衡 Balance** | 正式文件用對稱排版（置中標題），創意文件用不對稱 |

### 二、Craft 文件分級樣式指南

| 文件類型 | Theme 建議 | 字型 | 背景 | 適合 |
|:---------|:-----------|:-----|:-----|:-----|
| **正式法律文件** | `paper` 或 `silk-screen` | **serif** | 純白／淺灰 gradient | 申論答案、法律分析 |
| **技術文件** | `techy` 或 `mdr` | **mono** | 深色 gradient | 程式碼、API 文件 |
| **會議記錄** | `default` 或 `soft-spring` | **system** | 無或淺背景 | 快速記錄 |
| **創意筆記** | `le-mans` 或 `azure-breeze` | **rounded** | 彩色 gradient | 腦力激盪 |
| **日記／個人** | `writer` 或 `midnight` | **serif** | 暖色 gradient | 閱讀體驗優先 |
| **專案看板** | `breeze` 或 `citrus` | **rounded** | 明亮 solid | 任務追蹤 |
| **簡報風格** | `fire-horse` 或 `vibrant-nights` | **serif** | 深色 gradient + cover | 高視覺衝擊 |
| **學術研究** | `paper` 或 `antiquities` | **serif** | 米白 solid | 論文草稿 |
| **食譜／生活** | `citrus` 或 `honey` | **rounded** | 暖色 solid | 輕鬆活潑 |

### 三、Craft 特有的視覺工具

#### 3a. 卡片系統（Cards）

Craft 最與眾不同的功能。Page block 加上視覺樣式就變成卡片。

**建立方式**：`/card` slash menu 或 MCP 建立 page block 後加 `cardLayout`

**5 種預覽樣式**（控制卡片在父頁面上的顯示方式）：

| 樣式 | 顯示 | 適用 |
|:-----|:------|------|
| Standard | 標題 + 摘要 | 一般用途 |
| Emoji | 最多 4 個 emoji | 快速辨識 |
| Book | 書本翻頁風格 | 長篇閱讀 |
| Sticky Note | 黃色便利貼 | 臨時筆記 |
| Gallery | 最多 3 張圖片 collage | 視覺內容 |

**5 種卡片尺寸**（前 2 種需 Craft Plus）：
- Mini → Small → Medium → Large → Hero

**卡片背景**：
- Solid color（從調色盤或自訂 RGB）
- Unsplash 圖片（內建搜尋）
- 自己上傳圖片
- **無背景**（極簡風）

**卡片適用場景**：
- 專案規劃 → 每個 phase 一張卡片
- 知識庫 → 每個 topic 一張卡片
- 會議記錄 → 每個 agenda item 一張卡片

#### 3b. Callout 高亮區塊

`<callout>文字</callout>` — 粉色底色高亮，適合放置警告、提醒、重點
在 MCP 中可搭配 emoji 前綴：
- `<callout>🔴 高風險：...</callout>`
- `<callout>🟢 正確：...</callout>`
- `<callout>ℹ️ 注意：...</callout>`

#### 3c. Toggle 可折疊區塊

`+ 標題` — 折疊內容。後續 block 的 indentationLevel 大於 toggle block 時自動成為其折疊內容。

```
+ 點擊展開
  這裡是折疊內容（indentationLevel=1）
  繼續內容（indentationLevel=1）
```

#### 3d. Focus Block（焦點區塊）

Block decorations 中的 `"quote"` 類型——左側有豎線的強調區塊，比 callout 低調，適合放置關鍵引述。

#### 3e. Washi Tape 裝飾分隔線

Craft 專有功能。五種圖案 + 自訂顏色：

| Pattern | 視覺 |
|:--------|:------|
| `wave` | 波浪 |
| `hex` | 六角幾何 |
| `stripe` | 橫條紋 |
| `dot` | 圓點 |
| `grid` | 網格 |
| `diagonal` | 斜線 |

**設計原則**：washi 裝飾性強，適合創意文件；正式文件用 `line` 或 `doodle`。

#### 3f. Page Break（分頁符號）

`lineStyle: "pageBreak"` — 在 Craft app 中產生視覺分頁效果，適合長文件章節分隔。

### 四、頁面美學完整設定

```
# 主題（影響字型、背景、色調全部）
--theme-id <name>

# 字型（覆蓋主題設定）
--font sans-serif|serif|rounded|mono

# 文字與背景顏色（多模式適應）
--text-color "#RRGGBB"              # 固定顏色
--text-color "#LIGHT_HEX #DARK_HEX" # 淺色／深色模式各自顏色
--bg-color "#RRGGBB"                # 區塊背景

# Cover 封面圖片（頁面頂端 hero 橫幅）
--cover-url <url>
--cover-crop "x,y,w,h"             # 裁切（0.0-1.0 比例）

# Backdrop 頁面背景
--backdrop-type solid|gradient|image|pattern|none
--backdrop-color "#RRGGBB"                    # 純色背景
--backdrop-colors "#C1,#C2"                   # 漸層色（逗號分隔）
--backdrop-direction top-to-bottom|left-to-right
--backdrop-url <url>                          # 圖片背景

# 分隔線
--separator line|doodle|washi|none
--washi-pattern wave|hex|stripe|dot|grid|diagonal
--washi-color "#RRGGBB"
```

### 五、排版實戰流程（最佳做法）

Craft 官方建議的 5 步驟工作流：

```
Step 1 — 頁面基底
  ↓ 選擇背景（solid / gradient / image）和 cover 設定文件氛圍
Step 2 — 選擇字型
  ↓ 根據文件用途配對字型（serif=正式、mono=技術、rounded=活潑）
Step 3 — 加入結構元素
  ↓ 在主要章節之間插入分隔線（separator）建立視覺層次
Step 4 — 應用區塊級樣式
  ↓ 隨寫隨用 highlight、color、callout、card 等樣式
Step 5 — 退一步審視調整
  ↓ 看整體是否平衡、層級是否清晰、留白是否恰當
```

### 六、常見排版錯誤（避免）

| ❌ 錯誤 | ✅ 修正 | 原因 |
|:--------|:--------|:-----|
| 一份文件用 2 種以上主題 | 全篇統一一個 theme | 破壞 unity |
| 過度使用 callout | 關鍵 1-2 處用 callout，其餘用 focus quote | 降低對比效果 |
| 深色背景 + 深色文字 | 深色背景配淺色文字，反之亦然 | 可讀性 |
| 連續 5+ 個 block 無分隔 | 每 3-4 個 section 插入 separator | 閱讀節奏 |
| 同一頁面混太多顏色 | 限制在 2-3 色（主色 + 強調色 + 文字色） | 視覺混亂 |
| 大段落無標題層級 | 每 200-300 字插入適當 heading | 掃讀困難 |
| 卡片塞滿 block 無留白 | 卡片內部保持 padding | 呼吸空間 |

---

## 頁面美學

### 主題（120+ 套，常用清單）

| 主題 ID | 風格 |
|:--------|:-----|
| `default` | 原始 |
| `fire-horse` | 🔴 熱情紅 |
| `soft-spring` | 🌸 柔和春 |
| `midnight` | 🌙 深夜 |
| `writer` | 📝 寫作 |
| `paper` | 📄 紙張 |
| `techy` | 💻 科技 |
| `mdr` | 🎨 現代 |
| `le-mans` | 🏎 賽車 |
| `sunset` | 🌅 夕陽 |
| `golden-hour` | 🌇 黃金 |
| `azure-breeze` | 🌊 清風 |
| `vibrant-nights` | 🌃 夜 |
| `coral` | 🪸 珊瑚 |
| `blushblue` | 💙 藍調 |
| `silk-screen` | 🖼 絲網 |
| `beach` | 🏖 沙灘 |
| `lunar-ink` | 🖋 墨 |
| `nord` | ❄️ 北歐 |
| `retro` | 📻 復古 |
| `citrus` | 🍊 柑橘 |
| `leaves` | 🌿 葉 |
| `indigo` | 🔮 靛藍 |
| `honey` | 🍯 蜂蜜 |
| `plum` | 🫐 梅紫 |
| `rose` | 🥂 玫瑰 |
| `infinity-void` | ⚫ 虛空 |
| `electric` | ⚡ 電光 |

查詢全部：`blocks explore-themes --type page`

### 字型

```
--font sans-serif    # 無襯線（預設）
--font serif         # 襯線（適合正式文件）
--font rounded       # 圓體（活潑）
--font mono          # 等寬（程式碼）
```

### 頁面裝飾

```
# Hero 封面圖片
--cover-url <url>              # 頂部橫幅
--cover-crop "x,y,w,h"         # 裁切（0.0-1.0）

# 背景
--backdrop-type solid|gradient|image|pattern|none
--backdrop-color "#RRGGBB"               # 純色
--backdrop-colors "#FF6B6B,#4ECDC4"      # 漸層
--backdrop-direction top-to-bottom       # 漸層方向

# 分隔線風格
--separator line|doodle|washi|none
--washi-pattern wave|hex|stripe|dot|grid|diagonal
--washi-color "#RRGGBB"
```

---

## 任務管理

```
tasks add --markdown "任務內容"
  --location inbox|dailyNote|document
  --date today|tomorrow|yesterday|YYYY-MM-DD
  --schedule 日期
  --deadline 日期
  --state todo|done|canceled
  --repeat daily|weekly|weekly:mon,wed,fri|monthly|monthly:1,15|yearly|flexible:weekly:mon,fri
```

### 重複規則

| 簡寫 | 等同 JSON |
|:-----|:----------|
| `daily` | `{"type":"fixed","frequency":"daily"}` |
| `weekly:mon,wed,fri` | `{"type":"fixed","frequency":"weekly","weekly":{"days":["monday","wednesday","friday"]}}` |
| `monthly:1,15` | `{"type":"fixed","frequency":"monthly","monthly":{"days":[1,15]}}` |
| `flexible:weekly:mon,fri` | 完成日為基準相對排程 |

---

## 查詢操作

### 文件列表

```
documents list                                    # 全部文件
documents list --location unsorted                # 未排序
documents list --folder <folderId>                # 指定資料夾
```

### 讀取內容

```
blocks get <rootBlockId>                          # 預設 markdown
blocks get <rootBlockId> --format markdown|json   # 指定格式
blocks get <rootBlockId> --depth 3                # 巢狀深度
blocks get --date today                           # 今日日記
```

### 搜尋

```
search "關鍵字" [--location unsorted|trash|templates|daily_notes]
```

### 資料夾

```
folders list [--filter <regex>]
```

### Collections（資料庫表格）

```
collections list [--document <rootBlockId>]
collections schema --collection <collectionId>
collections items-get --collection <collectionId>
collections items-add --collection <id> --Name "value"
collections views-list --collection <id>
```

---

## 實用串接範例

### 建立一篇排版完整的新文件

```bash
# 1. 建立文件
documents create --title "週報 2026-06-28" --destination unsorted
# → 拿到 rootBlockId: ABC-123

# 2. 設定頁面主題
blocks update --id ABC-123 --theme-id writer --font serif

# 3. 加入內容
blocks add --id ABC-123 --markdown "# 本週重點\n\n<callout>截止日提醒</callout>\n\n## 進度\n- 項目A ✅\n- 項目B ⏳\n\n> 引用客戶回饋"
```

### 將智研 WRITER 輸出寫入 Craft

```bash
# blocks add 後套上 visial formatting
blocks add --id <pageId> --markdown "申論答案..."
blocks update --id <pageId> --theme-id paper --font serif
```

### 建立含 code block 的技術文件

```bash
blocks add --id <pageId> --json '{"type":"code","rawCode":"def hello():\\n    print(\"hi\")","language":"python"}'
# 設定 syntax highlighting
blocks update --id <codeBlockId> --theme-id dracula
```

---

## 注意事項

| 限制 | 說明 |
|:-----|:------|
| CRUD 文件 | ✅ 建立／讀取／更新／搜尋／刪除 |
| 刪除限制 | 不能刪 trash 裡的文件，需先還原 |
| Collection items | 用 `collections items-*` 工具，非 `blocks update` |
| 部分表格 | 巢狀 cell 表格 read-only |
| 模板文件 | 可建立在 templates 區，但 MCP 不能從模板實例化新文件 |
| 自訂 style ID | ❌ 不支援，只能用內建 theme 或逐項設定 |
| 大量操作 | 用 `--json '[...]'` 陣列批次，比多次單一呼叫快 |
