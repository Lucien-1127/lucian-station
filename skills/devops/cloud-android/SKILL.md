---
name: cloud-android
description: 在 GCP VM 上建立雲端 Android 模擬器（雲手機），含無頭模式、螢幕鏡像、觸控橋接、iOS 優化
---

# Cloud Android Emulator（雲手機）

在 GCP 或其他雲端 VM 上建立可從手機連線操控的 Android 模擬器。

## 系統架構

```
iPhone Safari/VNC App
    ↓ port 80 (nginx) or port 5900 (VNC)
    ↓
nginx 反向代理 (port 80 → container:6080)
    ↓ WebSocket (noVNC)
budtmo/docker-android 容器
    ├── x11vnc (port 5900) + -pipeinput → ADB touch bridge
    ├── websockify → noVNC (port 6080)
    ├── Xvfb :0 (720×1280) ← ffplay ← ADB screenrecord (H.264)
    └── qemu-system-x86_64-headless (Android 13, Pixel 8)
```

## 工作流程

### Step 1 — 建立 VM（GCP）

```bash
gcloud compute instances create android-emu \
  --zone=asia-east1-b \
  --machine-type=n2-standard-4 \
  --min-cpu-platform="Intel Cascade Lake" \
  --enable-nested-virtualization \
  --boot-disk-size=50GB \
  --boot-disk-type=pd-ssd \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud
```

**關鍵點：**
- `--enable-nested-virtualization` 必填
- `--min-cpu-platform="Intel Cascade Lake"` — N2 系列限定 Intel
- 只用 `n2-*` 系列（N1 不支援 nested virt）

### Pitfall: CPU 顯示 AMD EPYC → VM 需重啟

```bash
gcloud compute instances stop <name> --zone=<zone>
gcloud compute instances start <name> --zone=<zone>
```
驗證：`grep -cw vmx /proc/cpuinfo` 回傳 > 0。

### 關鍵：Xvfb 解析度必須匹配螢幕鏡像

螢幕鏡像管線（ADB screenrecord → ffplay）輸出 `720×1280`（手機直向）。
**Xvfb 必須完全匹配**，否則畫面裁切或觸控偏移。

**解法：docker run 傳入正確的 SCREEN_WIDTH/HEIGHT**
```bash
-e SCREEN_WIDTH=720 -e SCREEN_HEIGHT=1280 -e SCREEN_DEPTH=24
```

預設 1600×900 會裁切手機畫面下方。設為 720×1280 後 ffplay 填滿整個 Xvfb，觸控直接對應。

### Step 2 — 基本環境

```bash
sudo apt update && sudo apt upgrade -y
grep -cw vmx /proc/cpuinfo   # 確認 nested virt 有開

# Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# KVM
sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils
sudo adduser $USER kvm
```

### Step 3 — 啟動容器（雲手機模式）

```bash
docker run -d --restart=always --name android-emu --privileged --device /dev/kvm \
  -p 5900:5900 \
  -p 6080:6080 \
  -e WEB_VNC=true \
  -e EMULATOR_DEVICE='Pixel 8' \
  -e EMULATOR_NO_SKIN=true \
  -e EMULATOR_ADDITIONAL_ARGS='-no-window' \
  -e SCREEN_WIDTH=720 \
  -e SCREEN_HEIGHT=1280 \
  -e SCREEN_DEPTH=24 \
  -e APPIUM=false \
  budtmo/docker-android:emulator_13.0
```

**重點：**
- `--device /dev/kvm` 不是 `-v /dev/kvm:/dev/kvm`
- `-no-window` → 無頭模式，畫面全靠鏡像管線
- 雙 port：6080（noVNC）+ 5900（VNC Direct）

### Step 4 — 螢幕鏡像管線

容器啟動後，需手動啟動鏡像管線（或靠後續的 watchdog 自動恢復）：

