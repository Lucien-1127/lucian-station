# GitHub Token 權限速查

## Classic Token vs Fine-grained PAT

| 操作 | Classic (`repo` scope) | Fine-grained PAT |
|------|----------------------|-----------------|
| git push | ✅ | Contents: Read & Write |
| gh issue create/edit | ✅ | Issues: Read & Write |
| gh pr create/merge | ✅ | Pull requests: Read & Write |
| gh repo create | ✅ | Account: Create repositories |
| gh repo edit --add-topic | ✅ (public_repo) | **Administration: Read & Write** |
| gh repo edit --description | ✅ (public_repo) | **Administration: Read & Write** |
| gh secret set | ✅ | Secrets: Read & Write |
| gh workflow run | ✅ | Actions: Read & Write |
| gh release create | ✅ | Contents: Read & Write |

## 關鍵陷阱

- **`gh repo view` 可以但 `gh repo edit --add-topic` 403** — topics API 歸 Administration 管，不是 Contents
- Fine-grained PAT 預設不開 Administration → 需要手動到 PAT 設定頁啟用
- GitHub Badge 是零權限的「標籤」替代方案：`[![Label](https://img.shields.io/badge/標籤名-color)](url)` 直接放 README

## 實用備案：推送失敗時的 PR 網址

當 `gh pr create` 因權限不足（403）失敗時，git push 輸出會自動顯示 PR 網址：

```
remote: Create a pull request for 'fix/xxx' on GitHub by visiting:
remote:      https://github.com/owner/repo/pull/new/fix/xxx
```

直接提供該網址給用戶即可跳過 CLI PR 建立流程。這不需要任何 API 權限。

```markdown
[![MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![法律研究](https://img.shields.io/badge/法律研究-台灣-blue)](#)
[![OpenAI](https://img.shields.io/badge/OpenAI-LLM-412991)](#)
```
