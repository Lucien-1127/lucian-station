# Gemini 混合策略配置範例（2026-06）

本文件記錄在 `lenien-gcp` 專案上驗證過的混合策略命令序列。

## 策略

| 任務 | 模型 | 理由 |
|------|------|------|
| Vision | `gemini-3.5-flash` | 法律文件品質優先 |
| Compression | `gemini-3.5-flash` | 上下文不能壓錯 |
| Title | `gemini-3.1-flash-lite` | 一句話即可 |
| Fallback | `gemini-3.1-flash-lite` | 備援夠用 |
| Curator（技能整理） | `gemini-3.1-flash-lite` | 每週一次，不急，免費跑 |
| Profile Describer | `gemini-3.1-flash-lite` | 定期背景任務，輕量即可 |

## 完整指令序列

```bash
# 1. Vision + Compression 用 3.5-flash（品質敏感）
hermes config set auxiliary.vision.model gemini-3.5-flash
hermes config set auxiliary.compression.model gemini-3.5-flash

# 2. Title + Fallback + Curator + Profile 用 3.1-flash-lite（輕量即可，免費）
hermes config set auxiliary.title.model gemini-3.1-flash-lite
hermes config set fallback_providers.0.model gemini-3.1-flash-lite
hermes config set auxiliary.curator.provider gemini
hermes config set auxiliary.curator.model gemini-3.1-flash-lite
hermes config set auxiliary.profile_describer.provider gemini
hermes config set auxiliary.profile_describer.model gemini-3.1-flash-lite

# 3. OpenRouter fallback 第二、三層（免費備援模型）
hermes config set fallback_providers.1.provider openrouter
hermes config set fallback_providers.1.model meta-llama/llama-4-scout-17b-16e-instruct
hermes config set fallback_providers.2.provider openrouter
hermes config set fallback_providers.2.model qwen/qwen3-32b:free

# 4. 驗證
grep -A3 "fallback_providers:" ~/.hermes/profiles/lenien-gcp/config.yaml
grep -A4 "curator:\|profile_describer:\|vision:\|compression:\|title:" ~/.hermes/profiles/lenien-gcp/config.yaml | grep -E "provider:|model:"
```

## Key Pool 建議優先序

```
Priority 1: gemini-key-3（預付制，Tier 1，高 rate limit，資料不外洩）
Priority 2: gemini-key-2（Free tier，fallback）
Priority 3: gemini-key-4（Free tier，備援）
Priority 4: gemini-key-5（Free tier，備援）
```

## 成本

Free Tier 下四個 Key 都完全免費（gemini-3.5-flash 和 3.1-flash-lite 皆支援 Free Tier）。
唯一會扣費的是 gemini-key-3（預付制）走 Priority routing 或使用非 Flash 模型時，
但在 Standard routing + Flash 模型下同樣不收費。
