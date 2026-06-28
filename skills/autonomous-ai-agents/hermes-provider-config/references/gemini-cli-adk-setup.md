# Gemini CLI + ADK + GEAR 工具鏈

本機安裝的輔助開發工具，配合 Gemini API 使用。

## Gemini CLI

開源終端 AI 助手，直接在 terminal 用 Gemini 模型。

```bash
npm install -g @google/gemini-cli
```

### 認證方式

| 方式 | 適用場景 | 狀態 |
|------|---------|:---:|
| Google OAuth（Sign in with Google） | 有瀏覽器的本機 | 🔴 免費層已於 2026-06-18 停用 |
| API Key | headless VM | ✅ 最簡單 |
| Vertex AI | GCP 專案已啟用 Vertex AI | ⚠️ 模型區域可用性不一致 |
| GCA（Gemini Code Assist） | 需互動式終端 | ❌ headless 不可用 |

**headless VM 推薦用法**：設定 `GEMINI_API_KEY` + `GEMINI_CLI_TRUST_WORKSPACE=true`。

```bash
export GEMINI_API_KEY="<your-key>"
export GEMINI_CLI_TRUST_WORKSPACE=true
gemini -p "你的問題"
```

> 💡 **Hermes 加密 token 相容性**：Hermes 憑證池中的 `AQ.Ab8...` 加密 token 可直接設為 `GEMINI_API_KEY`。Gemini CLI 調用時，Hermes 背景解密機制會自動解析成真正的 API key。不需手動解密或從 Google AI Studio 複製明文 key。將 token 寫入 `.env` 即可永久生效：
> ```bash
> echo 'GEMINI_API_KEY=AQ.Ab8...' >> ~/.hermes/profiles/<profile>/.env
> ```

### 已知陷阱

- Vertex AI 在 asia-east1 無法存取 gemini-3.1/3.5 系列模型 → 改用 API Key
- `gcloud auth application-default login` 仍要求互動式終端 → headless 不可用
- 需要 `GEMINI_CLI_TRUST_WORKSPACE=true` 否則 headless 模式報信任錯誤

## Agent Development Kit (ADK)

Google 的 AI Agent 開發框架，GEAR 課程核心工具。

```bash
pip install google-adk
```

驗證安裝：
```python
import google.adk; print(google.adk.__version__)
```

用途：建構、測試、評估、部署 AI agents。支援 Python/TypeScript/Go/Java/Kotlin。

## GEAR（Gemini Enterprise Agent Ready）

Google 免費開發者計畫，每月 35 學習學分。

- 註冊：https://developers.google.com/program/gear
- 登入後自動獲得 35 monthly credits
- 學分用於 [Google Cloud Skills Boost](https://www.cloudskillsboost.google/) 的 hands-on labs

### 學分用途

1 學分 ≈ $1 USD。可兌換：
- 單個 Hands-on Lab：1-5 學分
- Skill Badge 任務：5-15 學分
- 完整課程：10-30 學分

建議配置：
- 每月一個 Skill Badge（15 學分）+ 數個基礎 labs（20 學分）

### Get Certified 免費考照

GEAR 會員可申請 Get Certified 計畫（免費考照 voucher）：
- 2026 Edition 1：3/11 截止（已過期）
- 等待下一梯次開放

### 推薦 Skill Badge 路線（用每月 35 學分）

優先拿與現有 GCP 環境直接相關的 badges：

| # | Badge | 時長 | 關聯 |
|:---:|------|:---:|------|
| 1 | **Explore Generative AI in Agent Platform** | 30m | Gemini API + function calling |
| 2 | **Develop Gen AI Apps with Gemini and Streamlit** | 1h | Gemini + Cloud Run 部署 |
| 3 | **Develop Your Google Cloud Network** | 1h15m | IAM、VPC、Compute Engine VM |
| 4 | **Cloud Architecture: Design, Implement, and Manage** | 2h15m | VM、Docker、Cloud SQL |

策略：每月一個 Skill Badge（10-15 學分）+ 數個基礎 labs（剩餘學分），半年集 6 個。

## 相關技能

- `hermes-provider-config` — Gemini API 設定與 cost optimization
- `gemini-models` — 模型選擇與定價
