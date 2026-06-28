# TYPE-S 執行紀錄與除錯筆記

## 容器內進程對照

| 進程 | 說明 | 正常狀態 |
|:-----|:------|:---------|
| `qemu-system-x86_64` | Android 模擬器本體 | CPU 30-40%，記憶體 5-7GB |
| `crashpad_handler` | Google crash reporting | 低資源背景 |
| `netsimd` | 網路模擬器 | 少量記憶體 |
| `Xvfb` | 虛擬顯示器 (:0, 1600x900x24) | 持續運行 |
| `x11vnc` | VNC 伺服器 (:0) | 持續運行 |
| `novnc_proxy` | 瀏覽器 VNC (port 6080) | 持續運行 |
| `socat` | ADB port forwarding (5554/5555) | 持續運行 |
| `openbox` | 視窗管理員 | 持續運行 |

## 正常 vs 異常 logs 判讀

### 正常啟動 log 順序
```
supervisord started
spawned: d_screen, d_wm, vnc_server, vnc_web, android_port_forward, appium, device, log_web_shared
success: android_port_forward → RUNNING
success: d_screen → RUNNING
success: d_wm → RUNNING
success: vnc_server → RUNNING
success: vnc_web → RUNNING
success: device → RUNNING
success: log_web_shared → RUNNING
exited: log_web_shared (exit status 0; expected)   ← 這是正常的，log 收集器完成任務
exited: appium (exit status 0; not expected)        ← 如果 APPIUM=false 這是正常的
```

### 可忽略的警告
```
WARN exited: log_web_shared (exit status 0; not expected)
INFO gave up: log_web_shared entered FATAL state, too many start retries too quickly
```
→ `log_web_shared` 是共享日誌收集器，重啟失敗不影響模擬器運行。

### 真正問題信號
```
WARN exited: device (exit status 1; not expected)
```
→ 模擬器啟動失敗。檢查 KVM、磁碟空間、重新啟動容器。

### 容器一直 restart（exit status 1 循環）
```
WARN exited: device (exit status 1; not expected)
...（過幾秒重新 spawned）
```
→ 最常見原因：**KVM 沒掛入**。檢查 `ls -la /dev/kvm` 是否存在、容器啟動指令有沒有 `--privileged` 和 `-v /dev/kvm:/dev/kvm`。
→ 若 `/dev/kvm` 不存在 → 檢查 VM 的 nested virtualization（`grep -cw vmx /proc/cpuinfo`）

## VNC 可用但畫面黑屏

即使 qemu 正在跑，VNC 可能因為以下原因顯示黑屏：
- 模擬器仍在冷啟動過程中（3-5 分鐘）
- Android 系統正在首次設定
- 顯示解析度不相容

解法：等待、檢查 ADB 是否連線（`adb devices` 顯示 `device` 而非 `offline`）、檢查容器 CPU 使用率。

## VM 重開後容器消失或命名衝突

### 情境
VM 重啟後，原先的 android-emu 容器變成 stopped 狀態（沒有 `--restart=always`），新的 `docker run` 報錯：
```
docker: Error response from daemon: Conflict. The container name "/android-emu"
is already in use by container "6d9e1a26..."
```

### 預防
建容器時務必加 `--restart=always`。

### 修復
```bash
docker rm android-emu            # 移除舊容器（release 名稱）
# 重新執行 Step 5 的 docker run（含 --restart=always）
```

## VM 排到 AMD EPYC 主機 — nested virt 失效

### 情境
建立 VM 時設了 `--enable-nested-virtualization` 和 `--min-cpu-platform="Intel Cascade Lake"`，但 `grep -cw vmx /proc/cpuinfo` 回傳 0，且 `cat /proc/cpuinfo | grep "model name"` 顯示 **AMD EPYC**。

### 原因
GCP 在 asia-east1-b 可能暫時沒有 Intel Cascade Lake 容量，改配 AMD 主機。AMD 不支援 nested virtualization。

### 解法
```bash
gcloud compute instances stop type-q --zone=asia-east1-b    # 關機
gcloud compute instances start type-q --zone=asia-east1-b   # 重開，強迫換主機
# 等待開機後 SSH 連入，再確認 vmx > 0
```

## KVM 模組重開機後消失

VM 重啟後 `/dev/kvm` 不存在，即使 vmx>0。

### 原因
KVM kernel modules 不會自動載入。需要設定 `/etc/modules-load.d/`。

### 預防
```bash
sudo modprobe kvm
sudo modprobe kvm_intel
echo "kvm" | sudo tee /etc/modules-load.d/kvm.conf
echo "kvm_intel" | sudo tee -a /etc/modules-load.d/kvm.conf
```

### 修復
```bash
sudo modprobe kvm && sudo modprobe kvm_intel
sudo chown $USER /dev/kvm
docker start android-emu   # 容器如果還在的話直接 start 即可
```

## 環境變數對照

| 變數 | 預設值 | 說明 |
|:-----|:--------|:------|
| `EMULATOR_DEVICE` | `Samsung Galaxy S10` | 模擬裝置型號，影響解析度 |
| `WEB_VNC` | `true` | 啟用瀏覽器 VNC |
| `APPIUM` | `false` | Appium 測試框架 |
| `DEBUG` | 無 | 除錯模式 |
