---
name: legal-docx
description: 台灣法律書狀 Word/PDF 產生器。司法院書狀規則第3條：全字庫正楷體TW-Kai 14pt、行高25-26pt、邊界四面2.5cm、目標2頁。字階18>16>14pt。LibreOffice headless 轉PDF。smtplib寄附件。v8研究先於輸出。
---

# 台灣法律書狀 Word 檔產生器

## ⚠️ 研究先於輸出（v8 新增 — 不可跳過）

法律文件輸出前必須完成以下研究動作，否則輸出與 generic AI 無異：

```
[GATE: CITATION層 → EXECUTION層] ← 必須先通過此閘門
□ 法條依據：≥3 條相關法條（名稱＋條號）已識別，並在文件中引用
□ 樣本研究：≥1 份合格書狀範本已分析（結構＋用語記錄在 references/）
□ 引用慣例：法條引用格式已對照合格文件確認
□ 警示識別：該類型文件的高風險點已列出（≥2 項）
□ 差異化檢查：本文檔與 generic AI 輸出有何不同？（必須能說出具體根據）
```

**不完成研究動作的輸出範例（已遭用戶糾正）：**
- 跳過 web_search 合格範本，直接用「一般合約知識」輸出
- 引用法條時只寫「根據民法」而不標明具體條號
- 遣詞用語未對照合格文件，全憑感覺

---

## 前置

```bash
pip3 install python-docx
sudo apt-get install -y libreoffice-writer   # docx→PDF 轉換（headless 可，GCP 不需圖形）
sudo apt-get install -y fonts-cns11643-kai   # 全字庫正楷體 TW-Kai（臺灣國家標準楷體）
```

## ⚠️ 核心格式鐵律（勿使用預設值）

| 項目 | 規格 | 錯誤做法 |
|------|------|----------|
| 紙張 | A4（21.0 x 29.7 cm） | Letter |
| 字體 | **全字庫正楷體 TW-Kai**（Linux 裝 fonts-cns11643-kai）<br>Windows 用標楷體 DFKai-SB | Noto Serif CJK TC（非楷體，不符司法慣例） |
| **標題** | **18 pt** 粗體置中 | 20pt（太大） |
| **段標題**（一、二、三…） | **16 pt** 粗體 | 14pt（層次不明） |
| **主旨句**（為聲請…事） | **15 pt** 粗體 | 12pt（看不出是主旨） |
| **內文** | **14 pt**（司法院規定14號以上） | 12pt（不符司法最低標準） |
| **行高** | **固定 25 pt**（最低標準）／**26 pt**（舒適值）| 20pt（不符司法標準） |
| 首行縮排 | **0.8 cm**（標準）／**1.2 cm**（寬鬆排版） | 無縮排 |
| 邊距 | 上下左右皆 **2.5 cm**（司法院規定） | 2.54/3.18（非標準） |
| 目標頁數 | **2 頁以內** | 5 頁（太長，檢察官不會看完） |
| 頁碼 | 頁尾置中 | 無頁碼 |

## 書狀標準結構

目標：**2 頁以內**。填寫說明、送件提醒等附註放在 email 中，不寫入正式書狀。

```
1. 標題（18pt 粗體置中）
2. 案號、股別
3. 聲請人基本資料（姓名／生日／身分證號／電話／地址）
4. 主旨句（15pt 粗體）
5. 主文四段：
   壹、執行命令摘要
   貳、事實詳述（具體、有證據）
   參、法律依據（457 條裁量權＋憲法 23 條比例原則）
   肆、具體請求（明確日期、承諾準時）
6. 「此致」＋機關全銜
7. 附件清單（編號、名稱、用途說明）
8. 聲請人簽章欄、送達代收人欄
9. 民國紀年日期（置中）
```

## 核心程式碼

