#!/usr/bin/env python3
"""Refresh GCP MCP token in ~/.hermes/.env

This script is invoked by cron (every 30 min) as a no_agent watchdog.
On success: silent (empty stdout) — cron delivers nothing.
On failure: stderr message — cron delivers error notification.

Usage: python3 refresh-gcp-mcp-token.py
"""
import json, re, subprocess, sys, urllib.request
from pathlib import Path

def get_token():
    # 1. GCE metadata server (VM with service account)
    try:
        req = urllib.request.Request(
            "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
            headers={"Metadata-Flavor": "Google"}
        )
        resp = urllib.request.urlopen(req, timeout=5)
        return json.loads(resp.read())["access_token"]
    except Exception:
        pass
    # 2. Fallback: gcloud ADC
    try:
        out = subprocess.run(
            ["gcloud", "auth", "application-default", "print-access-token"],
            capture_output=True, text=True, timeout=30
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        pass
    return None

token = get_token()
if not token:
    print("FAILED: GCP MCP token refresh — no token from metadata or gcloud", file=sys.stderr)
    sys.exit(1)

env_path = Path.home() / ".hermes" / ".env"
content = env_path.read_text()
replacement = f"GCP_MCP_TOKEN={token}"
new_content = re.sub(r"^GCP_MCP_TOKEN=.*", replacement, content, flags=re.MULTILINE)
if new_content == content:
    new_content = content.rstrip() + "\n" + replacement + "\n"
env_path.write_text(new_content)
# Silent on success - no_agent watchdog delivers empty stdout = nothing
