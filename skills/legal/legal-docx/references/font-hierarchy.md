# 書狀字階層次實戰教訓

## 問題歷程

| 版本 | 問題 | 用戶反饋 |
|:----:|:-----|:---------|
| v1 | 12pt 內文、20pt 行高、5 頁含說明頁 | 「字體怪怪的」「頁面是否太多」 |
| v2 | 14pt 內文、28pt 行高、5 頁 | 字級太大導致頁數暴增 |
| v3 | 12pt 內文、20pt 行高、2 頁 | 「字體大小要留意」— 段標與內文無層次 |
| v4 | 14pt 內文、20pt 行高（低於標準） | 「排版要在優化」 |
| **v5 最終** | **14pt + 25pt 行高 + 2.5cm 邊界 + 字階分明** | **用戶 TYPE-S 驗證通過** |

## 最終字階（司法院書狀規則第3條合規）

| 層級 | 大小 | 用途 | 備註 |
|:----:|:----:|:------|:------|
| L1 | **18pt 粗體** | 標題（暫緩執行聲請書） | 最大，一眼可見 |
| L2 | **16pt 粗體** | 段標題（一、二、三、四、五） | 與內文明顯區隔 |
| L3 | **15pt 粗體** | 主旨句（為聲請…事） | 在段標與內文中間 |
| L4 | **14pt** | 內文、案號、基本資料、附件、簽章 | 司法最低標準 |
| 頁碼 | **10pt** | 頁尾 | 最小不搶眼 |

## Linux 字型方案

**不要用 Noto Serif CJK TC（明體）或 DFKai-SB（Linux 無此字體）。**

正確作法：
```bash
sudo apt-get install -y fonts-cns11643-kai
```

```python
def set_font(run, size=14, bold=False):
    run.font.name = 'TW-Kai'      # 全字庫正楷體
    run.font.size = Pt(size); run.bold = bold
    rPr = run._element.get_or_add_rPr()
    rf = rPr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts'); rPr.insert(0, rf)
    rf.set(qn('w:eastAsia'), 'TW-Kai')
```

## 頁數目標與檢查

司法院標準（14pt + 25pt 行高）下，一般書狀約 350 字/頁。

**發送前檢查順序：**
1. 產出 docx
2. LibreOffice 轉 PDF
3. 檢查頁數（目標 ≤ 2 頁；3 頁可接受但第三頁不能只有簽名日期）
4. 檢查 A4 尺寸（MediaBox 595 x 842 pt）
5. 檢查字型嵌入（PDF 內應含 TW-Kai）
6. 寄送前附上格式說明（方便用戶在 Windows 用標楷體開啟）

## 頁數擁擠時的優先刪減順序

1. 先減段落間距（sa 值從 4→2→1→0 遞減）
2. 附件字型可縮至 13pt（仍在 14 號以上範圍）
3. 內文可精簡字句（刪贅字、合併短句）
4. 簽章區間距縮至最小
