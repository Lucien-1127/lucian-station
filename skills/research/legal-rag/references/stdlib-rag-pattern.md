# Stdlib RAG Pattern — Zero-Dependency Approach

When package installation fails or is infeasible (PEP 668, no-GPU, no root), SQLite FTS5 + Python stdlib provides a production-grade alternative to chromadb/sentence-transformers for **keyword-dense, structured text** — exactly the profile of legal, regulatory, technical, and domain-specific corpora.

## Decision Matrix

| Factor | FTS5 (stdlib) | Embedding RAG (chromadb + sbert) |
|--------|---------------|----------------------------------|
| Dependencies | Zero | 200+ MB (torch, transformers, etc.) |
| Install risk | None | High (CVE advisories, PEP 668, disk space) |
| Query type | Keyword/phrase | Semantic / conceptual |
| Chinese support | `unicode61` tokenizer | Better (subword embeddings) |
| Cold start | Instant | ~30s model download |
| DB size | ~40 MB for 47k docs | ~100-500 MB for same corpus |
| Relevance ranking | TF/IDF-like (FTS5 rank) | Cosine similarity |
| Cross-lingual | No | Yes (multilingual models) |
| Best for | Law, code, configs, enums | Prose, conversation, open-ended QA |

## When to Use Stdlib RAG (Signals)

1. **`pip install` keeps failing** → CVE blocks, PEP 668, timeout on torch download
2. **Corpus is keyword-dense** → legal citations, article numbers, technical terms are naturally discriminative
3. **Low latency required** → no model loading, no GPU wait
4. **Offline / air-gapped** → zero network, zero external downloads
5. **User values simplicity** → one SQLite file, one Python script, no config

## Architecture Recap

```
Raw data (TSV/CSV/JSON)
    ↓ Python csv/json parse
SQLite + FTS5 virtual table
    ↓ 3-tier query: FTS5 → LIKE → tag index
Result with ranked relevance
```

## The 3-Tier Query Strategy

1. **FTS5 MATCH** — best recall for multi-term AND queries. Fastest path.
2. **LIKE %query%** — fallback when FTS5 syntax can't parse user input (mixed chars, special tokens).
3. **Tag index** — exact-match filter via separate `tag_index` table for domain-specific keywords.

## Scoring Heuristic

When FTS5 rank alone isn't sufficient, compute a simple relevance score per result row:

```python
score = (hits_in_summary × 3.0) +
        (hits_in_content × 2.0) +
        (hits_in_tags × 1.5) +
        (hits_in_issues × 1.0)
```

This works because summary is the human-curated "answer," content is the raw source, and tags are the classification layer.

## Sync Pattern

Always offer **both** auto (cronjob) and manual (script) sync paths. Users expect the safety of a manual override even after automation is set up.

```bash
# Manual (emergency / immediate)
bash ~/.hermes/scripts/sync_rag.sh

# Auto (set-and-forget)
cronjob 0 3 * * * "sync script"  # daily 3 AM
```
