---
name: devops-v2
description: 系統監控、效能優化、自動維護 — 三層閾值 (CPU/Memory/Disk) + 清理管線
version: 2.1.0
author: Lucian
trigger: "輸入包含「CPU」「記憶體」「磁碟」「監控」「優化」「效能」，或 Curator 定時觸發維護"
---

# DevOps Skill v2.0

## 用途
系統監控、當機診斷、效能優化、自動維護任務。

## 監控指標（三層閾值）

| 指標 | 正常 | 警告 (🟡) | 危急 (🔴) | 行動 |
|------|------|---------|---------|------|
| CPU | <70% | 70–85% | >85% | SKIP high-load task |
| Memory | <80% | 80–90% | >90% | Kill non-essential / Notify |
| Disk | <80% | 80–90% | >90% | Cleanup / Archive |
| Swap | 有配置 | 無 swap | — | 建立 /swapfile（RAM 的 25-50%） |

## 當機診斷管線（由淺入深）

當使用者回報 VM 不穩定/常當機，依序執行以下診斷：

### Phase 1 — 快照指標（5 指令）
```bash
uptime                                    # 運行時間 & load average
who -b; last -x -F reboot shutdown | head -20  # 開機歷史
free -h; swapon --show                    # 記憶體 & swap
df -h; df -i | head -20                   # 磁碟 & inode
ps aux --sort=-%cpu | head -10            # 最吃 CPU 的 process
ps aux --sort=-%mem | head -10            # 最吃記憶體的 process
```

### Phase 2 — kernel & 硬體層（3 指令）
```bash
sudo dmesg --level=emerg,alert,crit,err,warn | tail -60   # kernel 錯誤
sudo sgdisk -v /dev/nvme0n1 2>/dev/null                   # GPT 完整性（若 NVMe）
sudo fdisk -l /dev/nvme0n1 2>/dev/null | grep "Disk"      # 磁碟幾何 & GPT type
```

常見 kernel 錯誤訊號：
- `Alternate GPT header not at the end of the disk` → GPT 備份標頭損毀，`sgdisk -e` 修復
- `NVRM: No NVIDIA GPU found` → 無 GPU 機器裝了 NVIDIA 驅動，移除
- `Out of memory` / `oom_kill` → 記憶體不足，檢查 leak 或加 swap
- `GPT:Primary header thinks Alt. header is not at the end` → 同上 GPT 問題

### Phase 3 — systemd & 服務層（3 指令）
```bash
sudo systemctl --failed                                    # 失敗服務
sudo journalctl -p 0..3 --no-pager -n 50                   # 嚴重/錯誤日誌
sudo journalctl -g "oom_kill|OOM|Out of memory|killed process" -n 30  # OOM
```

### Phase 4 — 日誌 & crash dump
```bash
ls -la /var/crash/          # apport crash reports
sudo journalctl -u sshd --no-pager -n 20   # SSH 錯誤（暴力攻擊）
sudo journalctl --vacuum-time=3d           # 壓縮舊日誌
cat /var/log/kern.log | grep -i "nvidia\|NVRM\|panic\|oom"  # kernel log 專屬檢查
cat /var/lib/gce-accelerator/shipped-nvidia-version 2>/dev/null  # GCE GPU flag 殘留
```

## 修復行動檢查清單

發現問題後，按優先級逐項修復：

1. **GPT 分割表損毀** → `sudo sgdisk -e /dev/nvme0n1`（重建備份 GPT header）
2. **無 swap** → `fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile`，寫入 `/etc/fstab`
3. **多餘驅動**（NVIDIA 等無 GPU 機器） → 完整清理序列：
   ```bash
   # 步驟 1: purge 所有 nvidia 套件
   sudo apt-get purge -y nvidia-* linux-modules-nvidia-* libnvidia-*
   # 步驟 2: 清除 GCE accelerator 旗標（防下次開機自動載入）
   echo "" | sudo tee /var/lib/gce-accelerator/shipped-nvidia-version
   # 步驟 3: 加入 modprobe 黑名單（封鎖 nvidia/nvidia_drm/nvidia_modeset/nvidia_uvm）
   sudo tee /etc/modprobe.d/blacklist-nvidia.conf <<'EOF'
   blacklist nvidia
   blacklist nvidia_drm
   blacklist nvidia_modeset
   blacklist nvidia_uvm
   EOF
   # 步驟 4: 刪除殘留 systemd unit
   sudo rm -f /etc/systemd/system/nvidia-fabricmanager.service \
             /etc/systemd/system/nvidia-persistenced.service
   # 步驟 5: 重建 initramfs（purge 不一定會自動做）
   sudo update-initramfs -u -k all
   # 步驟 6: 刪除舊 kernel 的 initramfs（可能含 nvidia 殘留設定）
   ls /boot/initrd.img-*generic* 2>/dev/null | while read f; do
     [ -f "$f" ] && lsinitramfs "$f" | grep -q nvidia && sudo rm -v "$f"
   done
   # 步驟 7: 清理 systemd 記憶的失敗狀態
   sudo systemctl reset-failed nvidia-fabricmanager.service 2>/dev/null
   sudo systemctl reset-failed nvidia-persistenced.service 2>/dev/null
   sudo systemctl daemon-reload
   ```
   ⚠️ **常見陷阱**：purge 後 initramfs 不一定會自動重建。務必手動執行 `update-initramfs -u -k all`，且檢查所有 kernel 版本的 initramfs 是否有 nvidia 殘留。GCE VM 的 `/var/lib/gce-accelerator/shipped-nvidia-version` 旗標若未清除，下次開機仍會嘗試載入 nvidia。
