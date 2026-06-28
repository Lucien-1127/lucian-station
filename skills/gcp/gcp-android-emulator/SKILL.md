---
title: GCP Android 模擬器 VM
name: gcp-android-emulator
description: 在 GCP 上建立附巢式虛擬化（Nested Virtualization）的 Android 模擬器 VM，含 KVM + Docker + docker-android 完整流程
category: gcp
---

# GCP Android 模擬器（TYPE-Q/TYPE-S）

## 適用情境

需要在雲端 VM 上跑 Android 模擬器（無頭伺服器），以瀏覽器 VNC 連線操作。常見用途：
- Android App 自動化測試（Appium）
- 手機介面截圖/錄影
- 遠端 Android 開發環境
- TYPE-Q / TYPE-S 專案測試

## VM 最低規格

| 規格 | 勉強能跑 | 順跑 |
|:-----|:---------|:------|
| vCPU | 4 核 | 8 核 |
| RAM | 8 GB | 16 GB |
| 磁碟 | 30 GB SSD | 50 GB SSD |
| Nested Virt | ✅ 必要 | ✅ 必要 |

**Nested Virtualization 是關鍵，沒開直接死。**

## Nested Virt 支援對照

| 平台 | 支援 | 備註 |
|:-----|:------|:------|
| GCP | ✅ | `--enable-nested-virtualization` 建 VM |
| AWS | ✅ 限 metal | 一般 EC2（t3/c5 等）不支援 KVM |
| Azure | ✅ | Dv3/Ev3 系列以上 |
| Hetzner | ✅ | KVM 預設開 |
| Vultr | ✅ | Cloud Compute 高效能方案 |

## GCP 建立 VM 指令

```bash
gcloud compute instances create type-q \
  --zone=asia-east1-b \
  --machine-type=n2-standard-4 \
  --min-cpu-platform="Intel Cascade Lake" \
  --enable-nested-virtualization \
  --boot-disk-size=30GB \
  --boot-disk-type=pd-ssd \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud
```

**關鍵參數：**
- `--enable-nested-virtualization` — 必填
- machine type 必須選 **N2 系列**（N1 不支援）
- CPU platform 指定 **Cascade Lake** 或 **Skylake** 以上

### 磁碟擴容

```bash
gcloud compute disks resize type-q --zone=asia-east1-b --size=50GB
sudo growpart /dev/sda 1
sudo resize2fs /dev/sda1
```

## 防火牆

```bash
# ❌ 不要開 0.0.0.0/0 — NoVNC 沒有內建認證
gcloud compute firewall-rules create allow-android-vnc \
  --allow tcp:6080 \
  --source-ranges=<你的IP>/32
```

替代方案：SSH tunnel
```bash
gcloud compute ssh type-q --zone=asia-east1-b -- -L 6080:localhost:6080
```

## VM 內設定（依序執行）

### 1. 更新系統
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. 確認 KVM
```bash
grep -cw vmx /proc/cpuinfo
# >0 = OK，0 = nested virt 沒開

# 也可以用 gcloud 確認 VM 設定
gcloud compute instances describe type-q --zone=asia-east1-b --format="get(advancedMachineFeatures)"
# 應回傳 enableNestedVirtualization=True
```

**🟡 關鍵陷阱 — AMD EPYC：** 即使有設 `--enable-nested-virtualization` 和 `--min-cpu-platform="Intel Cascade Lake"`，GCP 可能把 VM 排到 **AMD EPYC** 主機（`cat /proc/cpuinfo | grep "model name"` 會看到 AMD EPYC），此時 vmx=0 且 `/dev/kvm` 不存在。**解法：** 把 VM stop 再 start，強迫重新排到 Intel 主機：
```bash
gcloud compute instances stop type-q --zone=asia-east1-b
gcloud compute instances start type-q --zone=asia-east1-b
```
重開後再次確認 `grep -cw vmx /proc/cpuinfo` > 0。

