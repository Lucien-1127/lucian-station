# GCP Nested Virtualization + docker-android (TYPE-Q)

## 用途
在 GCP VM 上啟用巢狀虛擬化，部署 `budtmo/docker-android` 運行 Android 模擬器，並透過 NoVNC 或原始 VNC 從外部存取。

---

## 一、開 VM（TYPE-Q 規格）

### 最低規格（勉強能跑）
- vCPU: 4 核
- RAM: 8 GB
- 磁碟: 30 GB SSD

### 建議規格（順跑）
- vCPU: 8 核
- RAM: 16 GB
- 磁碟: 50 GB SSD

### GCP 開 VM 關鍵指令（標準 UI 不給勾選巢狀虛擬化）

```bash
gcloud compute instances create type-q \
  --zone=asia-east1-b \
  --machine-type=n2-standard-8 \
  --min-cpu-platform="Intel Cascade Lake" \
  --enable-nested-virtualization \
  --boot-disk-size=50GB \
  --boot-disk-type=pd-ssd \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud
```

**關鍵參數：**
- `--enable-nested-virtualization` — **必填**，沒這個 KVM 打不開
- `--min-cpu-platform="Intel Cascade Lake"` — 指定 Intel CPU（AMD EPYC 有時 n2 也會配到，但 nested virt 可能不通）
- machine type 必須選 N2 系列（N1 不支援）

### 陷阱：GCP 配到 AMD EPYC 怎麼辦

即使指定了 Intel Cascade Lake，有時 GCP 仍會配到 AMD EPYC 主機（vmx=0, svm=0 都抓不到）。

**解法：停機重開**
```bash
gcloud compute instances stop type-q --zone=asia-east1-b
# 等到狀態變成 TERMINATED
gcloud compute instances start type-q --zone=asia-east1-b
```
重開後有機會排到 Intel 主機。驗證：
```bash
grep -cw vmx /proc/cpuinfo    # 回傳 >0 才對
grep "model name" /proc/cpuinfo | head -1
```

### 各雲端 Nested Virt 支援

| 平台 | 支援 | 備註 |
|------|------|------|
| GCP | ✅ | `--enable-nested-virtualization` |
| AWS | ⚠️ | 要選 .metal 或 bare metal，一般 EC2 不行 |
| Azure | ✅ | Dv3/Ev3 系列以上 |
| Hetzner | ✅ | KVM 預設開 |
| Vultr | ✅ | Cloud Compute 高效能方案 |

---

## 二、安裝基礎套件（SSH 進 VM 後執行）

```bash
# 更新系統
sudo apt update && sudo apt upgrade -y

# 確認 KVM
grep -cw vmx /proc/cpuinfo    # 應 > 0

# 載入 KVM 模組（如果 /dev/kvm 不存在）
sudo modprobe kvm
sudo modprobe kvm_intel
ls -la /dev/kvm               # 應看到 crw-rw----

# 安裝 Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# 安裝 KVM 套件
sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils
sudo adduser $USER kvm
sudo chown $USER /dev/kvm
```

---

## 三、啟動 docker-android 容器

### 正確的容器啟動指令

```bash
docker run -d --restart=always \
  --name android-emu \
  --privileged \
  --device /dev/kvm \
  -p 6080:6080 \
  -e EMULATOR_DEVICE="Samsung Galaxy S10" \
  -e WEB_VNC=true \
  -e APPIUM=false \
  budtmo/docker-android:emulator_13.0
```

**關鍵正確用法：**
- ✅ `--device /dev/kvm` — 正確傳遞 KVM 裝置權限
- ❌ **不要用** `-v /dev/kvm:/dev/kvm`（volume mount，權限可能不對）
- `--restart=always` — VM 重開容器自動復活

### 可用環境變數