```python
from docx import Document; from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn; from docx.oxml import OxmlElement

doc = Document(); s = doc.sections[0]
s.page_width = Cm(21.0); s.page_height = Cm(29.7)
# 司法院書狀規則第3條：邊界上下左右2.5cm
for m in ['top','bottom','left','right']:
    setattr(s, f'{m}_margin', Cm(2.5))

def set_font(run, size=14, bold=False):
    # Linux 用全字庫正楷體 TW-Kai，Windows 用標楷體 DFKai-SB
    run.font.name = 'TW-Kai'; run.font.size = Pt(size); run.bold = bold
    rPr = run._element.get_or_add_rPr()
    rf = rPr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts'); rPr.insert(0, rf)
    rf.set(qn('w:eastAsia'), 'TW-Kai')

def P(text, size=14, bold=False, align=WD_ALIGN_PARAGRAPH.LEFT, sa=0, indent=None):
    para = doc.add_paragraph(); para.alignment = align
    pf = para.paragraph_format
    pf.space_after = Pt(sa); pf.line_spacing = Pt(25)  # 司法院規定：固定行高25點以上
    if indent: pf.first_line_indent = Cm(indent)
    run = para.add_run(text); set_font(run, size, bold); return para

def page_break(): doc.add_page_break()

def add_page_number():
    footer = s.footer; footer.is_linked_to_previous = False
    p = footer.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(); set_font(run, size=10)
    for t in ['begin', 'end']:
        fld = OxmlElement('w:fldChar'); fld.set(qn('w:fldCharType'), t)
        run._element.append(fld)
        if t == 'begin':
            instr = OxmlElement('w:instrText')
            instr.set(qn('xml:space'), 'preserve'); instr.text = ' PAGE '
            run._element.append(instr)

add_page_number()
```

完整可執行腳本：`scripts/gen_docx_delay_execution.py`
Usage: `python3 ~/.hermes/skills/legal/legal-docx/scripts/gen_docx_delay_execution.py`

摘要版：

```python
P('暫緩執行聲請書', size=18, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, sa=14)
P('案　　號：115 年度執字第 6265 號', sa=1)
P('股　　別：丑股', sa=6)
P('聲 請 人（即受刑人）：楊瑞忠', sa=1)
P('出生日期：民國 68 年 5 月 14 日', sa=1)
P('國民身分證統一編號：＿＿＿＿＿＿＿＿（請填寫）', sa=1)
P('送達住址：桃園市大園區中正東路一段 739 號', sa=8)
P('為聲請准予暫緩（延緩）執行事：', size=13, bold=True, sa=6)
P('一、執行命令摘要', size=16, bold=True, sa=2)
P('內文……', sa=4, indent=0.8)
P('二、暫緩執行之事由', size=16, bold=True, sa=2)
P('內文……', sa=4, indent=0.8)
P('三、法律依據', size=16, bold=True, sa=2)
P('按刑事訴訟法第 457 條第 1 項規定……', sa=3, indent=0.8)
P('末按憲法第 23 條比例原則……', sa=4, indent=0.8)
P('四、具體請求', size=16, bold=True, sa=2)
P('內文……', sa=4, indent=0.8)
P('五、備位救濟', size=16, bold=True, sa=2)
P('內文……', sa=4, indent=0.8)
P('此　　致', sa=3)
P('臺灣桃園地方檢察署　執行科　公鑒', sa=10)
P('聲　請　人：楊瑞忠　（簽名蓋章）', sa=2)
P('中　華　民　國　115　年　＿＿　月　＿＿　日', align=WD_ALIGN_PARAGRAPH.CENTER, sa=4)
```

## TYPE-S 法律書狀審查

### 法條引用（最大失分項）

- 引用的法條是否確實存在？條號正確？
- 刑訴法 **467 條**是「停止執行」（法定列舉事由）→ 家庭照顧不符，誤引會扣信譽
- 暫緩執行應引刑訴法 **457 條**（檢察官執行指揮裁量權）＋憲法 **23 條**（比例原則）
- 比例原則不可引刑訴法第 2 條（那是職權調查義務）

### 格式

- 書狀第一行必須有正式標題
- 字階層次：標題 18pt > 段標 16pt > 主旨 15pt > 內文 **14pt**（司法最低標準）
- 固定行高 **25pt**（司法最低標準），邊界 **2.5cm** 四面均等
- 目標 2 頁以內——太長檢察官不會看完，第三頁若只有日期則重排
- 填寫說明、送件提醒不寫入正式書狀，另附 email
- 頁碼必要（頁尾置中）

