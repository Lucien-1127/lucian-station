# Inbox Cleanup Workflow

A repeatable process for cleaning a cluttered inbox by category.

## Classification Categories

| Category | Examples | Action |
|----------|----------|--------|
| 🗑 **Spam/Advertising** | foodpanda promos, 元大證券投顧推銷, ASUS/Canva/Klook 行銷, 天下學習課程廣告, Readmoo 書籍推薦, Binance 推銷 | Move to trash directly |
| 🔔 **System Notifications** | Verification codes, login alerts, billing/payment notices, TOS updates, trial notifications, Google Cloud/Firebase updates | User typically wants these deleted |
| 📰 **Newsletters (subscribed)** | Perplexity 接案市場, MyClaw Newsletter, Matter, OpenRouter updates, Kilo Weekly | Ask user — may want to keep or review first |
| 🛒 **Order Confirmations** | foodpanda order receipts, purchase confirmations | Keep (not ads) |
| 🔐 **Security Alerts** | 集保登入通知, 元大登入失敗通知, OpenRouter device sign-in | User may want them deleted or kept — ask |
| ❓ **Uncertain** | 天下訂戶週報, NVIDIA GTC, 讀墨推薦, 天下學習, Binance pre-IPO | **Ask the user** — don't guess |

## Workflow Steps

1. **Scan inbox** — `himalaya envelope list --page 1 --page-size 50`
2. **Classify** each email into one of the categories above
3. **Ask before acting** on newsletters, subscriptions, or anything uncertain
4. **Move known spam/notifications** directly: `himalaya message move "[Gmail]/垃圾桶" <ID1> <ID2> ...`
5. **Handle unsubscribes** — find `List-Unsubscribe` header in raw email (`himalaya message export <ID> --full`), then visit the URL via browser or web_extract
6. **Verify** by re-listing inbox

## Syntax Reminder

`himalaya message move` takes **target first, then IDs**:
```bash
himalaya message move "[Gmail]/垃圾桶" 10435 10414 10432
# NOT: himalaya message move 10435 "[Gmail]/垃圾桶"
```

When messages are moved, their IDs change in the new folder. Use `--folder` to list the trash if you need to find moved emails:
```bash
himalaya envelope list --folder "[Gmail]/垃圾桶" --page 1 --page-size 20
```

## Unsubscribe Flow

1. Find the email in trash: `himalaya envelope list --folder "[Gmail]/垃圾桶"`
2. Export raw headers: `himalaya message export <TRASH_ID> --full --folder "[Gmail]/垃圾桶"`
3. Extract `List-Unsubscribe` URL
4. Visit the URL to confirm unsubscription (browser or web_extract)
5. Note: some unsubscribe pages require login — report to user if so