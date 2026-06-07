---
name: google-sheets-finance-tracker
description: Build automated financial portfolio trackers in Google Sheets using Google Apps Script (GAS) — ETF trackers, stock portfolios, dividend tracking, and performance dashboards.
keywords: google sheets, gas, google apps script, portfolio, etf, stock, dividend, finance, dashboard
---

# Google Sheets Finance Tracker (GAS)

Build automated financial portfolio trackers in Google Sheets with Google Apps Script — from local Excel/Python workflows to cloud-based Google Sheets with automatic daily updates.

## Trigger Conditions

- User wants to build an ETF / stock / portfolio tracker in Google Sheets
- User wants to migrate from local Excel (openpyxl) / Python to Google Sheets
- User needs automated daily data updates (stock prices, dividends)
- User wants a dashboard (儀表板) as the homepage of the spreadsheet

## Architecture Pattern

### Recommended Sheet Structure (6 sheets)

| Sheet | Purpose | Update Mode |
|-------|---------|-------------|
| 📊總覽 (Dashboard) | KPI cards, holdings table, charts | Formula + GAS daily |
| 📝交易記錄 (Transactions) | Buy/sell log with fee/tax | Manual input |
| 📈每日持倉 (Daily Holdings) | Daily price snapshots | GAS daily auto |
| 💰配息記錄 (Dividends) | Dividend history | GAS auto + manual |
| 📅月度損益 (Monthly P&L) | Monthly performance | Formula-driven |
| 📋ETF清單 (ETF Master List) | Master data for tracked ETFs | Manual + read by GAS |

### Dashboard (儀表板) — must be first sheet

**Row 1: KPI Cards (6 cards, 2 columns each)**
- 總投入成本 (Total Cost)
- 目前市值 (Current Value)
- 未實現損益 (Unrealized P&L = Value − Cost)
- 整體報酬率 (Return %)
- 累計配息收入 (Cumulative Dividends)
- 最後更新日 (Last Updated = TODAY())

**Holdings Table (from row 7~8 onward):**
ETF代碼 | ETF名稱 | 持有股數 | 平均成本 | 當前價格 | 市值 | 成本合計 | 未實現損益 | 報酬率% | 持倉比重% | 累計配息 | 備註

Formula-driven columns: 市值=股數×價格, 成本=股數×均價, 損益=市值−成本, 報酬率=損益/成本, 比重=市值/總市值

### Key Differences from Local Excel

| Local Excel (openpyxl) | Google Sheets (GAS) |
|------------------------|---------------------|
| yfinance API (Python) | GOOGLEFINANCE() or UrlFetchApp |
| openpyxl formatting | Range.setBackground/Font/Border |
| cron job / manual run | ScriptApp time-based trigger |
| Conditional formatting rules | GAS conditional formatting or setBackground |

## Google Apps Script Essentials

### Built-in GOOGLEFINANCE (no API key needed)

```
=GOOGLEFINANCE("TPE:0050", "price")       — TW ETF real-time price
=GOOGLEFINANCE("SPY", "price")            — US ETF price
=GOOGLEFINANCE("0050.TW", "dividend")     — TW ETF dividend history
```

### GAS APIs

```javascript
// Read/write sheets
const ss = SpreadsheetApp.getActiveSpreadsheet();
const ws = ss.getSheetByName("📈每日持倉");
const data = ws.getRange(3, 1, lastRow-2, 10).getValues();

// Fetch external data (Yahoo Finance fallback)
const url = `https://query1.finance.yahoo.com/v8/finance/chart/${symbol}`;
const res = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
const json = JSON.parse(res.getContentText());

// Time-driven daily trigger
ScriptApp.newTrigger("dailyUpdate")
  .timeBased()
  .everyDays(1)
  .atHour(8)
  .inTimezone("Asia/Taipei")
  .create();

