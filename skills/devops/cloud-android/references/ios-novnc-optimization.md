# iOS noVNC 優化技術

## 已知問題

| 問題 | iOS Safari 行為 | VNC Viewer App |
|------|----------------|----------------|
| 捏合縮放 | 瀏覽器層級縮放，干擾 VNC 觸控 | 無此問題 |
| 雙擊縮放 | 300ms 延遲後觸發縮放 | 無此問題 |
| rubber-band 彈性捲動 | Safari 慣性滑動，畫面偏離 | 無此問題 |
| 非標準 port | 電信商可能封鎖 6080/5900 | 支援自訂 port |
| 觸控延遲 | VNC 協議本身就有延遲 | 比瀏覽器順 |

## 解決方案

### CSS 防護（容器內 base.css 追加）

```css
/* 防止 iOS 捏合縮放干擾 VNC 觸控 */
#noVNC_container { touch-action: none !important; }

/* 防止 iOS rubber-band 彈性捲動 */
body {
    overscroll-behavior: none !important;
    overflow: hidden !important;
    position: fixed !important;
    width: 100% !important;
    height: 100% !important;
}

/* 隱藏點不用的控制項（行動版畫面更清爽） */
#noVNC_control_bar_handle { display: none !important; }
```

### default.json（自動套用設定）

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

### viewport meta（已內建於 vnc.html）

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
```

### 登入頁面 JS 防護

```javascript
document.addEventListener('touchmove', function(e) { e.preventDefault(); }, { passive: false });
document.addEventListener('gesturestart', function(e) { e.preventDefault(); });
```

## 連線方式建議（依優先序）

1. **VNC Viewer App**（iPhone 去 App Store 下載 `RealVNC Viewer`）— 觸控手勢最穩定
2. **Safari port 80**（透過 nginx 反代）— 適合快速瀏覽
3. **Safari port 6080**（直連 noVNC）— 某些電信商會擋

## 操作步驟（給使用者）

1. 打開 `http://<IP>`
2. 點「連線」按鈕
3. 點「Approve」（伺服器身分）
4. 右上角「Full screen」進入全螢幕
5. 齒輪圖示 → Settings → Scaling mode 選 **Local scaling**
6. Clip to window 打勾
