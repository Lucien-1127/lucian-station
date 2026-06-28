# zhiyan-legal 專案參考

## 專案架構

```
zhiyan-legal/
├── src/zhiyan_legal/
│   ├── __init__.py        # 套件標記
│   ├── __main__.py        # python -m zhiyan_legal 入口
│   ├── cli.py             # CLI 入口（argparse）
│   ├── router.py          # 關鍵字 → 任務路由
│   ├── loader.py          # 文件載入 + compose + token 估算
│   ├── manifest.py        # 文件清單 + resolve_doc + get_load_order
│   └── runner.py          # OpenAI-compatible API 呼叫
├── tests/
│   ├── test_routing.py    # 路由邏輯測試
│   ├── test_loader.py     # loader 測試（tempfile fixtures）
│   └── test_manifest.py   # manifest 測試（monkeypatch tempfile）
├── docs/                  # 系統提示詞文件
├── pyproject.toml
└── .env.example
```

## 測試慣例

```bash
cd /path/to/zhiyan-legal
source .venv/bin/activate
PYTHONPATH=src python -m pytest tests/ -v
```

- 使用 `PYTHONPATH=src` 而非 `pip install -e .`
- 所有測試用 `sys.path.insert(0, ...)` + 相對 import
- loader/manifest 測試用 `tempfile.TemporaryDirectory` + `monkeypatch` 隔離
- 當前 56 個測試案例，三個測試檔

## 文件載入路由系統

router.py 使用 `KEYWORD_MAP` (dict[str, str]) 做關鍵字 → 任務映射。
按關鍵字長度排序（最長優先）避免子字串衝突。

路由優先序：
1. SAFETY（覆蓋一切）
2. LITIGATION
3. MODE 路由（QC > RESEARCH > REPORT）
4. PERSONA（CONSULTANT > TA > TUTOR > LEGAL_WRITER）
5. 預設 CONSULTANT

邊界保護：`"殺"` 使用 `_keyword_in_text()` 檢查前後是否為 CJK。
`"告"` 已移除單字 key，改用複合詞（告人/告他/被告/提告/告訴/控告）。
`"查"` 無邊界保護（中文中常用作獨立動詞）。

## manifest.py 文件載入

- `resolve_doc(subdir, filename)` → 先找 docs/，fallback 到 SKILL_DIR
- `get_load_order(task)` → core layers + task layers，去重
- SKILL_DIR 可透過 `ZHIYAN_SKILL_DIR` 環境變數覆蓋

## 文件

- `CHANGELOG.md` — 專案根目錄，記錄每次重要變更
- `README.md` — 中英雙語文件，各有一份 provider 表格和 code block 範例
- `.env.example` — 被 `scripts/setup.sh` 參考作為互動式安裝範本

## ⚠️ Provider/Model 文件同步檢查清單

當更新 API provider 或模型範例時，必須同步以下 **7 個位置**，缺一不可：

| # | 檔案 | 內容類型 |
|---|------|---------|
| 1 | `.env.example` | Provider 選項 + model 範例（6 options） |
| 2 | `README.md` — English provider table | Provider + URL + model 表 |
| 3 | `README.md` — English code block | `ZHIYAN_MODEL=gpt-...` 內嵌範例 |
| 4 | `README.md` — Chinese provider table | Provider + URL + model 表 |
| 5 | `README.md` — Chinese code block | `ZHIYAN_MODEL=gpt-...` 內嵌範例 |
| 6 | `scripts/setup.sh` | Provider 選單文字 |
| 7 | `src/zhiyan_legal/runner.py` | Module docstring provider 列表 |

**常見陷阱**：只改了 `.env.example` 和英文表，漏了中文表和 `setup.sh`，造成文件不一致。

**2026/06 最後一次更新**：
- GPT-4o → 退役，改 GPT-5.1
- deepseek-chat → 棄用，改 deepseek/deepseek-v4-flash
- gemini-2.5-flash → 改 gemini-3-flash-preview
- claude-sonnet-4 → 改 claude-sonnet-4.6
- Xiaomi MiMo → 移除，改 MiniMax M3 / NVIDIA Nemotron 3 Super
