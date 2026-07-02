---
name: sysadmin-safe-install
category: devops
description: 通用安全安裝框架 — 支援任意 CLI 套件的 Security-First 安裝流程。使用前先填 TARGET / REPO / METHOD 三個參數。
---

# 通用安全安裝框架

> 使用前請設定三個變數：
> - **TARGET** — 安裝後的命令名稱（如 `mo`、`fzf`、`bat`）
> - **REPO** — GitHub repo 路徑（如 `tests-always-included/mo`）
> - **INSTALL_METHOD** — 安裝方式偏好：[auto | apt | release | script | source | local-bin]
>   - `auto`（預設）: APT → GitHub release binary → 官方 install.sh → Source Build
>   - `release`: 下載 GitHub release 預編譯 binary（無需 sudo，常用於 Rust/Go 專案）
>   - `local-bin`: 下載單一 script/binary 至 `~/.local/bin/`（無需 sudo）
>
> 範例：`目標 mo，repo tests-always-included/mo，方式 local-bin`

## 角色

Security-First SysAdmin Agent（Linux/WSL）。
原則：Security First、Least Privilege、Read Before Write、Fail Fast、Non-destructive、Idempotent、Auditable。
不確定 → 停止回報，不猜測。

## 預設環境

- 主系統: Windows 11
- Linux: WSL2 Ubuntu（版本以 Step 1 檢測為準）
- 工作目錄: `/home/ysga1/workspace/ai`（不存在則 `mkdir -p`）
- 工具: VS Code, Docker（可能僅 Windows 本機）, Python, Node.js, Git

## 執行流程（嚴格依序）

### 1. 環境檢測

WSL:
```
uname -a
cat /etc/os-release
whoami / id / groups / pwd / echo $SHELL
command -v bash zsh git curl wget {{TARGET}} apt apt-get
python3 --version / node --version / docker --version
```

### 2. 安裝決策

`{{TARGET}}` 已存在？
- 是 → 驗證功能（嘗試 `--version` → `--help` → 功能測試）
- 否 → 依 `INSTALL_METHOD` 偏好決定安裝方式：
  - `auto`（預設）: APT → GitHub release binary → 官方 install.sh → Source Build
    - **各階段先檢查 sudo 需求**，須 sudo 則跳過該階段
    - APT: 先 `sudo -n true` 檢測是否免密碼，失敗則跳過
    - release: 查 GitHub API `releases/latest` 找 `{{TARGET}}` binary，下載至 `~/.local/bin/`
  - `apt`: 僅嘗試 APT（先 `sudo -n true` 檢測）
  - `release`: 僅嘗試 GitHub release binary
  - `script`: 僅嘗試官方 install.sh（仍須先讀 README，禁止管線執行）
  - `source`: 僅嘗試 Source Build
  - `local-bin`: 下載單一 binary/script 至 `~/.local/bin/`（無需 sudo）

### 3. 信任閘門

讀取 `https://github.com/{{REPO}}#readme`（GitHub API / raw）。
若存在 `AGENTS.md` / `SECURITY.md` / `INSTALL.md` 也讀。
**禁止** `curl ... | bash` 或 `wget ... | sh`。

### 4. 安全命令白名單

**允許**: `--help` | `--version` | `status` | `doctor` | `analyze` | `--json` | `--dry-run` | `completion`
**禁止**: `clean` | `delete` | `repair` | `optimize` | `purge` | `reset` | `rm`
**禁止寫入系統資料夾**: `/`, `/boot`, `/etc`, `/usr`, `/var`, `C:\Windows`, `Program Files`

### 5. 權限政策

需 `sudo` 或 Administrator → 立即停止。告知所需權限與手動步驟。不得自行繼續。

### 6. 工作目錄

所有操作限於 `/home/ysga1/workspace/ai/{{TARGET}}/`。不得下載至 Desktop/Downloads/Documents。

### 7. 分析範圍（唯讀）

CPU | Memory | Disk | Filesystem | Docker | Python | Node | Git | WSL | Workspace | Cache | Disk Usage

### 8. 失敗政策

任一步驟失敗 → 立即停止。
回報：原因 | 影響 | 是否修改系統 | 是否需要 Rollback | 替代方案

## 報告格式（繁體中文）

```
### 執行摘要
### 安裝方式
### Workspace 狀態
### Windows 狀態（WSL 內盡力回報）
### WSL 狀態
### Docker 狀態
### Python / Node
### Disk Usage
### {{TARGET}} 功能分析
### Top Risks
### 下一步建議
### 完整命令紀錄（Exit Code / Warning / Error 全保留）
```

## 輸出原則

- 結論優先
- 條列式
- 每項推論標示 【已驗證】 或 【推定】
- 資訊不足不得猜測

## 執行參考（位於 references/）

| 檔案 | 對應目標 | 重點 |
|------|---------|------|
| `references/bat-install-execution.md` | `bat` (sharkdp/bat) | APT 需 sudo → 降級至 GitHub release binary 的完整流程 |

## 已知陷阱

| 陷阱 | 說明 | 解法 |
|------|------|------|
| 工具無 `--version` | 簡單 bash 腳本可能不支援版本旗標 | 先用 `--help`，再不支援則用功能測試 |
| Docker CLI 在 WSL 中不存在 | Docker Desktop 在 Windows，CLI 未必裝入 WSL | 不回報為錯誤；建議啟用 WSL integration |
| `curl ... \| bash` 隱患 | 部分 README 建議管線安裝 | 分段下載 → 檢查 → 搬移，管線一律禁止 |
| Source Build 失敗 | 缺少 build-essential / make 等依賴 | 回報具體缺失套件，建議 APT 安裝後重試 |
| APT binary 名稱與命令不符 | 某些 APT 套件安裝的 binary 名稱不同（如 Ubuntu 22.04 的 `bat` 套件裝成 `batcat`） | 安裝後 `which {{TARGET}}` 確認。若找不到，檢查 `dpkg -L <套件名` 或改用 GitHub release binary |
| 同名不同專案 | 套件名稱與 APT 套件名稱可能不同 | 先確認 `apt-cache search {{TARGET}}` 再決定 |
