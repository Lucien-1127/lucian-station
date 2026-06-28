# GCP VM 診斷參考

## 常見的 GCP VM 問題模式

### 1. NVIDIA 驅動誤裝（最常見當機原因）
GCP 多數 VM 類型**沒有 GPU**（N1/N2/N4/C4 等標準系列），但若手動安裝了 NVIDIA 580-server 等驅動，會導致 kernel taint、fabricmanager 反覆失敗、最終系統當機。

**診斷**
```bash
dpkg -l | grep -i nvidia | wc -l        # 計數（0=已清，>0=殘留）
sudo systemctl --failed                  # 看 nvidia-fabricmanager / nvidia-persistenced
dmesg | grep "NVRM\|nvidia:"            # NVRM: No NVIDIA GPU found
cat /var/lib/gce-accelerator/shipped-nvidia-version  # 非空=GCE 會自動載入
lsinitramfs /boot/initrd.img-$(uname -r) | grep nvidia  # initramfs 殘留檢查
```

**完整修復序列**（purge 後仍需要手動清理多處殘留）

```bash
# 步驟 1: purge 所有 nvidia 套件
sudo apt-get purge -y nvidia-* linux-modules-nvidia-* libnvidia-*

# 步驟 2: 清除 GCE accelerator 旗標（最重要！否則下次開機仍會載入）
echo "" | sudo tee /var/lib/gce-accelerator/shipped-nvidia-version

# 步驟 3: 加入 modprobe 黑名單
sudo tee /etc/modprobe.d/blacklist-nvidia.conf <<'EOF'
blacklist nvidia
blacklist nvidia_drm
blacklist nvidia_modeset
blacklist nvidia_uvm
EOF

# 步驟 4: 刪除殘留 systemd unit
sudo rm -f /etc/systemd/system/nvidia-fabricmanager.service \
          /etc/systemd/system/nvidia-persistenced.service

# 步驟 5: 重建所有 initramfs（purge 不一定會自動做！）
sudo update-initramfs -u -k all

# 步驟 6: 刪除舊 kernel 的 initramfs（可能含 nvidia 殘留設定）
ls /boot/initrd.img-*generic* 2>/dev/null | while read f; do
  [ -f "$f" ] && lsinitramfs "$f" | grep -q nvidia && sudo rm -v "$f"
done

# 步驟 7: 清理 systemd 失敗狀態
sudo systemctl reset-failed nvidia-fabricmanager.service 2>/dev/null
sudo systemctl reset-failed nvidia-persistenced.service 2>/dev/null
sudo systemctl daemon-reload
```

**驗證**
```bash
modprobe --dry-run nvidia    # 應回傳 FATAL: Module nvidia not found
sudo systemctl --failed      # 應為 0 loaded units
cat /etc/modprobe.d/blacklist-nvidia.conf  # 應含 blacklist 行
ls /etc/systemd/system/nvidia* 2>/dev/null || echo "無殘留"
lsinitramfs /boot/initrd.img-$(uname -r) | grep nvidia || echo "initramfs 乾淨"
cat /var/lib/gce-accelerator/shipped-nvidia-version  # 應為空
```

**陷阱**
- ❌ purge 後 initramfs「不一定」會自動重建 — 務必手動 `update-initramfs -u -k all`
- ❌ GCE accelerator 旗標不清除 → 下次開機仍會自動載入 nvidia 模組
- ❌ 舊 kernel 的 initramfs 可能殘留 nvidia 設定 — 需逐一檢查並刪除
- ❌ systemd 即使 unit 已刪除仍記憶失敗狀態 — 需 `reset-failed`

### 2. GPT 分割表備份標頭損毀
GCP boot disk（NVMe）的 GPT 備份 header 有時被 cloud-init image 工具產生在錯誤位置。

**診斷**
```
dmesg --level=emerg,alert,crit,err | grep -i GPT
# 預期看到: Alternate GPT header not at the end of the disk
# 或: GPT:Primary header thinks Alt. header is not at the end
```

**修復**
```bash
sudo sgdisk -e /dev/nvme0n1
# -e = 將備份 GPT header 移動到磁碟末端
# 不需重啟即可生效（下次開機自動使用新表）
```

### 3. 無 Swap / 記憶體不足
GCP 預設 image 不建立 swap，7.3GB RAM 以下機型若跑 Docker 或多 Python 程序可能 OOM。

**建立 swap**
```bash
sudo fallocate -l 2G /swapfile          # 2GB 或 RAM 的 25-50%
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

**驗證**
```bash
swapon --show
free -h
```

### 4. 啟動後立即 SSH 錯誤: `pam_systemd(sshd:session): Failed to create session`
通常是 systemd-logind 啟動比 sshd 慢，GCP 上常見於剛 boot 的瞬間。
後續連線會正常，不需處理。若持續發生則檢查 `sudo systemctl status systemd-logind`。

### 5. GPT 「分割表順序」警告
`Partition table entries are not in disk order` 是 cloud-init 產生的正常現象。
GCP boot image 刻意把 Linux filesystem partition (sector 2099200) 放在 BIOS boot (sector 2048) 之後、EFI (sector 10240) / extended boot (sector 227328) 之前，這「不照 sector 順序」是 GCP image 的標準 layout，**不需修復**。

## 快速指令集

```bash
# 系統基本概況
echo "=== UPTIME ===" && uptime
echo "=== BOOTS ===" && who -b && last -x -F reboot shutdown 2>/dev/null | head -5
echo "=== CPU ===" && nproc && lscpu | grep -E "Model name|CPU MHz"
echo "=== MEMORY ===" && free -h
echo "=== DISK ===" && df -h && df -i | head -5
echo "=== SWAP ===" && swapon --show 2>/dev/null
echo "=== FAILED ===" && sudo systemctl --failed 2>/dev/null

# 深入診斷
echo "=== CRASH LOGS ===" && ls -la /var/crash/ 2>/dev/null
echo "=== OOM ===" && sudo journalctl -g "oom_kill|OOM|killed process" -n 20
echo "=== KERNEL ERR ===" && sudo dmesg --level=emerg,alert,crit,err,warn 2>/dev/null | tail -30
echo "=== GPT ===" && sudo sgdisk -v /dev/nvme0n1 2>&1 | grep -i "problem\|error\|caution"
echo "=== CACHE SIZE ===" && du -sh ~/.cache/ 2>/dev/null
echo "=== LOG SIZE ===" && sudo du -sh /var/log/ 2>/dev/null
```