### 3. 安裝 Docker
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# ⚠️ usermod 後需要新 shell session 才生效。舊 session 用 sudo docker
```

### 4. 安裝 KVM 套件
```bash
sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils
sudo adduser $USER kvm
sudo chown $USER /dev/kvm

# 🔴 必須確保 KVM 模組開機自動載入（否則 VM 重開後模擬器無法啟動）
sudo modprobe kvm
sudo modprobe kvm_intel
echo "kvm" | sudo tee /etc/modules-load.d/kvm.conf
echo "kvm_intel" | sudo tee -a /etc/modules-load.d/kvm.conf
```

### 5. 啟動 docker-android
```bash
# ⚠️ 如果之前跑過舊容器，先移除再重建
docker rm android-emu 2>/dev/null

docker run -d \
  --restart=always \
  --name android-emu \
  --privileged \
  -v /dev/kvm:/dev/kvm \
  -p 6080:6080 \
  -e EMULATOR_DEVICE="Samsung Galaxy S10" \
  -e WEB_VNC=true \
  -e APPIUM=false \
  budtmo/docker-android:emulator_13.0
```

**`--restart=always` 非常重要：** 沒有這個參數，VM 重啟後容器不會自動啟動，必須手動 `docker start android-emu`。

**`docker rm` 也很重要：** VM 重啟後舊的 stopped container 會佔住名稱，新的 `docker run` 會報 `Conflict. The container name "/android-emu" is already in use`。因此重建容器前先 `docker rm`。

### 6. 等就緒
```bash
docker logs -f android-emu
# 冷啟動約 3-5 分鐘，等待 Emulator is ready

# 或用 ps 確認 qemu 進程已跑（不需要等 log ready）
docker exec android-emu ps aux | grep emulator
# 有 qemu-system-x86_64 且含 -accel on 就對了
```

### 7. 瀏覽器連線
```
http://<GCP外部IP>:6080
```

## 驗證清單

```bash
# KVM
grep -cw vmx /proc/cpuinfo                              # >0
sudo docker exec android-emu ls -la /dev/kvm             # 存在

# 容器狀態
docker ps --filter name=android-emu                      # Up
docker top android-emu 2>&1 | grep qemu-system           # 進程存在
ss -tlnp | grep 6080                                    # 在聽

# ADB 連線
docker exec android-emu adb devices                      # emulator-5554  device

# 資源
df -h /                                                  # 有空間
free -h                                                  # 記憶體足夠
```

## 常見卡關點

| 症狀 | 原因 | 解法 |
|:-----|:------|:------|
| 容器一直 restart | KVM 沒掛進去 | 確認 `--privileged` + `-v /dev/kvm:/dev/kvm` |
| vmx=0, /dev/kvm 不存在 | VM 排到 AMD 主機 | 執行 stop/start VM 強迫換 Intel 主機 |
| 畫面黑屏很久 | 正常冷啟動 | 等 3-5 分鐘，確認 `-accel on` 有開 |
| 網頁打不開 | 防火牆沒開 | 補開 firewall 或用 SSH tunnel |
| /dev/kvm 權限錯誤 | 群組問題 | `sudo chown $USER /dev/kvm` |
| ADB offline | 模擬器還在開機 | 等開機完成後重試 |
| 磁碟空間不足 | 30GB 太小 | 擴容到 50GB |
| `Container name already in use` | VM 重開後舊容器殘留 | `docker rm android-emu` 再重新 run |
| 第一次 VM 重開後容器沒自動起來 | `--restart=always` 缺失 | 重新建立容器時加上該參數 |
| VM 重開後 KVM 模組消失 | modules-load 未設定 | 重新執行 Step 4 的 `modprobe` + `/etc/modules-load.d/kvm.conf` |

## 記憶體參考

Android 13 (Samsung Galaxy S10) 運行時 qemu 約佔 5.5-7 GB RAM：
```bash
sudo docker top android-emu 2>&1 | grep qemu | awk '{print $1,$2,$4"% MEM",$11}'
```