| 變數 | 說明 | 範例 |
|------|------|------|
| `EMULATOR_DEVICE` | 裝置型號 | `Samsung Galaxy S10`, `Pixel 8` |
| `EMULATOR_ANDROID_VERSION` | Android 版本 | `13.0`, `14.0` |
| `EMULATOR_ADDITIONAL_ARGS` | 額外模擬器引數 | `-no-snapshot` |
| `EMULATOR_NO_SKIN` | 不顯示機殼 | `true` |
| `WEB_VNC` | 開啟 noVNC | `true` |
| `APPIUM` | 是否開啟 Appium | `false` |
| `VNC_PASSWORD` | VNC 密碼（選填） | — |

### 監控啟動狀態

```bash
# 檢查 device 就緒
docker exec android-emu cat device_status    # 出現 READY 才是好了

# 檢查 boot 完成
docker exec android-emu adb shell getprop sys.boot_completed   # 回傳 1

# 檢查顯示狀態
docker exec android-emu adb shell dumpsys window | grep mCurrentFocus

# tail logs
docker logs -f android-emu
```

冷啟動約 3–5 分鐘。

---

## 四、NoVNC 空白畫面除錯

### 症狀
瀏覽器連 `http://VM-IP:6080` 看到 noVNC 頁面但畫面空白（灰色/黑色）。

### 常見原因與解法

| 症狀 | 原因 | 解法 |
|------|------|------|
| 空白 gray X11 桌面 | Xvfb + openbox 正常但 Android 畫面沒映射 | 用 ADB screenrecord + ffplay 鏡像 |
| 黑畫面 | SwiftShader 渲染離屏 | 同上 |
| noVNC 頁面載入失敗 | 電信商擋 6080 port | 改用 VNC app 走 5900 |
| 502 Bad Gateway | 瀏覽器工具代理無法處理 raw IP:port | 用實體瀏覽器直接連 |

### 鏡像解法：ADB screenrecord + ffplay

容器內已有 ffmpeg/ffplay，可用此方式將 Android 畫面映射到 Xvfb：

```bash
# 在容器內執行
docker exec android-emu bash -c 'nohup bash -c "adb exec-out screenrecord --output-format=h264 --bit-rate 4M --size 720x1280 /dev/stdout 2>/dev/null | DISPLAY=:0 ffplay -v 0 -noborder -x 720 -y 1280 - 2>/dev/null" > /dev/null 2>&1 &'
```

但注意此方式非持久化（容器重啟需重新執行），建議包成持續服務。

### 驗證顯示是否正常

用 ffmpeg 截取 Xvfb 畫面（容器內已有 ffmpeg）：
```bash
docker exec android-emu sh -c 'DISPLAY=:0 ffmpeg -y -video_size 1600x900 -framerate 1 -f x11grab -i :0 -frames:v 1 -update 1 /tmp/screenshot.png 2>&1'
# 複製出來看
docker cp android-emu:/tmp/screenshot.png /tmp/
```

### 替代存取方式：Raw VNC（手機友善）

noVNC 走 WebSocket，手機瀏覽器相容性差。容器同時有 Raw VNC 在 port 5900：

1. 手機裝 VNC App（bVNC Free / VNC Viewer）
2. 連線到 `104.199.163.227:5900`（不用密碼）

### 防火牆設定（安全注意）

```bash
# 開白名單（限自己的 IP）
gcloud compute firewall-rules create allow-novnc-typeq \
  --allow tcp:6080 \
  --source-ranges=你的IP/32

# 🔴 絕對不要開 0.0.0.0/0 — NoVNC 沒有內建認證
```

---

## 五、已知問題

1. **NoVNC 空白是已知通病** — GitHub Issues #120, #198, #305 都有討論。核心原因是 Android 模擬器用 `-gpu swiftshader_indirect` 離屏渲染，Xvfb 只抓到空白桌面。
2. **容器內不能裝套件** — 容器以非 root 執行（androidusr, uid 1300），無 sudo 權限安裝 scrcpy 等工具。
3. **VM 重開後 KVM 模組需重載** — 建議寫入 `/etc/modules` 或 systemd unit 確保開機自動載入 kvm / kvm_intel。
4. **Firecracker/microVM 不支援** — 此類輕量 VM 沒有硬體虛擬化延伸。
5. **N1 machine type 不支援** nested virtualization，必須用 N2、N2D、C2、M3 等系列。
