# Gemini API Rate Limits & Pool Strategy（2026-06）

官方來源：[Pricing](https://ai.google.dev/gemini-api/docs/pricing) · [Rate Limits](https://ai.google.dev/gemini-api/docs/rate-limits)

## 費用驗證規則

**設定模型前必須查官方定價頁**，不可憑記憶或第三方文章。信心 < 90% 強制標 🔴。

## Rate Limit 三維度

| 維度 | Free Tier | Tier 1（付費/預付制） |
|------|:---:|:---:|
| RPM（每分鐘請求） | ~10 | ~200-2000 |
| TPM（每分鐘 tokens） | ~1M | ~4M |
| RPD（每日請求） | ~1,500 | 無硬上限 |

> ⚠️ 官方頁面**未公布精確 RPM 數字**，實際配額在 [AI Studio Rate Limit 頁](https://aistudio.google.com/rate-limit) 查看。

## Spend-Based Limit（Tier 1 專有）

| Tier | Spend limit / 10min |
|------|:---:|
| Free | N/A（不收費） |
| Tier 1 | **$10** |
| Tier 2 | $200 |
| Tier 3 | $200 |

對 gemini-3.1-flash-lite（$0.25/$1.50 per 1M），$10/10min = 40M input 或 6.6M output tokens，幾乎不可能觸發。

## 模型定價對照

| 模型 | Free Tier | Paid Standard | Priority |
|------|:---:|:---:|:---:|
| gemini-3.1-flash-lite | 🆓 | $0.25/$1.50 | $0.45/$2.70 |
| gemini-3.5-flash | 🆓 | $1.50/$9.00 | $2.70/$16.20 |
| gemini-3.1-pro-preview | ❌ | $2.00/$12.00 | $3.60/$21.60 |
| gemini-3-flash-preview | 🆓 | $0.50/$3.00 | — |

## Pool 優先序策略

```
Priority 1: 預付制 Key（Tier 1，高 limit，資料不外洩）
Priority 2-4: 免費帳號 Key（Free Tier，獨立配額，做 fallback）
```

### 原因
- Tier 1 的 RPM/TPM 遠高於 Free Tier
- Paid tier 內容**不用於模型訓練**（法律 workflow 關鍵）
- 預付制 Key 用 3.1-flash-lite 在 Standard routing 下同樣不扣 credit
- 免費 Key 的流量會被 Google 用於訓練

### 注意
- 免費配額綁定 Google API Project，同帳號多 Key **不能**疊加配額
- 必須用不同 Google 帳號 → 不同 Project → 獨立配額

## 2026-04 免費層變化

- Gemini 3.x Pro 全系列移出免費層，只剩 Flash 系列繼續免費
- 付費帳號 Tier 1 上限 $250/月，達標後 API 自動暫停
