# Researcher Access Programs — 申請對照

> 給獨立研究者（無機構信箱）的 AI API credit 申請指南
> 最後更新：2026-06-27

---

## 快速對照

| 項目 | OpenAI | Anthropic | Gemini (Google) |
|:-----|:-------|:----------|:----------------|
| **額度** | $1,000 | $1,000 | $5,000 (Google Cloud) |
| **需要機構信箱？** | ✅ SMApply 強制 | ❌ Google Form, 不需 | ✅ 需要 |
| **替代方案** | 寫信到 `researcheraccess@openai.com` 說明獨立研究者身份 | Google Form 送出即可，不需機構信箱 | 需學校/機構信箱 |
| **審查週期** | 每季一次（3/6/9/12月） | 每月第一個週一 | 每月 |
| **審查時間** | 4-6 週 | 次月第一週後通知 | 不定 |
| **聯絡信箱** | ~~`researcheraccess@openai.com`~~ ❌ 已棄用 → help.openai.com chat | `researcheraccess@anthropic.com` | 透過 Google Form |
| **適合領域** | alignment / societal impact / robustness / safety | AI safety & alignment 優先 | 所有領域，特別 eval / benchmark / multimodal |

---

## OpenAI Researcher Access Program

### 申請方式
- 正式管道：`https://openai.smapply.org/prog/openai_researcher_access_program/`
- **獨立研究者替代管道**：~~寄信到 `researcheraccess@openai.com`~~ ❌
- **更新 (2026-06-28)**：`researcheraccess@openai.com` 已棄用，自動回覆引導至 help center chat
- **目前唯一管道**：help.openai.com 右下角 chat bubble → 跟客服說明獨立研究者身份

### 信件範本（2026-06-27 實寄版 — 已失效）

```
To: researcheraccess@openai.com
Subject: Researcher Access Program Application — Independent Researcher, No Institutional Email

Dear OpenAI Researcher Access Program Team,

I am writing to apply for the Researcher Access Program as an independent researcher
based in Taiwan. I have a complete research proposal ready but cannot submit through
the SurveyMonkey Apply portal because it requires an institutional email, which I do
not have as an independent researcher.

Research Project: Systematic Ablation of Hallucination Mitigation in LLM-Based
Legal Assistants

I have developed and open-sourced zhiyan-legal (github.com/Lucien-1127/zhiyan-legal),
a multi-layer legal AI system processing Taiwan civil law queries through a five-layer
prompt architecture with Safety Routing, Fact Gate, Mode Router, Persona Router, and
Module Router. The project conducts systematic ablation across 200 ground-truth-labeled
queries comparing GPT-4o, GPT-4o-mini, and o3-mini — to isolate which prompt techniques
independently reduce hallucination in a bilingual legal domain.

This addresses three of your priority areas:
1) Societal Impact — reproducible legal hallucination benchmarks for non-English jurisdictions
2) Robustness — how model families respond to structured safety constraints
3) Alignment — quantifying false-positive rates in tiered safety architectures

I am a prompt engineer and open-source developer in Taiwan (github.com/Lucien-1127).
The project has 122+ tests, a 47,001-provision RAG database, MCP Taiwan Legal DB
integration, and documented ablation methodology. All code and data will be released
under MIT + CC-BY licenses with an arXiv preprint within three months.

I understand the need for fraud prevention. I can provide any additional verification:
video call, notarized ID, GitHub profile review, or detailed project timeline. The
program's stated priority for "researchers with limited financial and institutional
resources" accurately describes my situation.

Could you advise whether:
1) The institutional email requirement can be waived for verifiable independent researchers?
2) There is an alternative submission channel?
3) I can submit my proposal directly via email for manual review?

Best regards,
育准 (Lucien Hsieh)
hsieh89t@gmail.com | github.com/Lucien-1127
```

### 信件要點
1. 說明是獨立研究者，無機構信箱無法透過 SMApply 申請
2. 附上 research proposal 摘要（重點：領域契合度、開源專案、可驗證身份）
3. 提供替代驗證方式（GitHub profile、video call、notarized ID）
4. 引用他們 FAQ 中的 priority：「researchers with limited financial and institutional resources」
5. 三個具體問題：是否可 waiver、替代提交方式、可否 email 提交

---

## Anthropic External Researcher Access Program

### 申請方式
- Google Form：`https://forms.gle/pZYC8f6qYqSKvRWn9`
- **不需要機構信箱**，獨立研究者可直接送

### 表單欄位（2026-06-27 驗證）

