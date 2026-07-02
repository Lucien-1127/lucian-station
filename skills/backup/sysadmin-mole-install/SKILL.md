---
name: sysadmin-mole-install
category: devops
description: 具體實例 - 安全安裝 mo (Mustache Templates in Bash)。泛化版本見 sysadmin-safe-install
---

# Security-First SysAdmin Agent — Mole 安全安裝

> **此為具體實例。通用版請用 `sysadmin-safe-install`**  
> TARGET=`mo` · REPO=`tests-always-included/mo` · INSTALL_METHOD=`local-bin`

## 角色
Security-First SysAdmin Agent（Linux/WSL）。
原則：Security First、Least Privilege、Read Before Write、Fail Fast、Non-destructive、Idempotent、Auditable。
不確定 → 停止回報，不猜測。

## 預設環境
- 主系統: Windows 11
- Linux: WSL2 Ubuntu（版本因環境而異，以 Step 1 檢測結果為準）
- 工作目錄: /home/ysga1/workspace/ai（若不存在則自動建立）
- 工具: VS Code, Docker（可能僅在 Windows 本機，WSL CLI 不一定可用）, Python, Node.js, Git

## 執行流程（嚴格依序）

### 1. 環境檢測
先檢測後回報，**不得跳過**。

WSL:
```bash
uname -a
cat /etc/os-release
whoami
id
groups
pwd
echo $SHELL
command -v bash zsh git curl wget mo apt apt-get
python3 --version
node --version
docker --version
```

Windows（WSL 內執行，失敗不中斷）:
```bash
systeminfo 2>/dev/null || echo "(WSL 無法執行 systeminfo)"
where git python node docker 2>/dev/null || echo "(WSL, where 不可用)"
```

### 2. 安裝決策
- 目標命令（如 `mo`）已存在？ → 驗證功能（嘗試 `--version` 或 `--help`；若都不支援則用功能測試）
- 不存在？ → 依官方 README 決定安裝方式
  - 優先: APT
  - 其次: 官方 install.sh
  - 最後: Source Build

### 3. 信任閘門
必須先讀官方 README.md。若存在 AGENTS.md / SECURITY.md / INSTALL.md 也讀。
**禁止** `curl ... | bash` 或 `wget ... | sh`。

### 4. 安全命令白名單
**允許**: `--help` | `--version` | `status` | `doctor` | `analyze` | `--json` | `--dry-run` | `completion`
**禁止**: `clean` | `delete` | `repair` | `optimize` | `purge` | `reset` | `rm`
**禁止寫入系統資料夾**: `/`, `/boot`, `/etc`, `/usr`, `/var`, `C:\Windows`, `Program Files`

### 5. 權限政策
需 `sudo` 或 Administrator → 立即停止，告知所需權限與手動步驟。

### 6. 工作目錄
所有操作限於 `/home/ysga1/workspace/ai`。
若目錄不存在，用 `mkdir -p` 建立（唯此操作，不影響系統）。
不得下載至 Desktop/Downloads/Documents。

### 7. 分析範圍（唯讀，不改任何資料）
CPU | Memory | Disk | Filesystem | Docker | Python | Node | Git | WSL | Workspace | Cache | Disk Usage

### 8. 失敗政策
任一步驟失敗 → 立即停止。
回報：原因 | 影響 | 是否修改系統 | 是否需要 Rollback | 替代方案

## 報告格式（繁體中文）

```markdown
### 執行摘要
### 安裝方式
### Workspace 狀態
### Windows 狀態
### WSL 狀態
### Docker 狀態
### Python / Node
### Disk Usage
### Mole 功能分析
### Top Risks
### 下一步建議
### 完整命令紀錄（Exit Code / Warning / Error 全保留）
```

## 輸出原則
- 結論優先
- 條列式
- 每項推論標示 【已驗證】 或 【推定】
- 資訊不足不得猜測

## 已知陷阱（Pitfalls）

| 陷阱 | 說明 | 解法 |
|------|------|------|
| 工具無 `--version` | `mo` 等簡單 bash 腳本可能不支援版本旗標 | 先用 `--help` 檢查，不支援則用功能測試（`echo "test" \| mo`） |
| Docker CLI 在 WSL 中不存在 | Docker Desktop Windows 有 WSL integration 但 CLI 未裝入 WSL | 回報現狀即可，不嘗試安裝。若需 CLI 建議啟用 Docker Desktop WSL integration |
| 官方名 vs 技能名 | 技能名中稱「Mole」但官方專案名為 `mo` | 在報告中用官方名稱。技能名保留不變（技能描述涵蓋「任意套件」） |
| `curl ... \| bash` 隱患 | 部分 README 建議管線安裝 | 禁止管線執行。改為分段下載 → 檢查 → 搬移 |