// Custom menu
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("📊 ETF 工具")
    .addItem("🔄 更新今日股價", "dailyUpdate")
    .addItem("💰 抓取配息記錄", "fetchDividends")
    .addSeparator()
    .addItem("⚙️ 建立每日排程", "createTrigger")
    .addToUi();
}
```

## Daily Update Script Flow

1. **Read ETF list** from 📋ETF清單 (columns: 代碼, yfinance代碼, 名稱, 配息頻率...)
2. **Calculate holdings** from 📝交易記錄 (buy/sell → shares + avg cost per ETF)
3. **Fetch prices** — try GOOGLEFINANCE first, fallback to UrlFetchApp+Yahoo
4. **Append to 📈每日持倉** — check for duplicate (date+code) before inserting
5. **Fetch dividends** — Yahoo Finance dividends endpoint, skip duplicates
6. **Append to 💰配息記錄** — new rows with ex-date + amount
7. **Update dashboard** — refresh KPI formulas

## GAS Formatting Helper Patterns

### Reusable Formatting Functions

```javascript
// Dark title bar with gold text (page title)
function writePageTitle(sheet, row, numCols, text) {
  var range = sheet.getRange(row, 1, 1, numCols);
  range.merge();
  range.setValue(text);
  range.setBackground('#1F3864');
  range.setFontColor('#C9A227');
  range.setFontSize(14);
  range.setFontWeight('bold');
  range.setHorizontalAlignment('center');
  range.setVerticalAlignment('middle');
  sheet.setRowHeight(row, 32);
}

// Blue section separator with white text
function writeSectionTitle(sheet, row, numCols, text) {
  var range = sheet.getRange(row, 1, 1, numCols);
  range.merge();
  range.setValue(text);
  range.setBackground('#2E75B6');
  range.setFontColor('#FFFFFF');
  range.setFontSize(11);
  range.setFontWeight('bold');
  range.setVerticalAlignment('middle');
  sheet.setRowHeight(row, 22);
}

// Dark header with white bold text + border
function writeHeaderRow(sheet, row, headers, bgColor) {
  bgColor = bgColor || '#1F3864';
  var range = sheet.getRange(row, 1, 1, headers.length);
  range.setValues([headers]);
  range.setBackground(bgColor);
  range.setFontColor('#FFFFFF');
  range.setFontWeight('bold');
  range.setFontSize(10);
  range.setHorizontalAlignment('center');
  range.setVerticalAlignment('middle');
  range.setBorder(true, true, true, true, null, null, '#9DC3E6', SpreadsheetApp.BorderStyle.SOLID);
  sheet.setRowHeight(row, 24);
}

// Alternating row colors (light blue stripe)
function writeDataRange(sheet, startRow, endRow, numCols) {
  for (var r = startRow; r <= endRow; r++) {
    var bg = (r % 2 === 0) ? '#F2F7FB' : '#FFFFFF';
    var range = sheet.getRange(r, 1, 1, numCols);
    range.setBackground(bg);
    range.setFontSize(9);
    range.setVerticalAlignment('middle');
    range.setBorder(true, true, true, true, null, null, '#D0D0D0', SpreadsheetApp.BorderStyle.SOLID);
    sheet.setRowHeight(r, 20);
  }
}
```

### Dashboard KPI Card Layout (2 columns per KPI)

Place KPI cards in pairs: column N = label, column N+1 = value. Arrange 5-6 KPIs across row 4:

| Col A-B | Col C-D | Col E-F | Col G-H | Col I-J |
|---------|---------|---------|---------|---------|
| 總投入成本 | 目前總市值 | 未實現損益 | 整體報酬率 | 累計配息收入 |
| ='交易記錄'!K3 | =SUM('看板'!H5:H54) | =C4-B4 | =IF(B4=0,"",(C4-B4)/B4) | ='配息記錄'!G3 |

Label cell: `#BDD7EE` bg, `#1F3864` text, 9pt bold, centered.
Value cell: 14pt bold, `#1F3864` text, `setNumberFormat('#,##0')`.

### Conditional Format Rules (programmatic)