```bash
# 等 Android 開機
docker exec android-emu bash -c '
  for i in $(seq 1 60); do
    b=$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d "\r")
    [ "$b" = "1" ] && break
    sleep 5
  done
'

# 啟動鏡像（背景執行）
docker exec -d android-emu bash -c '
  adb exec-out screenrecord --output-format=h264 --bit-rate 6M --size 720x1280 /dev/stdout 2>/dev/null | \
  DISPLAY=:0 ffplay -v 0 -noborder -left 0 -top 0 -x 720 -y 1280 - 2>/dev/null
'
```

**bit-rate 說明：** 6M 是畫質與延遲的平衡點。4M 省頻寬但畫質較差，8M 畫質好但手機網路可能卡。

### Step 5 — 觸控橋接（x11vnc pipeinput）

VNC 點擊 → ADB shell input tap → Android 原生觸控。

#### 5a. 建立 adb_touch.sh（含座標縮放）

```bash
docker exec android-emu python3 -c "
content = '''#!/bin/bash
while read L; do
  echo \"\$L\" | grep -q \"button_down\" || continue
  x=\$(echo \"\$L\" | cut -d\" \" -f2)
  y=\$(echo \"\$L\" | cut -d\" \" -f3)
  # Scale from VNC space (720x1280) to phone native (1080x2400)
  px=\$(( x * 1080 / 720 ))
  py=\$(( y * 2400 / 1280 ))
  adb shell input tap \$px \$py 2>/dev/null
done
'''
with open('/tmp/adb_touch.sh', 'w') as f: f.write(content)
import os; os.chmod('/tmp/adb_touch.sh', 0o755)
"
```

**縮放公式（必須）：** VNC 的 720×1280 不等於手機原生 1080×2400。
- X: `x * 1080 / 720`
- Y: `y * 2400 / 1280`
沒有這個縮放，觸控點會偏離實際位置（特別是 Y 軸誤差達 88%）。

#### 5b. 修改 app.py

```bash
docker exec android-emu sed -i \
  's|-display {display} -forever -shared {last_arg}|-display {display} -forever -shared -cursor none -pipeinput /tmp/adb_touch.sh {last_arg}|' \
  /home/androidusr/docker-android/cli/src/app.py

# 清除 Python 位元組碼快取（不刪不會生效！）
docker exec android-emu bash -c 'find /home/androidusr/docker-android/cli -name "*.pyc" -delete'
```

#### 5c. 重啟 x11vnc

```bash
docker exec android-emu bash -c 'pkill -f "x11vnc.*-display" 2>/dev/null'
sleep 3
# 確認已用正確參數重啟
docker exec android-emu ps aux | grep x11vnc | grep pipeinput
```

### Step 6 — nginx 反向代理（port 80）

iPhone 電信商常擋非標準 port（6080）。nginx 走標準 port 80。

```bash
sudo apt install -y nginx
```

#### ⚠️ 陷阱：nginx 變數會被 bash heredoc 吃掉

nginx 設定中的 `$host`、`$http_upgrade`、`$uri` 等變數**會被 bash heredoc 吃掉**：

```bash
# ❌ 錯誤 — 變數全變空字串
sudo tee /etc/nginx/sites-available/novnc << 'EOF'
proxy_set_header Upgrade $http_upgrade;   # 變成：proxy_set_header Upgrade ;
try_files $uri $uri/ =404;                # 變成：try_files  / =404;
EOF
```

**解法：用 Python stdin 寫入，不要用 bash heredoc**

```bash
# VM 上執行
python3 << 'PYIN'
config = '''server {
    listen 80; server_name _;
    root /var/www/cloudphone; index index.html;

    location /websockify {
        proxy_pass http://127.0.0.1:6080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400s; proxy_buffering off;
    }

    location ~ ^/(vnc\\.html|app/|core/|.*\\.json|favicon) {
        proxy_pass http://127.0.0.1:6080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / { try_files $uri $uri/ /index.html; }
}'''
with open('/etc/nginx/sites-available/novnc', 'w') as f: f.write(config)
print('nginx config written')
PYIN
```

**原理：** Python raw string 保留 `$`，而 `<< 'PYIN'` 阻止外層 bash 展開。

