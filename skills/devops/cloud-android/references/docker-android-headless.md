# docker-android 雲手機完整設定

## 容器啟動（完整參數）

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

## 容器內部環境變數（預設值）

| 變數 | 預設 | 最佳值 | 說明 |
|------|------|--------|------|
| SCREEN_WIDTH | 1600 | 720 | Xvfb 寬度，須等於 ffplay 輸出 |
| SCREEN_HEIGHT | 900 | 1280 | Xvfb 高度，須等於 ffplay 輸出 |
| SCREEN_DEPTH | 24+32 | 24 | 色彩深度 |
| WEB_VNC | false | true | 開啟 noVNC 網頁介面 |
| VNC_PORT | 5900 | 5900 | VNC 埠 |
| WEB_VNC_PORT | 6080 | 6080 | noVNC 埠 |
| NOVNC_VERSION | 1.7.0 | 1.7.0 | noVNC 版本 |
| WEBSOCKIFY_VERSION | 0.13.0 | 0.13.0 | websockify 版本 |

## x11vnc 啟動參數（需修改 app.py）

來源：`/home/androidusr/docker-android/cli/src/app.py` → `start_vnc_server()`

原始：
```python
args = f"-display {display} -forever -shared {last_arg}"
```

修改後：
```python
args = f"-display {display} -forever -shared -cursor none -pipeinput /tmp/adb_touch.sh {last_arg}"
```

**sed 單行：**
```bash
docker exec android-emu sed -i \
  's|-display {display} -forever -shared {last_arg}|-display {display} -forever -shared -cursor none -pipeinput /tmp/adb_touch.sh {last_arg}|' \
  /home/androidusr/docker-android/cli/src/app.py
```

**清除快取（每改必做）：**
```bash
docker exec android-emu bash -c 'find /home/androidusr/docker-android/cli -name "*.pyc" -delete'
```

## adb_touch.sh（含座標縮放）

```bash
#!/bin/bash
# Scale from VNC space (720x1280) to phone native (1080x2400)
while read L; do
  echo "$L" | grep -q "button_down" || continue
  x=$(echo "$L" | cut -d" " -f2)
  y=$(echo "$L" | cut -d" " -f3)
  px=$(( x * 1080 / 720 ))
  py=$(( y * 2400 / 1280 ))
  adb shell input tap $px $py 2>/dev/null
done
```

**為什麼需要縮放：**
- VNC/Xvfb 空間：720×1280（screenrecord 輸出）
- 手機原生：1080×2400（Pixel 8）
- 比例：X 軸 1.5 倍，Y 軸 1.875 倍
- `adb shell input tap` 使用原生座標
- 無縮放 → Y 軸誤差 88%，點擊嚴重偏位

## 鏡像管線（ADB screenrecord → ffplay）

```bash
adb exec-out screenrecord --output-format=h264 --bit-rate 6M --size 720x1280 /dev/stdout 2>/dev/null | \
  DISPLAY=:0 ffplay -v 0 -noborder -left 0 -top 0 -x 720 -y 1280 - 2>/dev/null
```

**bit-rate 選擇：**
- 4M：頻寬省但畫質差，適合低頻寬手機網路
- 6M：平衡點（推薦）
- 8M：畫質佳但可能卡頓

## noVNC defaults.json（iOS 優化）

```json
{
  "resize": "scale",
  "view_clip": true,
  "quality": 6,
  "compression": 9,
  "reconnect": true,
  "reconnect_delay": 5000,
  "show_dot": true,
  "shared": false,
  "view_only": false
}
```

## 容器內部 supervisord 管理

- 設定檔：`/home/androidusr/docker-android/mixins/configs/process/supervisord-screen.conf`
- `display_screen` → Xvfb + openbox
- `display_wm` → openbox session
- `vnc_server` → x11vnc
- `vnc_web` → websockify + noVNC
- 全部 `autorestart=true`

## 觸控管線資料流

```
iPhone 觸控 → noVNC → WebSocket → websockify → x11vnc
  → pipeinput → /tmp/adb_touch.sh → adb shell input tap
  → Android 觸控事件 → 回應畫面 → screenrecord → ffplay → Xvfb
  → x11vnc 捕捉 → noVNC 顯示
```

完整往返延遲約 200-500ms（取決於網路）。如果延遲大於 1 秒，建議改用 scrcpy-mobile App（ADB over WiFi 直連，無 Xvfb/VNC 中間層）。