```javascript
// Color rules: green for profit, red for loss
var profitRule = SpreadsheetApp.newConditionalFormatRule()
  .whenNumberGreaterThan(0)
  .setBackground('#E2EFDA')
  .setFontColor('#375623')
  .setRanges([sheet.getRange('J5:J54')])
  .build();

var lossRule = SpreadsheetApp.newConditionalFormatRule()
  .whenNumberLessThan(0)
  .setBackground('#FCE4D6')
  .setFontColor('#843C0C')
  .setRanges([sheet.getRange('J5:J54')])
  .build();

var rules = sheet.getConditionalFormatRules();
rules.push(profitRule, lossRule);
sheet.setConditionalFormatRules(rules);
```

### Data Validation (Dropdown Lists)

```javascript
// Buy/Sell dropdown
var dvBS = SpreadsheetApp.newDataValidation()
  .requireValueInList(['買入', '賣出'], true)
  .build();
sheet.getRange('D5:D504').setDataValidation(dvBS);

// Dividend frequency dropdown
var dvFreq = SpreadsheetApp.newDataValidation()
  .requireValueInList(['月配', '季配', '半年配', '年配'], true)
  .build();
sheet.getRange('G4:G103').setDataValidation(dvFreq);
```

### Embedded Charts

```javascript
var chart = sheet.newChart()
  .setChartType(Charts.ChartType.LINE)
  .addRange(sheet.getRange("'📅資產記錄'!A4:A"))
  .addRange(sheet.getRange("'📅資產記錄'!C4:C"))
  .setPosition(startRow, startCol, 0, 0)
  .setOption('title', '總資產趨勢')
  .setOption('height', 300)
  .setOption('width', 600)
  .setOption('legend', { position: 'bottom' })
  .setOption('curveType', 'function')
  .build();
sheet.insertChart(chart);
```

### Removing Charts Before Clearing

When re-initializing a sheet, delete existing charts first to avoid "cannot modify chart" errors:

```javascript
var charts = sheet.getCharts();
charts.forEach(function(c) { sheet.removeChart(c); });
```

## Yahoo Finance Dividend Fetch (GAS)

```javascript
function fetchDividends() {
  var existingDivs = {};
  var divData = divSheet.getRange('A5:B504').getValues();
  for (var i = 0; i < divData.length; i++) {
    var d = divData[i][0], c = divData[i][1];
    if (d && c) {
      var dateStr = (typeof d === 'object') ? d.toISOString().split('T')[0] : String(d);
      existingDivs[dateStr + '_' + String(c).trim()] = true;
    }
  }

  var url = 'https://query1.finance.yahoo.com/v8/finance/chart/' +
            encodeURIComponent(yfCode) + '?range=2y&interval=1d&events=div';
  var response = UrlFetchApp.fetch(url, {
    headers: { 'User-Agent': 'Mozilla/5.0 ...' },
    muteHttpExceptions: true
  });
  var json = JSON.parse(response.getContentText());
  var dividends = json.chart.result[0].events.dividends;

  Object.keys(dividends).sort().forEach(function(ts) {
    var ev = dividends[ts];
    var exDate = new Date(ev.date * 1000);
    var key = exDate.toISOString().split('T')[0] + '_' + yfCode;
    if (existingDivs[key]) return;

    divSheet.getRange(nextRow, 1).setValue(exDate);
    divSheet.getRange(nextRow, 2).setValue(yfCode);
    divSheet.getRange(nextRow, 5).setValue(ev.amount);
    nextRow++;
  });
}
```

Key points:
- `events=div` query param is required to include dividend events
- Response structure: `json.chart.result[0].events.dividends` is a map of timestamp -> {date, amount}
- Always sort timestamps (Object.keys()) before iterating
- De-duplicate against existing records using a Set of "date_code" keys

## Daily Snapshot Recording Pattern

