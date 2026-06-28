# RAP (Researcher Access Program) 申請流程

## 申請時程
- 每季一次，2026年下一輪：**9月**
- 評估時間：提交後約 2–3 個月

## 申請前準備（成功率最大化）

### 1. OSF.io DOI（最高優先）
1. 註冊 OSF.io 帳號（建議用 ORCiD 串接，免額外密碼）
2. 建立專案 → 上傳 `RESEARCH.md`
3. 專案設定 → 產生 DOI
4. 在 RAP 申請表的「Past Research」欄位填入 DOI 連結

### 2. arXiv 預印本
1. 將研究提案整理為 arXiv cs.CL 格式
2. 提交前需有已認證作者 endorsement
3. 無機構 affiliation 時：
   - 可請有 arXiv 帳號的合作者代提交
   - 或在 OSF 取得 DOI 後直接引用 OSF 連結（不必強求 arXiv）

### 3. RESEARCH.md 內容標準（已符合）
- 8 個章節完整：Title → Background → System Design → Method → Metrics → Budget → Sharing → Ethics
- 4 conditions ablation study（full / no-citation / no-gate / baseline）
- 200 labelled queries × 3 replicates
- 20% human evaluation sample
- Budget ≤ $1,000
- MIT + CC-BY + arXiv publication plan

## 成功率因子
| 因子 | 權重 | 現狀 |
|------|:----:|------|
| 研究設計嚴謹度 | 高 | 🟢 強（4 conditions, 200 queries, 3 reps） |
| 社會影響力 | 高 | 🟢 強（法律可及性 + 非英語語境） |
| 開放科學 | 中 | 🟢 強（MIT + CC-BY + 公開 repo） |
| 機構隸屬 | 高 | 🔴 弱（Independent Researcher） |
| 過去論文 | 中 | 🔴 弱（無 peer-reviewed） |
| 文件完整性 | 中 | 🟢 強（RESEARCH.md + 85+ spec files） |

## OSF 上傳操作
```bash
# 1. 登入後點 「Create Project」
# 2. Project Name: "A Reproducible Study of Citation-Grounding..."
# 3. 上傳 RESEARCH.md
# 4. 可附加：docs/ 目錄壓縮檔（完整規格文件）
# 5. 設定 License: MIT
# 6. 產生 DOI（在 Project Settings 中）
```

## 注意陷阱
- OSF 瀏覽器操作可能觸發 bot 偵測 → 改用 ORCiD 註冊免填密碼
- arXiv 需要 endorsement → 若無法取得，OSF DOI 仍是有效的學術引用
- RAP 申請表的 Fine-tuning 欄位：不確定是否勾選時建議取消
