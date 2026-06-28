---
name: tailscale
description: "Tailscale mesh VPN: install, authenticate, GCP firewall, Taildrop file transfer, subnet routing"
version: 1.0.0
author: agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [Tailscale, VPN, Taildrop, GCP, File Transfer, Mesh Networking]
prerequisites:
  commands: [tailscale]
---

# Tailscale on GCP VM

Tailscale creates a WireGuard-based mesh VPN (tailnet) connecting all your devices privately. This skill covers installation on a Linux VM, GCP firewall setup, authentication, and Taildrop file transfer.

## Quick Install

```bash
# Install (Ubuntu/Debian)
curl -fsSL https://tailscale.com/install.sh | sh

# Start and authenticate
sudo tailscale up
# → Visit the printed URL to authenticate with your Google/Apple/Microsoft account
```

## GCP Firewall (Required for direct P2P connections)

Create two ingress rules for Tailscale's UDP port 41641:

```bash
gcloud compute firewall-rules create allow-tailscale-udp \
  --allow udp:41641 --source-ranges 0.0.0.0/0 \
  --description "Tailscale direct connections IPv4"

gcloud compute firewall-rules create allow-tailscale-udp-v6 \
  --allow udp:41641 --source-ranges ::/0 \
  --description "Tailscale direct connections IPv6"
```

## Post-Install: Non-root File Access

After authentication, set the operator so file operations don't need sudo:

```bash
sudo tailscale set --operator=$USER
```

## Check Status

```bash
tailscale status
# Shows all connected devices with their Tailscale IPs
```

## Taildrop — File Transfer

**Send** from any device (iPhone/Android/Mac/PC):
- Share menu → Tailscale → select target device

**Receive** on Linux VM:

```bash
# Check for incoming files and move to ~/Downloads
tailscale file get --conflict rename ~/Downloads/
```

Files land in `~/Downloads/` (or specified directory).

## GCE Subnet Routing (Optional)

If you want other tailnet devices to reach GCE internal resources:

```bash
# Enable IP forwarding
echo 'net.ipv4.ip_forward = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
echo 'net.ipv6.conf.all.forwarding = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
sudo sysctl -p /etc/sysctl.d/99-tailscale.conf

# Advertise the subnet (replace with your GCE subnet)
tailscale set --advertise-routes=10.182.0.0/24 --accept-dns=false
```

## Security: Remove Public SSH

After confirming you can SSH via Tailscale IP, remove public SSH exposure:

```bash
gcloud compute firewall-rules delete default-allow-ssh
```

## Troubleshooting

### Taildrop: Access denied: file access denied

Run once: `sudo tailscale set --operator=$USER`
Then `tailscale file get` works without sudo.

### Taildrop: No files received

- Verify both devices are on the same tailnet (`tailscale status`)
- On iPhone: files appear in Files app → Tailscale folder (not automatically in Photos)
- On Linux: use `tailscale file get` explicitly — it doesn't auto-extract to Downloads

### Gmail App Passwords expire

See the `himalaya` skill for Gmail App Password troubleshooting.
