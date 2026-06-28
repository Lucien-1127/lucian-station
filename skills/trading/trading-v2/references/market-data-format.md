# 市場數據格式參考

## 標準輸入格式（6 條件決策用）
```json
{
  "symbol": "TICKER",
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

## 決策輸出格式
```json
{
  "skill": "trading",
  "action": "BUY|SELL|HOLD",
  "confidence": 0.92,
  "metadata": {
    "decision_path": [
      "rsi_14=35.2 <40 ✓",
      "adx_14=28.5 >25 ✓",
      "ma20=150.3 > ma50=148.9 ✓",
      "volume_ratio=1.25 >1.2 ✓",
      "max_drawdown_5d=-2.1% >-5% ✓",
      "utilization=80% <= 80% ✓"
    ],
    "kelly_fraction": 0.15,
    "entry_price": 152.00,
    "stop_loss": 147.44,
    "take_profit": 159.60,
    "cost_estimate": 0.08,
    "execution_time_ms": 1200
  },
  "rationale": "6 條件全數通過，ADX 28.5 顯示趨勢確立，量能放大 25% 確認動能",
  "next_action": "EXECUTE"
}
```

## 常見信號失效模式
- **RSI 在震盪市**：RSI <40 但在區間盤整中無趨勢 → ADX <20 時忽略 RSI 信號
- **ADX 高但無方向**：ADX >25 但 +DI 與 -DI 交纏 → 等待方向確認
- **MA 假突破**：價格短暫穿越 MA(20) 但量能不足 → 需量能 >20% 確認
