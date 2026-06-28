#!/bin/bash
#
# android-screen-mirror.sh — 將 Android 模擬器畫面鏡像到 Xvfb 供 NoVNC 顯示
#
# 用法: ./android-screen-mirror.sh [container_name]
#       預設 container_name = android-emu
#
# 說明: docker-android 的 NoVNC 常顯示空白 Xvfb 桌面，
#       因為模擬器用 -gpu swiftshader_indirect 離屏渲染。
#       此腳本用 ADB screenrecord + ffplay 將畫面映射到 Xvfb。
#
# 注意: 此腳本需在容器內以 androidusr 身份執行。
#       ffmpeg/ffplay 必須已安裝在容器內（budtmo/docker-android 預設有）。

set -e

CONTAINER="${1:-android-emu}"

echo ">>> Mirroring Android screen in container '${CONTAINER}'..."

docker exec "${CONTAINER}" bash -c '
# 清除舊的 mirror 行程
pkill -f "adb.*screenrecord" 2>/dev/null || true
pkill -f ffplay 2>/dev/null || true
sleep 1

# 啟動 screenrecord -> ffplay 管道
nohup bash -c \
  "adb exec-out screenrecord \
    --output-format=h264 \
    --bit-rate 4M \
    --size 720x1280 \
    /dev/stdout 2>/dev/null | \
   DISPLAY=:0 ffplay \
    -v 0 \
    -noborder \
    -x 720 \
    -y 1280 \
    - 2>/dev/null" \
  > /dev/null 2>&1 &

sleep 3

# 確認有起來
if pgrep -f "ffplay" > /dev/null; then
    echo ">>> Screen mirror started successfully!"
    echo "    Refresh your NoVNC browser to see the Android screen."
else
    echo ">>> ERROR: ffplay failed to start. Check if ADB is connected."
    exit 1
fi
'
