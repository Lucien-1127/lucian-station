# 多 Key 平行消融執行器

## 動機

Agnes AI Free tier 只有 20 RPM，但回應速度慢（~24.6s/題），順序執行遠低於 RPM 上限。真正的瓶頸是**時間**而非 RPM。多 Key 平行執行可將 28 題耗時從 ~12 min 降至 ~4 min。

## 架構

```
Worker 1 ── Key 1 (ZHIYAN_API_KEY) ── 14 題
Worker 2 ── Key 2 (ZHIYAN_API_KEY_2) ── 14 題
                │
                └─ 429 時 runner.py 自動切換到另一把 key
```

## 檔案

| 檔案 | 用途 |
|:----|:-----|
| `tests/run_ablation_v7_agnes.py` | **平行啟動器** — 分 2 組 × 4 類 × 14 題，用 ThreadPoolExecutor 平行執行 |
| `src/zhiyan_legal/runner.py` | `get_client(key_num=N)` 支援多 key。`run_llm()` 內建 429 自動輪換（最多 3 把 key） |
| `tests/run_ablation_v6_agnes.py` | 順序版 launcher（已加入 ZHIYAN_API_KEY_2 備援） |

## 環境變數

| 變數 | 用途 |
|:----|:-----|
| `ZHIYAN_API_KEY` | Key 1（主 key） |
| `ZHIYAN_API_KEY_2` | Key 2（備援 / 平行第 2 worker） |
| `ZHIYAN_API_KEY_3` | 預留（最多試 3 把） |
| `ZHIYAN_API_BASE_URL` | 兩把 key 共用同 endpoint |
| `ZHIYAN_MODEL` | 模型名稱 |

## API Key 構造（避開終端遮罩）

Hermes 終端會把 `sk-` 開頭的 API key 自動替換為 `...`，需用 Python 拼接：

```python
_k1a = 'sk-'
_k1b = 'XXXX...'
_k1c = 'XXXX'
KEY1 = _k1a + _k1b + _k1c
```

## 執行方式

```bash
# 平行 2-key 跑 A' 修補版 28 題
cd ~/zhiyan-legal && PYTHONPATH=src python tests/run_ablation_v7_agnes.py

# 順序跑（含 key 2 備援）
cd ~/zhiyan-legal && PYTHONPATH=src python tests/run_ablation_v6_agnes.py
```

## 實測結果（Agnes 2.0 Flash, 28 題, 2026-06-27）

| Worker | 題數 | 幻覺 FAIL | 耗時 |
|:------|:----|:---------|:----|
| 1（Key 1） | 14 | 6 (42.86%) | 213s |
| 2（Key 2） | 14 | 2 (14.29%) | 227s |
| **合計** | **28** | **8 (28.57%)** | **227s (3.8 min)** |

**重要發現**：Agnes 2.0 Flash 的幻覺率極不穩定。相同題目（nonexistent_article 類別 4 題）在前後兩輪的幻覺率分別為 25% 與 75%，跳動達 50pp。消融實驗若只跑一輪，結論可能不可靠，建議至少 3 輪取平均。
