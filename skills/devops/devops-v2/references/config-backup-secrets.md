# 配置備份機敏資料清理

當將系統配置備份到 Git 或儲存時，確保所有機敏資料已被遮蔽。

## 常見機敏資料

| 類型 | 特徵 | 範例 |
|------|------|------|
| OpenRouter API Key | `sk-or-...` | `api_key: sk-or-v1-abc123...` |
| GitHub PAT Classic | `ghp_...` | `GITHUB_TOKEN=ghp_xxxx...` |
| GitHub PAT Fine-grained | `github_pat_...` | `token: github_pat_abc...` |
| OpenAI API Key | `sk-...` | `OPENAI_API_KEY=sk-xxx...` |
| Telegram Bot Token | 數字:字母 | `TELEGRAM_BOT_TOKEN=123:ABC...` |
| FAL / Firecrawl Keys | 自訂格式 | `FAL_KEY=...` |

## 清理步驟

### 1. 掃描檔案

```bash
grep -rn "sk-or-\|ghp_\|github_pat\|api_key: [a-zA-Z0-9_]\{10,\}" \
  --include="*.txt" --include="*.md" --include="*.yaml" --include="*.yml" \
  vm/ skills/ 2>/dev/null
```

### 2. 遮罩機敏值

```bash
sed -i 's|api_key: sk-or-[^ ]*|api_key: <REDACTED>|g' vm/hermes-config.txt
sed -i 's|GITHUB_TOKEN=.*|GITHUB_TOKEN=<REDACTED>|g' vm/hermes-config.txt
```

### 3. 重寫 Git 歷史（若已提交）

```bash
git add -A
git commit --amend -m "🎉 初始提交：已遮罩 API key"
git push --force
```

### 4. 驗證無殘留

```bash
grep -rn "sk-or-\|ghp_" vm/ skills/ 2>/dev/null | grep -v "REDACTED\|os.environ\|os.getenv"
```
應無輸出（表示全已遮罩）。