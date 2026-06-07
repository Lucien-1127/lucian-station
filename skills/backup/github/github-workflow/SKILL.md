---
name: github-workflow
description: GitHub 完整工作流程 — 認證、Issue、PR、程式碼審查、倉庫管理、程式碼分析
version: 1.0.0
author: Lucian
license: MIT
platforms: [linux, macos, windows]
---

# GitHub 完整工作流程

合併自：github-auth、github-issues、github-pr-workflow、github-code-review、github-repo-management、codebase-inspection

---

## 快速入門：偵測認證方式

```bash
# 自動偵測用 gh 還是 curl
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  if [ -z "$GITHUB_TOKEN" ]; then
    [ -f ~/.hermes/.env ] && GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | cut -d= -f2)
    [ -z "$GITHUB_TOKEN" ] && [ -f ~/.git-credentials ] && GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials | sed 's|.*:\([^@]*\)@.*|\1|')
  fi
fi

# 取得 owner/repo
REMOTE_URL=$(git remote get-url origin 2>/dev/null)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\\.com[:/]||; s|\\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
```

---

## 1. 認證設定（Authentication）

### HTTPS + Personal Access Token（推薦）

```bash
# 設定 credential helper
git config --global credential.helper store

# 測試認證
git ls-remote https://github.com/<使用者>/<倉庫>.git
```

### SSH 金鑰認證

```bash
# 產生金鑰
ssh-keygen -t ed25519 -C "your@email.com" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub  # 加到 GitHub 設定

# 加入 known_hosts（無頭機器需要）
ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null

# 測試連線
ssh -T git@github.com
```

### gh CLI 登入

```bash
gh auth login                    # 互動登入
echo "TOKEN" | gh auth login --with-token  # Token 方式
gh auth setup-git                # 設定 git 憑證
gh auth status                   # 驗證
```

### 常見問題

| 問題 | 解法 |
|------|------|
| `git push` 要求密碼 | GitHub 已停用密碼認證，改用 PAT 或 SSH |
| Fine-grained PAT 403 | Token 缺少 repo 寫入權限，到設定頁面啟用 Contents: Read and write |
| `gh repo create` 403 | Fine-grained PAT 缺少「Create repositories」帳戶權限 |
| SSH Connection refused | 改用 SSH over HTTPS：設定 `~/.ssh/config` 用 Port 443 |

---

## 2. Issue 管理

### 檢視 Issue

```bash
# gh
gh issue list                                        # 列出所有 Issue
gh issue list --state open --label "bug"             # 依標籤篩選
gh issue list --assignee @me                         # 指派給我的
gh issue view 42                                     # 檢視單一 Issue

# curl
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/issues?state=open&per_page=20"
```

### 建立 Issue

```bash
gh issue create --title "標題" --body "說明" --label "bug" --assignee "username"
```

### 管理 Issue

```bash
gh issue edit 42 --add-label "priority:high"         # 加標籤
gh issue edit 42 --add-assignee @me                  # 指派
gh issue close 42                                    # 關閉
gh issue reopen 42                                   # 重新開啟
gh issue comment 42 --body "已調查，根因在 auth middleware"  # 留言
```

### 分類工作流程

1. `gh issue list --label "needs-triage"` — 列出未分類 Issue
2. 閱讀後加上適當標籤與優先級
3. 指派負責人
4. 留言分類結論

---

## 3. PR 工作流程

### 建立分支

```bash
git fetch origin
git checkout main && git pull origin main
git checkout -b feat/功能名稱        # feat/fix/refactor/docs/ci
```

### 提交

```bash
git add <檔案>
git commit -m "feat(scope): 簡短說明

詳細說明（選填）"
```

### 推送與建立 PR

```bash
git push -u origin HEAD

# gh
gh pr create --title "feat: ..." --body "摘要" --label "enhancement"

# curl
BRANCH=$(git branch --show-current)
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d "{\"title\":\"feat: ...\",\"head\":\"$BRANCH\",\"base\":\"main\"}"
```

### 監控 CI

```bash
gh pr checks                    # 檢查狀態
gh pr checks --watch            # 持續監控（每 10 秒）
gh run list --branch $(git branch --show-current) --limit 5
```

### CI 自動修復流程

```bash
# 1. 查看失敗記錄
gh run view <RUN_ID> --log-failed

# 2. 修復程式碼並推送
git add . && git commit -m "fix: 修復 CI 失敗" && git push

# 3. 重新檢查
gh pr checks --watch
```

### 合併

```bash
gh pr merge --squash --delete-branch   # Squash 合併 + 刪除分支
gh pr merge --auto --squash            # CI 通過後自動合併
```

---

## 4. 程式碼審查

