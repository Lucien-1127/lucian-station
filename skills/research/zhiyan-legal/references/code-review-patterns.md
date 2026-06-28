# zhiyan-legal 程式碼審查與維護模式

> 整理自 2026-06-09 code review sprint

## 路由關鍵字模式

### 複合詞優先於單字

中文單字關鍵字（告、查、殺）容易在複合詞中誤觸。
策略：加入複合詞關鍵字（長度長 = 先匹配），單字保留為 fallback。

```python
# ✅ 正確：複合詞先列，單字在後
"審查": "QC",      # 長度2，優先匹配
"查": "RESEARCH",  # 長度1，僅在無複合詞時匹配
```

### 邊界保護（安全關鍵字專用）

只有高風險誤觸的單字需要邊界保護：
- `殺` → SAFETY（抹殺 → 不應觸發 SAFETY）

邊界邏輯：前後皆為中文字時不匹配。

```python
_HIGH_RISK_SINGLE_CHARS = {"殺"}

def _keyword_in_text(kw, text):
    if len(kw) == 1 and kw in _HIGH_RISK_SINGLE_CHARS:
        idx = text.find(kw)
        while idx != -1:
            prev_cjk = idx > 0 and '\u4e00' <= text[idx-1] <= '\u9fff'
            next_cjk = idx+1 < len(text) and '\u4e00' <= text[idx+1] <= '\u9fff'
            if not (prev_cjk and next_cjk):
                return True
            idx = text.find(kw, idx + 1)
        return False
    return kw in text
```

### 不要對「查」做邊界保護

「查」在中文中常作為獨立動詞（查資料、查一下），
加邊界保護會讓「幫我查台灣法規」誤路由到 CONSULTANT。

維持複合詞優先即可：審查→QC、調查→RESEARCH、查→RESEARCH。

### 路由優先序（2026-06-27 修正）

```
1. SAFETY（無條件高危）—— 自殺/不想活/謀殺/綁架，不可被任何模式豁免
2. SIMULATION —— 模擬/假設/推演，優先於 LITIGATION，讓「模擬訴訟」正確進入模擬模式
3. SAFETY（情境敏感）—— 殺/跟蹤/詐騙/威脅，僅在非模擬語境觸發
4. LITIGATION —— 訴訟/攻防/起訴/提告
5. QC > RESEARCH > REPORT（模式路由）
6. CONSULTANT > TA > TUTOR > LEGAL_WRITER（人格路由）
7. CONSULTANT（預設 fallback）
```

**關鍵教訓**：`SIMULATION` 必須在 `LITIGATION` 之前檢查。否則「模擬原告的攻防策略」會誤進 LITIGATION，永遠到不了模擬模式。這是一行交換就可修復的設計缺陷，但若沒寫進路由表就容易被忽略。

### SAFETY 詞表分級（2026-06-27 新增）

第三方壓力測試發現：模擬模式的使用者討論「殺」的策略時，若殺字通過 CJK 邊界保護（前後非中文字），SAFETY 會無條件攔截。但模擬場景下討論「殺」是合法的法律分析，不應觸發安全路由。

解決方案：將 SAFETY 關鍵字分為兩級。

**無條件高危**（永遠最高優先，含模擬模式）：

```python
_SAFETY_UNCONDITIONAL = {
    "自殺", "不想活", "想死", "謀殺", "殺人", "殺害", "綁架",
}
```

**情境敏感**（非模擬語境才觸發）：

```python
_SAFETY_CONTEXT_SENSITIVE = {
    "殺", "跟蹤", "詐騙", "威脅",
}
```

route() 函數先檢查無條件高危詞，再偵測是否為 SIMULATION 語境，最後才決定情境敏感詞是否觸發。詳見 router.py `route()` 函數。

### 預設 fallback

無關鍵字匹配時 fallback 到 CONSULTANT（原為 QC）。
理由：使用者問「欠錢不還怎麼辦」是諮詢，不是品質檢查。

## 任務新增流程

1. KEYWORD_MAP 加入關鍵字
2. TASK_LAYERS（manifest.py）加入對應的文件層
3. describe_route() 加入描述
4. cli.py 的 print_task_list() 加入 order
5. 補測試案例（含邊界案例）

## SIMULATION 模式

當使用者使用「假設、模擬、推演」等程序性前提詞彙時，
路由到 SIMULATION。此時 compose() 自動插入模擬模式前言。

`--simulate` CLI 參數可手動啟用，即使 query 中無觸發詞。

## Frontmatter 時態標記

docs/ 下的 markdown 文件可在 frontmatter 中加入：

```yaml
---
status: active    # active / draft / deprecated
as_of_date: 2026-06-01
version: 2.0.0
---
```

compose() 會自動生成時態標頭：
```
✅ status: active | as of 2026-06-01 | v2.0.0
```

deprecated 文件會標示 ⚠️。

## Provider 模型更新（2026/06 現況）

| 舊模型 | 狀態 | 新模型 |
|--------|------|--------|
| gpt-4o / gpt-4o-mini | 退役 (2026/2) | gpt-5.1 |
| deepseek-chat | 棄用 (2026/7) | deepseek/deepseek-v4-flash |
| gemini-2.5-flash | 已舊 | gemini-3-flash-preview |
| claude-sonnet-4 | 已舊 | anthropic/claude-sonnet-4.6 |
| mimo-v2.5 (小米) | 無聲量 | minimax-m3 |

更新 4 個檔案：.env.example、README.md（中英雙語表）、setup.sh、runner.py docstring。