### 證據完整性

- 診斷證明書須 1 個月內 + 載明「需專人照顧」
- 戶籍謄本證明家庭狀況
- 安置機構有具體進度（簽約／訂金）比「正在找」有力

### 實務認知

- 家庭照顧事由的暫緩聲請，實務上**幾乎全數駁回**（案例：高雄地院111聲1291、台南高分院109聲334、桃園地院102聲643）
- 本聲請書的戰術價值：爭取時間、證明非惡意逃避
- 原報到日未獲批文前**仍然有效**，不可不到

## docx → PDF 轉換

```bash
libreoffice --headless --convert-to pdf 書狀.docx
```

驗證 A4 尺寸：
```python
import re
with open('書狀.pdf', 'rb') as f:
    for b in re.findall(rb'/MediaBox\s*\[([^\]]+)\]', f.read()):
        v = [float(x) for x in b.split()]
        w = (v[2]-v[0])*2.54/72; h = (v[3]-v[1])*2.54/72
        print(f'A4: {w:.1f}x{h:.1f} cm  {"✅" if abs(w-21)<.5 and abs(h-29.7)<.5 else "❌"}')
```

## 附件寄送（smtplib）

```python
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase; from email.mime.text import MIMEText
from email import encoders; import smtplib

msg = MIMEMultipart()
msg['From'] = 'hsieh89t@gmail.com'; msg['To'] = 'Lucien127@proton.me'
msg.attach(MIMEText('內文', 'plain', 'utf-8'))
with open('檔案', 'rb') as f:
    part = MIMEBase('application', 'pdf')  # 或 'vnd.openxmlformats-officedocument.wordprocessingml.document'
    part.set_payload(f.read()); encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment', filename='檔名')
    msg.attach(part)
pw = open('/home/hsieh89t_gmail_com/.hermes/scripts/gmail-pass.txt').read().strip()
with smtplib.SMTP('smtp.gmail.com', 587) as s:
    s.starttls(); s.login('hsieh89t@gmail.com', pw); s.send_message(msg)
```

## ⚠️ 已知陷阱

| 陷阱 | 後果 | 正確做法 |
|------|------|----------|
| 用 Noto Serif CJK TC（非楷體） | 不符司法慣例（法院用楷體） | 用全字庫正楷體 TW-Kai（`apt install fonts-cns11643-kai`） |
| 用 DFKai-SB（Linux 無此字體） | 字型 fallback 成醜字 | 裝 TW-Kai，改設 `TW-Kai` |
| 內文 12pt、行高 20pt | 低於司法院規定 14pt/25pt 最低標準，不符格式 | 14pt + 25pt |
| 邊界設 2.54/3.18 | 非司法標準 | 四面皆 2.5cm |
| 第三頁只有日期 | 排版明顯失敗，觀感不佳 | 縮減段落間距，確保 2 頁收尾 |
| 引刑訴法 467 條 | 書記官／檢察官一眼識破，扣分 | 引 457 條裁量權＋憲法 23 條比例原則 |
| 空白欄位未填 | 視為草稿退回 | 送件前逐一對檢查清單 |
| 診斷書未載「需專人照顧」 | 證據力不足 | 回診請醫師補開 |
| 無安置證明 | 說理薄弱 | 至少附機構接洽紀錄 |
| **未做研究先於輸出** | 輸出與 generic AI 無異，喪失智研價值 | 參考 `references/v8-research-protocol.md` |

## 📂 參考文件

- `references/v8-research-protocol.md` — **研究先於輸出 protocol**（v8 新增）：詳細的研究動作清單、合格範本搜尋關鍵字、差異化檢查流程
- `references/v7-specs.md` — **排版最終定版規格**（字階層次、字型安裝、書狀結構、TYPE-S檢查表、歷史版本對照）
- `references/font-hierarchy.md` — 字階層次實戰教訓（從用戶反饋修正的完整記錄）