### 審查本地變更（推送前）

```bash
git diff main...HEAD --stat              # 查看變更範圍
git diff main...HEAD                     # 完整 diff
git diff main...HEAD -- src/auth.py      # 特定檔案
git diff main...HEAD --name-only         # 只列檔名

# 常見問題掃描
git diff main...HEAD | grep -n "TODO\|FIXME\|HACK\|debugger"
git diff main...HEAD | grep -in "password\|secret\|api_key"
```

### 審查 GitHub 上的 PR

```bash
# 用 gh
gh pr view 123
gh pr diff 123
gh pr diff 123 --name-only

# 用 git 取到本機
git fetch origin pull/123/head:pr-123
git checkout pr-123
git diff main...pr-123
```

### 送出審查意見

```bash
# gh
gh pr review 123 --approve --body "LGTM!"
gh pr review 123 --request-changes --body "請修正以下問題"
gh pr comment 123 --body "整體不錯，有些小建議"

# curl（原子審查，含多個行內留言）
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/reviews \
  -d '{
    "event": "COMMENT",
    "body": "Hermes Agent 程式碼審查",
    "comments": [
      {"path": "src/auth.py", "line": 45, "body": "建議使用參數化查詢防止 SQL injection"}
    ]
  }'
```

### 審查檢查清單

- ✅ 正確性：邊界情況、錯誤路徑是否處理？
- ✅ 安全性：有無硬編碼密鑰、SQL injection、XSS？
- ✅ 程式碼品質：命名清晰、單一職責、無重複邏輯
- ✅ 測試：新功能有測試嗎？涵蓋快樂路徑與錯誤情況？
- ✅ 效能：有無 N+1 查詢、不必要的迴圈？

---

## 5. 倉庫管理

### 複製與建立

```bash
git clone https://github.com/owner/repo.git
gh repo clone owner/repo
gh repo create 新專案 --public --clone          # 建立
gh repo create 新專案 --source . --public --push # 從本地推送
```

### Fork 與同步

```bash
gh repo fork owner/repo --clone
git remote add upstream https://github.com/owner/repo.git
git fetch upstream && git merge upstream/main && git push origin main
```

### 倉庫設定

```bash
gh repo edit --description "新描述" --visibility public
gh repo edit --default-branch main
gh repo edit --add-topic "machine-learning,python"
```

### 版本發佈

```bash
gh release create v1.0.0 --title "v1.0.0" --generate-notes
gh release list
gh release download v1.0.0 --dir ./downloads
```

### Actions 管理

```bash
gh workflow list                                  # 列出 workflows
gh run list --limit 10                            # 最近執行
gh run view <RUN_ID> --log-failed                 # 失敗記錄
gh run rerun <RUN_ID> --failed                    # 重跑失敗 job
gh workflow run ci.yml --ref main                 # 手動觸發
```

### Secrets 管理

```bash
gh secret set API_KEY --body "your-secret-value"
gh secret list
gh secret delete API_KEY
```

### 分支保護

```bash
curl -s -X PUT -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/branches/main/protection \
  -d '{
    "required_status_checks": {"strict": true, "contexts": ["ci/test"]},
    "required_pull_request_reviews": {"required_approving_review_count": 1}
  }'
```

---

## 6. 程式碼庫分析（pygount）

### 安裝

```bash
pip install pygount
```

### 使用

```bash
cd /path/to/repo

# 語言統計摘要
pygount --format=summary --folders-to-skip=".git,node_modules,venv,__pycache__,dist,build" .

# 只看特定語言
pygount --suffix=py --format=summary .

# JSON 輸出（程式處理用）
pygount --format=json --folders-to-skip=".git,node_modules" .
```

### 注意事項

- 務必使用 `--folders-to-skip` 排除依賴目錄，否則可能耗時很久
- Markdown 全部被歸類為評論（非程式碼），這是正常行為
- 大型 monorepo 建議用 `--suffix` 限定語言範圍

---

## 快速參考

| 操作 | gh 指令 | curl endpoint |
|------|---------|---------------|
| 列出 Issue | `gh issue list` | `GET /issues` |
| 建立 Issue | `gh issue create` | `POST /issues` |
| 建立 PR | `gh pr create` | `POST /pulls` |
| 審查 PR | `gh pr review N` | `POST /pulls/N/reviews` |
| 合併 PR | `gh pr merge --squash` | `PUT /pulls/N/merge` |
| 建立倉庫 | `gh repo create` | `POST /user/repos` |
| 發佈 release | `gh release create` | `POST /releases` |
| 設定 secret | `gh secret set` | `PUT /actions/secrets/KEY` |
| 列出 workflow | `gh workflow list` | `GET /actions/workflows` |