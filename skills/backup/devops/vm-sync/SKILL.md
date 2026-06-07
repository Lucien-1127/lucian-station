---
name: vm-sync
description: Sync files and directories with remote VMs (GCP, KVM, custom SSH) using rsync or gcloud compute rsync.
version: 1.0.0
author: Hermes Agent
tags: [sync, vm, gcp, gcloud, rsync, ssh]
---

# VM / GCP Synchronization Skill

Use this skill to safely and efficiently synchronize your local directories (like the Obsidian vault) with remote VMs, Google Cloud Platform VMs (GCP VMs), or local virtual machines (KVM/VirtualBox).

## Features

- **Standard Rsync (SSH)**: Fast, optimized, incremental sync over regular SSH (supports custom ports like 22 or 2222).
- **GCP IAP Rsync**: Completely secure, passwordless sync with Google Cloud Platform VMs using Identity-Aware Proxy (IAP) with zero public IP exposure!
- **Incremental & Diff-Only**: Uses `rsync`'s delta-transfer algorithm to only send modified parts of files.

## CLI Usage

Run `vm-sync` directly from your WSL terminal:

```bash
vm-sync          # Run actual sync (interactive setup on first run)
vm-sync --setup  # Reconfigure target IP, remote directory, port, or mode
vm-sync --dry-run # Run trial sync to verify files without writing changes
vm-sync --help   # Show options
```

## Settings File

The configuration is saved as a simple bash-sourceable file under:
`~/.config/vm-sync/config`

Format:
```bash
SYNC_METHOD="rsync" # "rsync" or "gcloud"
REMOTE_IP="172.20.10.2"
REMOTE_PORT="22"
REMOTE_USER="ysga1"
REMOTE_DIR="/home/ysga1/vault"
GCP_VM="my-gcp-vm"
GCP_ZONE="asia-east1-a"
```
