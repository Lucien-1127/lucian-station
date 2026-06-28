# GCP VM 建置參考

## 完整 VM 建立指令

```bash
gcloud compute instances create type-q \
  --zone=asia-east1-b \
  --machine-type=n2-standard-4 \
  --min-cpu-platform="Intel Cascade Lake" \
  --enable-nested-virtualization \
  --boot-disk-size=50GB \
  --boot-disk-type=pd-ssd \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud
```

## disk 擴容（30GB → 50GB）

```bash
gcloud compute disks resize type-q --size=50 --zone=asia-east1-b
# 進 VM 後：
sudo growpart /dev/disk/by-id/xxx 1
sudo resize2fs /dev/disk/by-id/xxx-part1
```

## 錯誤恢復：nested virt 沒吃到

驗證：
```bash
grep -cw vmx /proc/cpuinfo   # Intel
grep -cw svm /proc/cpuinfo   # AMD
```
都回傳 0 → VM 需要停啟重排主機：
```bash
gcloud compute instances stop type-q --zone=asia-east1-b
gcloud compute instances start type-q --zone=asia-east1-b
```
啟動後 KVM module 需手動載入：
```bash
sudo modprobe kvm && sudo modprobe kvm_intel
```

## 防火牆規則（安全注意！）

🔴 全部都要綁使用者 IP，不開 0.0.0.0/0：
```bash
gcloud compute firewall-rules create allow-novnc-typeq --allow tcp:6080 --source-ranges=<IP>/32
gcloud compute firewall-rules create allow-vnc-typeq --allow tcp:5900 --source-ranges=<IP>/32
gcloud compute firewall-rules create allow-http-typeq --allow tcp:80 --source-ranges=<IP>/32
```

## 自動恢復（systemd service）

把 `/opt/cloudphone-setup.sh` 設為 systemd oneshot service：
```ini
[Unit]
Description=Cloud Phone setup
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=/opt/cloudphone-setup.sh
RemainAfterExit=yes
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
```
