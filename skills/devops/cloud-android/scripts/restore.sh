#!/bin/bash
# Cloud Phone Restore — idempotent health check

CONTAINER=android-emu
MAX_WAIT=120

wait_for_container() {
    local el=0
    while [ $el -lt $MAX_WAIT ]; do
        docker ps --format '{{.Names}}' | grep -q "^$CONTAINER$" && return 0
        sleep 2; el=$((el+2))
    done
    return 1
}

echo "[$(date)] Cloud Phone check..."
wait_for_container || { echo "Container not found"; exit 1; }

docker exec $CONTAINER bash -c '[ -f /tmp/adb_touch.sh ]' || {
    echo "Writing adb_touch.sh..."
    docker exec $CONTAINER python3 /dev/stdin << 'PYEOF'
content = """#!/bin/bash
while read L; do
  echo "$L" | grep -q "button_down" || continue
  x=$(echo "$L" | cut -d" " -f2)
  y=$(echo "$L" | cut -d" " -f3)
  px=$(( x * 1080 / 720 ))
  py=$(( y * 2400 / 1280 ))
  adb shell input tap $px $py 2>/dev/null
done
"""
with open('/tmp/adb_touch.sh', 'w') as f: f.write(content)
import os; os.chmod('/tmp/adb_touch.sh', 0o755); print('OK')
PYEOF
}

docker exec $CONTAINER bash -c 'grep -q "pipeinput" /home/androidusr/docker-android/cli/src/app.py' || {
    echo "Patching app.py..."
    docker exec $CONTAINER sed -i \
      's|-display {display} -forever -shared {last_arg}|-display {display} -forever -shared -cursor none -pipeinput /tmp/adb_touch.sh {last_arg}|' \
      /home/androidusr/docker-android/cli/src/app.py
    docker exec $CONTAINER bash -c 'find /home/androidusr/docker-android/cli -name "*.pyc" -delete'
}

docker exec $CONTAINER bash -c 'ps aux | grep x11vnc | grep -q pipeinput' || {
    echo "Restarting x11vnc..."
    docker exec $CONTAINER bash -c 'pkill -f "x11vnc.*-display" 2>/dev/null'
    sleep 3
}

docker exec $CONTAINER pgrep -x ffplay >/dev/null && { echo "Mirror OK"; exit 0; }

echo "Starting mirror..."
nohup docker exec $CONTAINER bash -c '
el=0
while [ $el -lt 120 ]; do
  adb get-state 2>/dev/null | grep -q device && break
  sleep 5; el=$((el+5))
done
while [ $el -lt 600 ]; do
  b=$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d "\r")
  [ "$b" = "1" ] && break
  sleep 5; el=$((el+5))
done
adb exec-out screenrecord --output-format=h264 --bit-rate 6M --size 720x1280 /dev/stdout 2>/dev/null | \
DISPLAY=:0 ffplay -v 0 -noborder -left 0 -top 0 -x 720 -y 1280 - 2>/dev/null
' > /dev/null 2>&1 &
echo "Mirror started"