```bash
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/novnc /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

```python
# VM 上執行
config = '''
server {
    listen 80;
    server_name _;

    root /var/www/cloudphone;
    index index.html;

    location /websockify {
        proxy_pass http://127.0.0.1:6080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400s;
        proxy_buffering off;
    }

    location /vnc.html {
        proxy_pass http://127.0.0.1:6080/vnc.html;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_read_timeout 86400s;
    }

    location /app/ { proxy_pass http://127.0.0.1:6080/app/; proxy_http_version 1.1; proxy_set_header Host $host; }
    location /core/ { proxy_pass http://127.0.0.1:6080/core/; proxy_http_version 1.1; proxy_set_header Host $host; }
    location ~ \\.json$ { proxy_pass http://127.0.0.1:6080; proxy_http_version 1.1; proxy_set_header Host $host; }

    location / {
        try_files $uri $uri/ =404;
    }
}
'''
open('/etc/nginx/sites-available/novnc', 'w').write(config)
```

```bash
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/novnc /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

#### Cloud Phone 登入頁面

提供 `/var/www/cloudphone/index.html` 作為簡潔登入頁：
- 全黑背景，一鍵「連線」按鈕
- 點擊後跳 `vnc.html?autoconnect=true&resize=scale&view_clip=true`
- 防止 iOS 捏合縮放（JS 攔截 gesturestart）

### Step 7 — 優化 noVNC for iOS

#### 7a. 設定預設值（defaults.json）

```bash
docker exec -u 0 android-emu python3 -c "
import json
d = {'resize': 'scale', 'view_clip': True, 'quality': 6,
     'compression': 9, 'reconnect': True, 'reconnect_delay': 5000,
     'show_dot': True, 'shared': False, 'view_only': False}
json.dump(d, open('/opt/noVNC/defaults.json', 'w'), indent=2)
"
```

| 設定 | 值 | 效果 |
|------|----|------|
| resize | scale | 自動縮放填滿手機螢幕 |
| view_clip | true | 無捲軸 |
| compression | 9 | 最大壓縮，適合行動網路 |
| reconnect | true | 斷線自動重連 |
| show_dot | true | 無滑鼠游標時顯示觸控點 |

#### 7b. 加入 iOS 防干擾 CSS

在容器內 `base.css` 追加：

```css
/* 防止 iOS 捏合縮放干擾 VNC 觸控 */
#noVNC_container { touch-action: none !important; }
/* 防止 iOS rubber-band 彈性捲動 */
body { overscroll-behavior: none; overflow: hidden; position: fixed; }
```

### Step 8 — 自動復原（systemd watchdog）

容器重啟後鏡像管線不會自動執行，需 VM 層級 watchdog。

#### 8a. 建立恢復腳本

`/opt/cloudphone/restore.sh`（每 3 分鐘執行）：
1. 確認容器 running
2. 檢查 /tmp/adb_touch.sh 是否存在，不存在則建立
3. 檢查 app.py 是否有 pipeinput 設定，無則 patch
4. 檢查 x11vnc 是否有 pipeinput 參數，無則重啟
5. 檢查 ffplay 是否在跑，無則啟動鏡像管線

#### 8b. systemd 服務 + 計時器

```bash
# 服務
sudo tee /etc/systemd/system/cloudphone-watchdog.service << 'SVC'
[Unit]
Description=Cloud Phone watchdog
After=docker.service
[Service]
Type=oneshot
ExecStart=/opt/cloudphone/restore.sh
SVC

# 計時器（每 3 分鐘檢查）
sudo tee /etc/systemd/system/cloudphone-watchdog.timer << 'TMR'
[Unit]
Description=Check cloud phone every 3 min
[Timer]
OnBootSec=90
OnUnitActiveSec=180
Persistent=true
[Install]
WantedBy=timers.target
TMR

sudo systemctl daemon-reload
sudo systemctl enable cloudphone-watchdog.timer
sudo systemctl start cloudphone-watchdog.timer
```

### Step 9 — 防火牆

```bash
gcloud compute firewall-rules create allow-cloudphone \
  --allow tcp:80,6080,5900 \
  --source-ranges=<USER_IP>/32
```
🔴 不要開 0.0.0.0/0 — noVNC 和 VNC 都沒認證。

