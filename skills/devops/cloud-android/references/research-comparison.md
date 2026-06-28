# 雲手機方案比較研究（2026年6月）

## 背景

從 iPhone 遠端操作 GCP 上 docker-android 模擬器。使用者在中華電信行動網路。

## 三種方案比較

### 1. VNC（本方案，已實作）

- **原理：** ADB screenrecord（H.264）→ ffplay → Xvfb → x11vnc → noVNC/websockify → Safari
- **延遲：** 中（200–500ms，取決於網路）
- **iOS 支援：** Safari + VNC Viewer App（RealVNC）
- **安裝：** 無需使用者安裝
- **優點：** 瀏覽器直連，免 App；nginx port 80 無電信商阻擋問題
- **缺點：** 兩層轉碼（H.264→X11→RFB），層層損耗；noVNC 觸控手勢有 iOS 相容問題（捏合、雙擊、300ms 延遲）
- **最佳化已做：** `touch-action:none` CSS、Local Scaling 預設、`cursor none`、觸控座標縮放

### 2. scrcpy-mobile App（最推薦）

- **專案：** [wsvn53/scrcpy-mobile](https://github.com/wsvn53/scrcpy-mobile)（MIT，⭐ 948）
- **原理：** ADB over WiFi 直連 iPhone，H.264 硬體解碼
- **延遲：** 極低（45–80ms，與 scrcpy 本機相當）
- **iOS 支援：** **App Store 原生 App** — 搜尋「Scrcpy Remote」
- **安裝：** 使用者需從 App Store 下載免費 App
- **優點：** 硬體解碼、最佳化行動網路手勢、URL scheme 一鍵連線、支援 iOS 鍵盤輸入、剪貼簿同步、音訊轉送
- **缺點：** 需額外安裝 App；GCP 防火牆需開放 ADB port（5555）
- **實做方式：**
  ```
  # VM 上啟用 ADB TCP/IP
  adb tcpip 5555
  
  # 防火牆開 5555（只限使用者 IP）
  gcloud compute firewall-rules create allow-adb-scrcpy \
    --allow tcp:5555 --source-ranges=<USER_IP>/32
  
  # iPhone App 連線
  App → Host: <VM_IP> → Port: 5555 → Connect
  ```

### 3. ws-scrcpy（WebRTC H.264）

- **專案：** [NetrisTV/ws-scrcpy](https://github.com/NetrisTV/ws-scrcpy)（MIT，⭐ 2.5k）
- **原理：** scrcpy fork 輸出 H.264 WebSocket 串流 → 瀏覽器 MSE/Broadway/TinyH264 播放
- **延遲：** 低（80–150ms）
- **iOS 支援：** Safari 瀏覽器（需 H.264 解碼能力）
- **安裝：** VM 需 Node.js + npm install + npm start
- **優點：** 免 App 安裝、H.264 直送無轉碼、支援多點觸控
- **缺點：** Node.js 服務需維護；emulator 有已知問題（ADB listens on internal interface → 需 proxy over adb）；Safari file upload 進度條異常
- **實做方式：**
  ```bash
  # VM 上
  git clone https://github.com/NetrisTV/ws-scrcpy.git
  cd ws-scrcpy
  npm install
  npm start  # port 8000
  # 防火牆開 8000
  ```

## 原始資料來源

- scrcpy-mobile GitHub: https://github.com/wsvn53/scrcpy-mobile
- ws-scrcpy GitHub: https://github.com/NetrisTV/ws-scrcpy
- docker-android custom configs: https://github.com/budtmo/docker-android/blob/master/documentations/CUSTOM_CONFIGURATIONS.md
- noVNC iOS touch issues: https://github.com/novnc/noVNC/issues/1267 (no touch gesture support)
- noVNC viewport/scale mobile: https://groups.google.com/g/novnc/c/zCghmk5xdsc
- noVNC touch device clip: https://github.com/novnc/noVNC/issues/1172 (Clip to Window forced on touch devices)
