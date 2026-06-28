# 全國法規資料庫 API 規格

## 封裝格式

Law API 和 Order API 回傳的都是 ZIP 壓縮檔，內含一個 JSON 檔案。
ZIP 使用標準 DEFLATE 壓縮（method 8）。

## 端點

### 法律索引

```
GET https://law.moj.gov.tw/api/Ch/Law/JSON
```

回傳 ZIP → JSON 陣列。每筆欄位：

| 欄位 | 型態 | 範例 |
|------|------|------|
| LawName | string | 毒品危害防制條例 |
| LawURL | string | https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=C0000008 |
| LawLevel | string | 法律 |
| LawCategory | string | 刑事類 |
| LawModifiedDate | number | 20220504 |
| LawEffectiveDate | number | 20220504 |
| LawAbandonNote | string | （空字串）或「廢」 |
| LawHistories | string | 沿革全文 |
| LawArticles | array | 條文陣列 |

### 命令索引

```
GET https://law.moj.gov.tw/api/Ch/Order/JSON
```

同上格式，LawLevel 為「命令」。

### 條文格式（LawArticles 元素）

每筆條文：
| 欄位 | 說明 |
|------|------|
| ArticleNo | 條號（如「第1條」、「第2-1條」） |
| ArticleContent | 條文內容（HTML 已去除） |

### 歷史法規（舊版條文）

```
GET https://law.moj.gov.tw/LawClass/LawOldVer.aspx?pcode={PCODE}
```

回傳 HTML，需解析：
- 修正日期：`修正日期：</th><td>民國XXX年XX月XX日</td>`
- 條文：`<div class="col-no">...</div><div class="col-data">...</div>`

### 沿革

```
GET https://law.moj.gov.tw/LawClass/LawHistory.aspx?pcode={PCODE}
```

API 回傳的 LawHistories 欄位已經包含完整的沿革文字，格式為條列式號次：
```
1. 中華民國XXX年XX月XX日OOO令修正公布...
2. 中華民國XXX年XX月XX日OOO令修正公布...
```

## 資料規模（2026/06 實測）

| 項目 | 數量 |
|------|:----:|
| 法律 | 1,345 |
| 命令 | 10,423 |
| 總計 | 11,768 |
| 廢止 | ~3,517 |

## 頻率限制

API 無官方 rate limit 文件，但實測經驗：
- 單次下載 ~30MB ZIP，數秒完成
- 同一天重複下載回傳相同內容
- 建議同一天不重複下載（用快取日期判斷）
- g0v 國會 API (ly.govapi.tw) 較嚴格，建議退避重試（1500ms * attempt）

## 參考

- https://law.moj.gov.tw/ 全國法規資料庫
- https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode={PCODE} 單一法規條文
- https://data.gov.tw/dataset/35486 政府開放資料說明