```javascript
function recordDailySnapshot() {
  // Check if today already has a record
  var dateCol = history.getRange('A4:A503');
  var exists = dateCol.getValues().some(function(row) {
    var d = row[0];
    return d && typeof d === 'object' && d.toDateString() === new Date().toDateString();
  });
  if (exists) return;

  // Find first empty row
  var nextRow = 4;
  while (history.getRange(nextRow, 1).getValue() !== '') {
    nextRow++;
  }

  // Aggregate values from other sheets
  var totalValue = board.getRange('H5:H54').getValues()
    .reduce(function(sum, row) { return sum + (typeof row[0] === 'number' ? row[0] : 0); }, 0);

  // Write record
  history.getRange(nextRow, 1).setValue(new Date());
  history.getRange(nextRow, 2).setValue(totalCost);
  history.getRange(nextRow, 3).setValue(totalValue);
  history.getRange(nextRow, 4).setFormula('=IF(B' + nextRow + '=0,"",C' + nextRow + '-B' + nextRow + ')');
}
```

## Two-File Project Structure

For maintainability, split GAS code into two files:

| File | Contents | When to use |
|------|----------|-------------|
| `初始化試算表.gs` | `initializeSpreadsheet()` — creates all sheets, formats, formulas, charts, sample data | Run ONCE at setup |
| `自動更新與選單.gs` | `onOpen()`, `refreshPrices()`, `recordDailySnapshot()`, `fetchDividends()`, `setupTriggers()` | Everyday automation |

Also provide a `完整版_全合一.gs` combined file for users who prefer one-file paste.

### Deliverable Convention (用戶偏好)
- **File names**: Use Chinese file names with emoji prefixes (e.g. `📄 初始化試算表.gs`) for Taiwanese users
- **Test before deliver**: Run syntax checks (`node --check`) on all .gs/.js files before delivery
- **Reference templates**: When designing layout, browse professional templates (e.g., iCenter ETF 儀表板) for layout inspiration

## iCenter-Style Two-Zone Architecture (參考)

Professional financial trackers (iCenter/艾森ETF儀表板) use a two-zone layout:

| Zone | Sheets | Purpose |
|------|--------|---------|
| **A區** (Overall) | A1-總儀表板, A2-資產配置, A3-看板, A4-現金流, A5-ETF現金流, A6-資金匯兌, A7-資產記錄, A8-再平衡, A9/A10-匯入 | Aggregate all accounts |
| **B區** (Per Account) | B1-儀表板, B2-現金流, B3-ETF現金流, B4-資金匯兌, B5-資產記錄 | Per-account detail |

For single-portfolio users, simplify to 6 sheets: 📊儀表板 -> 📝交易記錄 -> 📈ETF看板 -> 💰配息記錄 -> 📅資產記錄 -> 📋ETF清單.

## Pitfalls & Gotchas

- **GOOGLEFINANCE only supports major exchanges** (TPE, NYSE, NASDAQ, HKEx). For other markets, use UrlFetchApp + Yahoo Finance.
- **Yahoo Finance API is unofficial** — it can change without notice. Endpoint: `https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=2y&interval=1d&events=div`
- **TW stock symbol format**: use `TPE:0050` for GOOGLEFINANCE, `0050.TW` for Yahoo Finance.
- **GAS daily quotas**: ~20K UrlFetch calls/day, 90 min total runtime, 30 min max per trigger execution.
- **Duplicate prevention**: Always check existing (date, code) pairs before inserting records in daily/dividend sheets.
- **Time zone matters**: Set `inTimezone("Asia/Taipei")` on triggers, otherwise GAS defaults to US time zone.
- **Rate limiting**: Insert `Utilities.sleep(500-1000)` between fetch calls.
- **Menu creation**: Call `onOpen()` from script editor once to register the custom menu.
- **Conditional formatting**: Use `SpreadsheetApp.newConditionalFormatRule()`, not hardcoded colors.
- **Clear charts before re-initializing**: `sheet.getCharts().forEach(c => sheet.removeChart(c))`.
- **Cross-sheet formula references**: Always quote emoji sheet names: `='📈ETF看板'!H5`.
- **First-time authorization**: User must manually run one function from script editor to trigger OAuth.
- **Formula vs. value tradeoff**: Use GOOGLEFINANCE for real-time display, GAS setValue() for historical records.

## References

See `references/` directory for session-specific implementation details.