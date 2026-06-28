# RAG DB 路徑解析（Hermes Profile 相容）

## 問題

Hermes Agent 在某些配置下會覆寫 `HOME` 環境變數為 profile 目錄
（例如 `/home/user/.hermes/profiles/lenien-gcp/home`），
導致 `os.path.expanduser("~/.hermes/rag/...")` 指向錯誤路徑。

## 修復（2026-06-26）

### 修改位置
`query_rag.py` 中的 `DB_PATH` 解析邏輯。

### 原始程式碼（問題）
```python
DB_PATH = os.path.expanduser("~/.hermes/rag/legal_translation/legal_rag.db")
```

### 修正後（使用系統 passwd 查詢真實家目錄）
```python
import pwd
_HOME = pwd.getpwuid(os.getuid()).pw_dir
# Allow override via env for testing
_HOME = os.environ.get("REAL_HOME", _HOME)
DB_PATH = os.path.join(_HOME, ".hermes/rag/legal_translation/legal_rag.db")
```

### 驗證
```bash
python3 -c "
import pwd, os
real_home = pwd.getpwuid(os.getuid()).pw_dir
print('HOME 環境變數:', os.environ.get('HOME'))
print('實際家目錄:', real_home)
print('RAG DB 存在:', os.path.exists(os.path.join(real_home, '.hermes/rag/legal_translation/legal_rag.db')))
"
```

### 原理
- `pwd.getpwuid(os.getuid()).pw_dir` 不受 `HOME` 環境變數影響
- 直接查系統 `/etc/passwd` 取得真實使用者的家目錄
- 保留 `REAL_HOME` 環境變數覆寫機制，以利測試
