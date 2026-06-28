---
name: gcp-learning
description: GCP 免費證照訓練資源 — awesome list、認證指南、考試經驗
version: 1.1.0
author: Lucian
trigger: "需要 GCP 認證資訊、免費訓練資源、考試準備指南時"
---

# GCP 認證訓練資源（免費為主）

GitHub 與官方平台的 GCP 認證訓練資源整理，以**免費**或低成本資源優先。

---

## 認證路徑總覽（由淺入深）

| 層級 | 認證 | 費用 | 時間 | 建議經驗 |
|------|------|------|------|---------|
| 🟢 Foundational | Cloud Digital Leader | $99 | 1.5h / ~60 題 | 無 |
| 🟢 Foundational | Generative AI Leader | — | — | — |
| 🟡 Associate | **Associate Cloud Engineer (ACE)** | $125 | 2h / ~50 題 | 6 個月 GCP 實作經驗 |
| 🟡 Associate | Associate Data Practitioner | — | — | — |
| 🔴 Professional | Cloud Architect / DevOps / Data Engineer ... 共 10 科 | $200/科 | 2h | 2年+ 經驗 |

> 開發中國家（含台灣）有 **PPP 折扣**，實際費用更低。

---

## 官方免費訓練平台

| 平台 | 說明 | 費用 |
|------|------|------|
| [Google Cloud Skills Boost](https://cloud.google.com/skills) | 300+ 免費課程 + 技能徽章，含 hands-on labs | $29/月（訂閱制），但 300+ 門免費 |
| [Google Skills](https://skills.google/) | 官方免費培訓，含認證準備 | 免費 |
| [Cloud Learning](https://cloud.google.com/learn) | 角色導向學習路徑 | 免費 |
| [Google 數位人才探索計畫](https://growonairtw.withgoogle.com/events/digitaleducation) | 台灣專屬免費課程 | 免費 |
| [TechDevGuide](https://techdevguide.withgoogle.com/paths/cloud/) | Google 官方雲端技術指南 | 免費 |
| [Architecture Center](https://cloud.google.com/architecture) | GCP 架構最佳實踐 | 免費 |
| [Coursera GCP 課程](https://www.coursera.org/professional-certificates/google-cloud-digital-leader-training) | Google Cloud Digital Leader 專業證書 | 7 天免費試用 |
| [Google Cloud $300 免費試用](https://cloud.google.com/free) | 新用戶 $300 抵免額，可用 90 天 | 免費 |

---

## GitHub 精選資源庫

### 🏆 認證大全

| 專案 | ⭐ | 說明 |
|------|------|------|
| [awesome-gcp-certifications](https://github.com/sathishvj/awesome-gcp-certifications) | 4.4k⭐ | **最完整** GCP 認證資源庫，每個認證都有獨立頁面 |
| [google-cloud-4-words](https://github.com/gregsramblings/google-cloud-4-words) | 5k+⭐ | 所有 GCP 產品 4 字描述 |

### 📖 考試筆記

| 專案 | 說明 |
|------|------|
| [GCP ACE Notes](https://github.com/Ernyoke/certified-gcp-cloud-engineer) | Associate Cloud Engineer 完整筆記 |
| [CDL Study Notes](https://github.com/nisamrine/Google-cloud-certifications-notes) | Cloud Digital Leader 學習筆記 |

### 🆓 免費學習資源

| 資源 | 說明 |
|------|------|
| [300+ Free Google Cloud Skills Boost Badges 2026](https://meshworld.in/blog/reference/learning/google-cloud-skills-boost-badges/) | 2026 年 300+ 門免費技能徽章完整目錄 |
| [FreeCodeCamp CDL 課程 (YouTube)](https://www.youtube.com/watch?v=UGRDM86MBIQ) | 免費 Cloud Digital Leader 完整課程 |
| [AwesomeGCP 頻道 (YouTube)](https://www.youtube.com/channel/UCIGDDqu5DzlaaC4XzXj_4-A) | Sathish VJ 的 GCP 頻道 |
| [GCP Sketch Notes](https://thecloudgirl.dev/) | Priyanka Vergadia 的圖解 GCP 筆記 |

### 🛠 實用工具與樣例

| 專案 | 說明 |
|------|------|
| [microservices-demo](https://github.com/GoogleCloudPlatform/microservices-demo) (Online Boutique) | 11 微服務 GKE 示範 |
| [bank-of-anthos](https://github.com/GoogleCloudPlatform/bank-of-anthos/) | Anthos + Cloud SQL 完整範例 |
| [awesome-cloudrun](https://github.com/steren/awesome-cloudrun) | Cloud Run 應用大全 |

---

## 推薦學習路徑（免費方案）

```
① Cloud Digital Leader (CDL)
   費用：$99（有折扣更低）
   準備：FreeCodeCamp YouTube 課程 + Google Skills 官方教材
   推薦：✅ 入門首選

② Associate Cloud Engineer (ACE)
   費用：$125（PPP 折扣後更低）
   準備：Skills Boost 免費 labs + ACE Notes GitHub + 官方 Practice Exam
   推薦：✅ 我們有實際 VM 可練手

③ Professional（擇一）
   費用：$200/科
   準備：先工作經驗，再考慮
   推薦：⏸ 暫緩
```

---

---

## 本地 RAG 搜尋

```bash
# 搜尋 GCP 認證資源（離線，不需連 GitHub）
python3 ~/.hermes/rag/ai_learning/search.py "associate cloud engineer free course"
python3 ~/.hermes/rag/ai_learning/search.py --stats
```

## 相關技能

- **google-cloud-platform** — GCP 操作管理（API 啟用、Secret Manager、Cloud Run、快照等）
- **ai-learning** — AI/Agent/RAG/Prompt 免費認證資源（共用同一個 RAG DB）