### Step 10 — 連線方式

| 方式 | URL | 備註 |
|------|-----|------|
| Safari 瀏覽器 | `http://<IP>` | 自動連線，推薦 |
| VNC Viewer App | `<IP>:5900` | 更順暢的觸控體驗 |
| noVNC 直連 | `http://<IP>:6080` | 需手動點 Connect |

冷啟動約 3-5 分鐘才顯示畫面。

## iOS 操作注意事項

| 問題 | 解法 |
|------|------|
| 畫面太大/太小 | noVNC Settings → Local Scaling + Clip to window |
| 捏合變成縮放頁面 | 已由 CSS `touch-action: none` 處理 |
| 點擊無反應 | 檢查 x11vnc 是否含 pipeinput 參數 |
| 點擊位置偏移 | 確認 adb_touch.sh 有座標縮放公式 |
| 連不上 port 80 | 電信商擋 port？走 VNC Viewer App |
| 斷線後回不來 | watchdog 每 3 分鐘自動恢復 |

## 效能研究對照

| 方案 | 延遲 | iOS 支援 | 安裝 |
|------|------|---------|------|
| 本方案（VNC + H.264 鏡像） | 中 | Safari + App | 無 |
| **scrcpy-mobile App**（最推） | 極低 | App Store 原生 App | 使用者安裝 |
| **ws-scrcpy**（WebRTC H.264） | 低 | 瀏覽器 | VM 需 Node.js |
| VNC 純裸（無鏡像管線） | 高 | Safari + App | 無 |

**VNC 的瓶頸：** ADB screenrecord 輸出 H.264 串流 → ffplay 解碼到 Xvfb → x11vnc 再用 RFB 協議傳送 framebuffer。這層層轉換是效能瓶頸。若要更順暢，建議使用者裝 **scrcpy-mobile**（App Store 搜尋 "Scrcpy Remote"），透過 ADB over WiFi 直連。

## 常見卡關

| 症狀 | 原因 | 解法 |
|------|------|------|
| VNC 連不上 | port 不開或防火牆沒設 | `docker port` + `gcloud firewall-rules list` |
| 模擬器一直重啟 | KVM 沒掛進容器 | 確認 `--device /dev/kvm` |
| 觸控沒反應 | pipeinput 路徑錯或 cache 未清 | 確認 adb_touch.sh 存在 + 刪除 `__pycache__` |
| noVNC 黑畫面 | 鏡像管線未啟動 | `docker exec` 檢查 ffplay 是否在跑 |
| 畫面被裁切 | Xvfb 解析度不符 | 檢查 `SCREEN_WIDTH=720, SCREEN_HEIGHT=1280` |
| 點擊位置不對 | 觸控縮放公式缺失 | adb_touch.sh 需 `x*1080/720` 和 `y*2400/1280` |

## 使用者偏好（老闆）

- 純正繁體中文，簡潔乾淨
- 不要中英夾雜
- 指令極簡，直接行動
- iPhone 優先：port 80 > port 6080
- 防火牆裸開禁忌：限期使用者 IP 即可
- **先測試再交付：** 不要跑完指令就回「好了」。必須確認 noVNC 頁面回 200、adb shell 回 boot_completed=1、螢幕 ON、Launcher 執行中，全部驗證無誤後再給連線資訊。
- **容器重啟 = 使用者斷線：** 每次 `docker stop/rm/run` 都會中斷現有連線。先用草稿容器測試完整流程，確認後一次到位。

## 各雲端 Nested Virtualization 支援

| 平台 | 支援 | 備註 |
|------|------|------|
| GCP | ✅ | `--enable-nested-virtualization` + N2 系列 + Intel CPU |
| AWS | ✅ | 需 .metal 或 bare metal 機型，一般 EC2 不行 |
| Azure | ✅ | Dv3/Ev3 系列以上 |
| Hetzner | ✅ | KVM 預設開，性價比最高 |
| Vultr | ✅ | Cloud Compute 高效能方案 |
