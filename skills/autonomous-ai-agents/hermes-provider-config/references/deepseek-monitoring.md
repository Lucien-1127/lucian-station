# DeepSeek 用量監控

## 查詢餘額

```bash
curl -s https://api.deepseek.com/user/balance \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY"
```

回傳格式：
```json
{
  "is_available": true,
  "balance_infos": [{
    "currency": "USD",
    "total_balance": "9.13",
    "granted_balance": "0.00",
    "topped_up_balance": "9.13"
  }]
}
```

- `total_balance` — 總餘額
- `granted_balance` — 贈送額度（通常為 0）
- `topped_up_balance` — 儲值金額

## 每日餘額監控腳本

儲存到 `~/.hermes/profiles/<profile>/scripts/deepseek_balance.sh`：

```bash
#!/bin/bash
# DeepSeek Balance Monitor
set -e

# Source API keys from Hermes .env
ENV_FILE="$HOME/.hermes/profiles/lenien-gcp/.env"
[ -f "$ENV_FILE" ] && set -a && source "$ENV_FILE" && set +a

if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "❌ DEEPSEEK_API_KEY not found"
    exit 1
fi

BALANCE=$(curl -sf https://api.deepseek.com/user/balance \
    -H "Authorization: Bearer ${DEEPSEEK_API_KEY}" | \
    python3 -c "import sys,json; d=json.load(sys.stdin); print(d['balance_infos'][0]['total_balance'])")

if [ -z "$BALANCE" ]; then
    echo "❌ 無法查詢 DeepSeek 餘額"
    exit 1
fi

THRESHOLD=2.00

if python3 -c "exit(0 if float('${BALANCE}') >= ${THRESHOLD} else 1)"; then
    echo "💰 DeepSeek 餘額：\$${BALANCE} (安全)"
else
    echo "🔴 DeepSeek 餘額僅剩 \$${BALANCE}！低於 \$${THRESHOLD}，請儲值！"
fi
```

## Hermes cron 設定

每日台灣時間下午 6 點推送餘額到 Telegram：

```bash
# cronjob action=create 或直接用 hermes cron
hermes cron create \
  --schedule "0 10 * * *" \
  --name "DeepSeek 每日餘額監控" \
  --script "deepseek_balance.sh" \
  --no_agent
```

> `--no_agent`：腳本 stdout 直接推送 Telegram，不經過 LLM。腳本路徑相對於 `~/.hermes/profiles/<profile>/scripts/`，`--script` 只給檔名不帶目錄。

## 警報邏輯

- 餘額 ≥ $2 → 顯示「安全」
- 餘額 < $2 → 🔴 警告 + 提示儲值

可調 `THRESHOLD` 變數改變警示門檻。

## 注意

- DeepSeek 沒有原生用量 dashboard，只能靠 `/user/balance` API
- 餘額用完 API 回 `402 Payment Required`
- Hermes telemetry plugin（`hermes-telemetry`）可記錄每次呼叫的 token 用量和費用
- cron 執行環境無法自動讀取 `.env`，腳本需手動 `source`
