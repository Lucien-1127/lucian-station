---
name: debugging-tools
description: 除錯工具集 — Python (pdb/debugpy)、Node.js (Chrome DevTools)、系統性除錯流程
version: 1.0.0
author: Lucian
license: MIT
platforms: [linux, macos, windows]
---

# 除錯工具集

合併自：python-debugpy、node-inspect-debugger、systematic-debugging

---

## 1. Python 除錯

### PDB 互動式除錯

```bash
# 在程式中設中斷點
python3 -c "
import pdb

def divide(a, b):
    result = a / b
    return result

pdb.set_trace()  # 執行到此處暫停
print(divide(10, 2))
"
```

常用指令：`n`（下一行）、`s`（進入函式）、`c`（繼續）、`p var`（印變數）、`q`（離開）

### Debugpy 遠端除錯（DAP 協定）

```bash
# 安裝
pip install debugpy

# 啟動除錯伺服器（等待連線）
python3 -m debugpy --listen 0.0.0.0:5678 --wait-for-client script.py

# 或在程式中嵌入
python3 -c "
import debugpy
debugpy.listen(('0.0.0.0', 5678))
debugpy.wait_for_client()
print('除錯器已連線')
"
```

## 2. Node.js 除錯

透過 `--inspect` 使用 Chrome DevTools 協定除錯。

```bash
# 啟動除錯模式
node --inspect script.js
# 輸出: ws://127.0.0.1:9229/xxx

# 除錯並在第一行暫停
node --inspect-brk script.js

# 使用 Chrome DevTools CLI 連線
node -e "
const inspector = require('inspector');
const session = new inspector.Session();
session.connect();

session.post('Debugger.enable');
session.post('Runtime.evaluate', { expression: 'console.log(\"hello\")' });
"
```

## 3. 系統性除錯流程（4 階段）

當面對不明錯誤時，按以下順序逐步縮小範圍：

### 第一階段：理解錯誤

```bash
# 讀取完整的錯誤訊息與堆疊追蹤
# 確認：是什麼錯誤？在哪一行？什麼時候開始出現？
echo "錯誤訊息: $ERROR_MSG"
```

### 第二階段：重現問題

```bash
# 建立最小可重現範例
cat > /tmp/repro.py << 'EOF'
# 最小化重現問題的程式碼
EOF
python3 /tmp/repro.py
```

### 第三階段：隔離根因

二分法搜尋：註解掉一半程式碼、加入斷點、檢查變數。

### 第四階段：修復與驗證

1. 撰寫最小修復
2. 確認修復後錯誤消失
3. 執行完整測試確保沒回歸