4. **OOM 風險** → 確認 swap 已建立，檢查是否有 leak（`ps aux --sort=-%mem` 高駐留程序）
5. **系統過期** → `apt upgrade -y`，有 kernel 更新需提示重啟
6. **GPT partition table entries not in disk order** → 通常是 cloud-init image 的正常現象，不處理

## 自動化清理清單
1. **暫存檔** — ~/.cache/, /tmp/ (>7 日)
2. **舊日誌** — /var/log/ (>30 日)，journalctl --vacuum-time=3d
3. **孤立進程** — Zombie / Defunct 進程清理（`ps aux | awk '$8 ~ /Z/ {print $2}' | xargs kill`）
4. **套件快取** — `apt-get clean` 清理 /var/cache/apt/，`pip cache purge`
5. **crash reports** — /var/crash/ 內的非核心 crash 可清除
6. **套件更新** — 檢查更新列表，提示使用者

## 執行步驟
1. 收到系統問題回報 → 先確認「當機」還是「慢」
2. 慢 → 直接 Phase 1 + cleanup
3. 當機/不穩定 → 完整 Phase 1→2→3→4
4. 依修復檢查清單執行修復
5. 最終驗證（不可跳過，確認無錯誤才可停止）：
   ```bash
   # 系統基本
   uptime
   free -h
   swapon --show
   df -h /
   sudo systemctl --failed
   # NVIDIA 特定驗證
   modprobe --dry-run nvidia 2>&1                   # FATAL=已封鎖
   cat /etc/modprobe.d/blacklist-nvidia.conf 2>/dev/null   # 確認黑名單存在
   cat /var/lib/gce-accelerator/shipped-nvidia-version     # 應為空
   ls /etc/systemd/system/nvidia* 2>/dev/null || echo "(無殘留)"
   lsinitramfs /boot/initrd.img-$(uname -r) | grep nvidia || echo "(initramfs 乾淨)"
   # 記憶體/磁碟
   ps aux --sort=-%mem | head -5
   ```
6. 若任何驗證項目失敗 → 回到步驟 4 補修復，**必須確認 10 項全過才能回報完成**

## 禁止事項
- ❌ 在 CPU >85% 時執行清理（避免雪崩）
- ❌ 刪除關鍵系統檔案（whitelist only）
- ❌ 無詢問殺死關鍵進程
- ❌ 修改 cloud-init 產生的分割表配置（GPT partition order warnings 可忽略）
- ❌ 無確認就重啟 VM（kernel 更新需使用者同意）
- ❌ 修復後跳過最終驗證就回報完成 — 必須確認所有檢查項目全過（failed services=0, initramfs 無殘留, 模組不可載入等）

## 參考文件
- `references/gcp-vm-diagnostics.md` — GCP 雲端 VM 專屬檢查項目

## SSH 連線穩定性（行動裝置適用）

行動裝置（iPhone/Android）的 SSH client 在切換 app 或鎖定螢幕時會斷線。以下方案可確保工作中斷後能接回：

### 方案 A：tmux（推薦，最簡單）
```bash
sudo apt-get install -y tmux    # 安裝
tmux new -s work                # 建立持久 session
# 斷線後重新 SSH 連上，執行：
tmux attach -t work             # 接回原本 session，所有工作完整保留
# 其他操作
tmux ls                         # 列出所有 session
tmux detach                     # 脫離 session (Ctrl+B, D)
tmux kill-session -t work       # 刪除 session
```

### 方案 B：mosh（專為行動裝置設計）
```bash
sudo apt-get install -y mosh
# iPhone 需支援 mosh 的 client（如 Blink Shell）
mosh user@host
```

### 方案 C：SSH KeepAlive（客戶端設定）
在 `~/.ssh/config` 加入：
```
Host *
    ServerAliveInterval 30
    ServerAliveCountMax 3
```

### 注意事項
- tmux 不需額外 client 支援（標準 SSH 即可用）
- mosh 需要 UDP（部分防火牆會封鎖）
- 同時開多個 session 用 `tmux ls` + `tmux attach -t <name>` 管理

## 成本與參數
- 溫度：0.1（確定性最高）
- 最大輸出 Token：512（診斷管線較長）
- 信心閾值：85%
- 成本上限：$0.15/次
- 延遲目標：<10s