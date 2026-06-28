---
name: zhiyan-committee
title: zhiyan-committee
description: 多模型合議庭標示器 — 對法律查詢進行跨模型共識/分歧/盲區分析
trigger: 用戶要求多模型比對、合議庭分析、委員會裁決
---

# zhiyan-committee

獨立品質閘門模組，位於 `~/zhiyan-legal/committee/`。

**核心原則：不裁決，只標示。**
- ✅ 共識區：所有模型一致
- ⚠️ 分歧區：模型間意見不同
- ❌ 盲區：所有模型全軍覆沒

## 使用

```bash
cd ~/zhiyan-legal && PYTHONPATH=$PWD python3 -m committee.run --dry-run
PYTHONPATH=$PWD python3 -m committee.run
PYTHONPATH=$PWD python3 -m committee.run --categories nonexistent_article
```

## 模型

agnes-k1 / agnes-k2 / gemini-2.5-flash，全部 $0。

## 測試

```bash
cd ~/zhiyan-legal && PYTHONPATH=$PWD python3 committee/tests/test_core.py
```
