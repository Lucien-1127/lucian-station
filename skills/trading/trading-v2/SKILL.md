---
name: trading-v2
description: 股票/ETF 交易決策與執行管理 — 6 條件 AND 邏輯，Kelly 分數，風險控制
version: 2.0.0
author: Lucian
trigger: "用戶輸入包含「買」「賣」「交易信號」「股票」或系統提示詞識別 skill: trading"
---

# Trading Skill v2.0

## 用途
股票 / ETF 交易決策與執行管理。

## 決策框架 — 6 條件 AND 邏輯

### 買入信號
所有 6 條必須同時滿足，否則禁止交易（輸出 HOLD）：

1. **RSI(14) < 40** — 超賣確認
2. **ADX(14) > 25** — 趨勢強度
3. **MA(20) > MA(50)** — 短期向上突破
4. **成交量 > 前 20 日均 +20%** — 量能確認
5. **過去 5 日最大跌幅 < 5%** — 風險緩衝
6. **持倉利用率 < 80%** — 資金安全邊際

### 賣出信號（任一觸發即執行）
- +5% 目標達成 **OR**
- -3% 止損觸發 **OR**
- ADX < 15（趨勢減弱） **OR**
- 重大新聞事件（灰天鵝）

### 輸入格式
```json
{
  "symbol": "AAPL",
  "market_data": {
    "rsi": 35.2,
    "adx": 28.5,
    "ma20": 150.30,
    "ma50": 148.90,
    "volume_20d_avg": 52000000,
    "current_volume": 65000000,
    "max_drawdown_5d": -2.1
  },
  "account": {
    "cash": 10000,
    "position_value": 40000,
    "max_loss_tolerance": 0.03
  }
}
```

## 執行步驟
1. 驗證所有 6 條件（任何失敗 → HOLD）
2. 計算 Kelly 分數：成功率 × 報酬率 / 風險
3. 設定 stop_loss = entry × (1 - 0.03)
4. 設定 take_profit = entry × 1.05
5. 記錄決策理由（用於 Curator 評分）

## 參考文件
- `references/market-data-format.md` — 標準輸入/輸出格式與常見信號失效模式

## 禁止事項
- ❌ 單筆持倉 > 30% 帳戶
- ❌ 日交易 > 3 筆
- ❌ 追漲殺跌
- ❌ 無根據推測

## 成本與參數
- 溫度：0.2（決策確定性優先）
- 最大輸出 Token：512
- 信心閾值：92%
- 成本上限：$0.20/次
- 延遲目標：<2.5s