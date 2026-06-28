# 免費 API 模型探索指南

## 如何尋找可用的免費 API 模型

### OpenRouter 免費模型

OpenRouter 提供持續更新的免費模型清單，在專屬 collection 頁面：
https://openrouter.ai/collections/free-models

快速查詢方式：
```bash
# 獲取免費模型清單 (JSON)
curl -s "https://openrouter.ai/api/v1/models" | python3 -c "
import json, sys
models = json.load(sys.stdin)
for m in models.get('data', []):
    pricing = m.get('pricing', {})
    # 檢查 input 與 output 是否均為 $0
    input_cost = float(pricing.get('input', 1))
    output_cost = float(pricing.get('output', 1))
    if input_cost == 0.0 and output_cost == 0.0:
        ctx = m.get('context_length', '?')
        print(f'{m[\"id\"]}  context={ctx}')
"
```

注意事項：
- 免費模型可能隨時下架或改為收費
- 部分免費模型有每日請求次數限制（取決於帳戶 credit）
- `openrouter/free` 路由會自動選用可用免費模型
- 免費模型通常不支援長 context (多數 128K-262K，少數如 Owl Alpha 達 1M)

### 常見免費模型類型

| 類型 | 例子 | 適合 |
|------|------|------|
| 小型 dense (3B-9B) | Nemotron Nano 9B, GLM 4.5 Air | 簡單任務、分類、摘要 |
| 中型 dense (12B-31B) | Gemma 4 31B, Owl Alpha | 推理、coding、agentic |
| MoE (大參數少活化) | Nemotron 3 Ultra (550B/55B), GPT-OSS (117B/5B) | 高品質推理、長 context |
| 專用 coding | Laguna M.1, Kimi K2.6 | 程式碼生成、多 agent |

### 評估免費 vs 本機的取捨

| 因素 | 免費 API | 本機 Ollama |
|------|---------|------------|
| 速度 | 伺服器端，通常快 | 取決於本機硬體 |
| 可靠性 | 可能限流、排隊 | 穩定，但慢 |
| 模型大小 | 可跑超大模型 (31B+) | 受限於 RAM/VRAM |
| 隱私 | 資料經過第三方 | 完全本機 |
| 成本 | $0（但有隱性限制） | 電費 |
| Context | 可能受限 | 256K 可用 |

建議策略：**API 為主，本機為輔** — 日常用免費 API，本機 Ollama 當備用或離線方案。
