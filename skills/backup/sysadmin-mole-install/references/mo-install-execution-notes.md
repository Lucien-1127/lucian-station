# mo 安裝執行紀錄（2026-06-30）

本技能首次執行於 WSL2 Ubuntu 22.04.5 (Jammy) / kernel 6.6.87.2-microsoft-standard-WSL2。

## 環境摘要

| 項目 | 值 |
|------|-----|
| OS | Ubuntu 22.04.5 LTS（非技能預設的 24.04.4） |
| Shell | bash 5.1.16 |
| WSL 記憶體 | 3.8Gi（總計 15.32GB 實體 RAM） |
| CPU | 4 vCPU (Ryzen 5 7535HS) |
| Git | 2.34.1 |
| Python | 3.11.15 |
| Node | v24.15.0 |
| Docker CLI | WSL 內不可用（但使用者屬於 docker group → Docker Desktop Windows 已安裝） |
| zsh | 未安裝 |

## 安裝過程

1. **APT search**: `apt-cache search mo` → 無相關套件；`apt-cache search mole` → 僅有分子模擬相關套件，非本目標。
2. **官方 README** 確認安裝方式：local install（下載 → `chmod +x` → `mv ~/.local/bin/`）
3. **Workspace 不存在**：`/home/ysga1/workspace/ai/` 需要 `mkdir -p` 建立
4. **`mo --version`**：exit 1 → 不支援版本旗標；改用功能測試 `echo "works" | mo` → 驗證成功

## 最終成果

- 安裝路徑：`/home/ysga1/.local/bin/mo`（59KB）
- 功能驗證：`echo "Hello, {{NAME}}!" | NAME=老闆 mo` → `Hello, 老闆!`
- 無系統修改，無 sudo 使用

## 注意

- 技能描述中稱「Mole」但官方專案名為 `mo`（tests-always-included/mo）
- Dcoker 需從 Windows 端啟用 WSL integration 才能在 WSL 內使用 docker CLI
