# Syncthing 無頭伺服器設定

## 安裝

```bash
sudo apt-get install -y syncthing
syncthing --version  # 確認版本
```

## 啟動

**重要：** `--home` 必須用**絕對路徑**，不能用 `~/`（不會展開）：

```bash
# ✅ 正確
syncthing --no-browser --home=/home/user/.config/syncthing

# ❌ 錯誤（目錄會變 ~/.config/syncthing 字面值）
syncthing --no-browser --home=~/.config/syncthing
```

無頭伺服器上 `systemctl --user` 會失敗（`Failed to connect to bus: No medium found`），必須用 background process 啟動：

```bash
terminal(command="syncthing --no-browser --home=/home/user/.config/syncthing", background=true)
```

## 常用操作

| 操作 | 指令 |
|------|------|
| 取得 Device ID | `syncthing --home=/home/user/.config/syncthing --device-id` |
| 重啟 | kill process → 重新啟動 background |
| 檢查連線 | `ps aux \| grep syncthing \| grep -v grep` |
| 監看日誌 | `process(action="poll")` 或 `process(action="log")` |

## 設定遠端裝置

加入另一台裝置到 config.xml：

```xml
<device id="遠端-DEVICE-ID" name="使用者名稱" compression="metadata" introducer="false" skipIntroductionRemovals="false" introducedBy="">
    <address>dynamic</address>
    <paused>false</paused>
    <autoAcceptFolders>true</autoAcceptFolders>
    <maxSendKbps>0</maxSendKbps>
    <maxRecvKbps>0</maxRecvKbps>
    <maxRequestKiB>0</maxRequestKiB>
    <untrusted>false</untrusted>
    <remoteGUIPort>0</remoteGUIPort>
    <numConnections>0</numConnections>
</device>
```

`autoAcceptFolders=true` 讓 Syncthing 自動接受對方分享的資料夾。

## 資料夾同步

當遠端裝置分享資料夾後，Syncthing 自動建立資料夾條目，但需要手動修正：

### ⚠️ 常見陷阱：`~` 不會展開

自動建立的資料夾路徑可能是 `~/obsidian` 而非完整路徑。**必須改成絕對路徑：**

```xml
<!-- ❌ 錯誤 -->
<folder id="xxx" label="obsidian" path="~/obsidian" ...>

<!-- ✅ 正確 -->
<folder id="xxx" label="obsidian" path="/home/user/obsidian-vault" ...>
```

### ⚠️ 常見陷阱：缺少 .stfolder 標記

如果資料夾路徑不存在或缺少標記檔，Syncthing 會報錯：
```
WARNING: Error on folder "obsidian": folder marker missing
```

**解法：建立 `.stfolder` 空檔案**
```bash
mkdir -p /home/user/obsidian-vault
touch /home/user/obsidian-vault/.stfolder
```

然後觸發重掃：
```bash
curl -s -X POST -H "X-API-Key: YOUR_API_KEY" \
  http://127.0.0.1:8384/rest/db/scan?folder=FOLDER_ID
```

## 連線類型

| 連線方式 | 日誌特徵 | 說明 |
|---------|---------|------|
| 中繼 (Relay) | `relay-client/TLS1.3-...` | 無法直連時的備用方案，不斷連線/斷線為正常 |
| 直連 (QUIC) | `quic-server/TLS1.3-...` | 最佳連線方式，穩定 |
| 直連 (TCP) | `tcp-server/TLS1.3-...` | 另一種直連方式 |

## 常用 API

所有 API 需要 `X-API-Key`（從 config.xml 的 `<apikey>` 標籤取得）：

```bash
API_KEY=*** "xxx"
BASE=http://127.0.0.1:8384

# 檢查連線狀態
curl -s -H "X-API-Key: $API_KEY" $BASE/rest/system/connections

# 檢查資料夾狀態
curl -s -H "X-API-Key: $API_KEY" $BASE/rest/db/status?folder=FOLDER_ID

# 觸發重掃
curl -s -X POST -H "X-API-Key: $API_KEY" $BASE/rest/db/scan?folder=FOLDER_ID

# 查看完整設定
curl -s -H "X-API-Key: $API_KEY" $BASE/rest/system/config
```

## GCP VM 特定注意事項

- NAT 穿透依賴中繼伺服器，連線可能不穩定（連了又斷是正常的）
- QUIC 直連在多次嘗試後會建立
- UDP buffer 警告可忽略：`failed to sufficiently increase receive buffer size`
- GUI 只監聽 `127.0.0.1:8384`，不對外開放