| 欄位 | 類型 | 填入內容 |
|:-----|:-----|:---------|
| Email | 必填 | `hsieh89t@gmail.com` |
| Name of primary contact | 必填 | `育准 (Lucien Hsieh)` |
| Organization name | 選填 | `Independent Researcher` |
| Recommended by Anthropic employee? | 必填 radio | `No` |
| Organization ID | **必填** | 從 `console.anthropic.com/settings/organization` 複製 |
| Brief description (<200 words) | 必填段落 | 見下方範本 |
| Research description (<300 words) | 必填段落 | 見下方範本 |
| More than $1000? | 必填 radio | `No` |
| Low quality of service? | 必填 radio | `I'm fine with receiving a low quality of service` |
| GitHub / Google Scholar link | 必填 | `https://github.com/你的帳號` |
| Additional information | 選填 | 研究額外背景（release plan、時程等） |
| Located in US? | 必填 radio | `No`（台灣） |
| Terms of Service | 必填 checkbox | `I agree` ✓ |

### Applicant Description 範本（<200 words）

```
Independent prompt engineer and open-source developer based in Taiwan.
Creator of zhiyan-legal (github.com/Lucien-1127/zhiyan-legal), a multi-layer
legal AI system with 122+ tests, 47K-provision Taiwan law RAG database, and
MCP integration. Research focuses on hallucination mitigation in LLM-based
legal assistants for civil law jurisdictions.
```

### Research Description 範本（<300 words）

```
Systematic ablation of hallucination mitigation in LLM-based legal assistants
for Taiwan civil law. Compares four conditions (full system, no-citation-policy,
no-fact-gate, unconstrained baseline) across 200 ground-truth-labeled queries
spanning 9 task routes. Directly addresses AI safety by quantifying how
citation-grounding reduces fabrication rates and measuring safety routing
effectiveness. Free credits essential as independent researcher without
funding — 800+ configurations cost ~$800-1000.
```

### ⚠️ 已知陷阱：Google Forms reCAPTCHA

Google Form 有 reCAPTCHA 保護，瀏覽器自動化工具（browser_click / browser_type）和 curl 直接 submit 都會被擋。**必須由人類在瀏覽器上手動點擊提交。**

| 方式 | 結果 |
|:-----|:------|
| `browser_type` 填入資料 | ✅ 可填寫 |
| 程式化 `curl POST` | ❌ 400 (reCAPTCHA blocked) |
| `form.requestSubmit()` JS | ❌ 被 CAPTCHA 擋 |
| 人類手動點「提交」 | ✅ 唯一通過方式 |

解決方案：用 browser 工具填好所有欄位後，引導使用者自行點擊提交按鈕。

---

## Gemini Academic Program (Google)

### 申請方式
- Google Form：`https://forms.gle/HMviQstU8PxC5iCt5`
- **需要機構信箱**（faculty / staff / PhD student）
- 獨立研究者目前無替代管道

### Alternative
Google Cloud for Researchers：`https://cloud.google.com/edu/researchers`
- $5,000 Google Cloud credits
- 同樣需要機構 affiliation

---

## 不適合獨立研究者的其他管道

| 管道 | 原因 |
|:-----|:------|
| Together AI Research Credits | invite-only，限學生 |
| Cohere Catalyst Grants | 限 academic / civic institution |
| Anthropic Fellows Program | 4 個月全職 fellowship，非 credit grant |
| ML Commons | 機構導向 |

---

## 策略建議

| 順序 | 管道 | 理由 | 現狀（2026-06-28） |
|:----:|:-----|:------|:-------------------|
| 1 | **Anthropic**（Google Form） | 最簡單，不需機構信箱，每月審查 | ✅ 已送出，等 7 月初審查 |
| 2 | **OpenAI**（email 直寄） | ~~有 waiver 可能~~ ❌ 信箱已棄用 | ❌ 已關閉，可試 help center chat |
| 3 | **Gemini** | 需機構信箱，若有門路再申請 | ⏸️ 等候機構信箱 |

## 關於 zhiyan-legal 的研究提案

上述所有申請的核心研究提案一致：

```
Title: Systematic Ablation of Hallucination Mitigation in LLM-Based Legal Assistants
Domain: Taiwan civil law, hallucination, prompt engineering
Architecture: 5-layer (SRP → Fact Gate → Mode Router → Persona → Module)
Dataset: 200 ground-truth-labeled Taiwan law queries, 9 task routes
Conditions: full system / no-citation-policy / no-fact-gate / unconstrained
Models: GPT-4o, GPT-4o-mini, o3-mini (OpenAI); Claude 3.5 (Anthropic)
Output: arXiv preprint + open-source (MIT + CC-BY), within 3 months
Budget: ~$800-1,000 per lab
```
