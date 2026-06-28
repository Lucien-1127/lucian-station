---
name: github-workflow
description: GitHub 完整工作流程 — 認證、Issue、PR、程式碼審查、倉庫管理、程式碼分析
version: 1.2.0
author: Lucian
license: MIT
platforms: [linux, macos, windows]
---

# GitHub 完整工作流程

合併自：github-auth、github-issues、github-pr-workflow、github-code-review、github-repo-management、codebase-inspection

快速參考：`github-token-permissions.md`（PAT 權限對照表）、`zhiyan-legal-codebase.md`（老闆的 zhiyan-legal 專案架構）、`github-branding.md`（GitHub Pages / 雙語 README / Wiki / Profile / 模板）

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

### 🔑 頭戴伺服器裝置認證流程（gh auth login --web）

在無瀏覽器的伺服器上，`gh auth login --web` 使用 GitHub 裝置流程認證。流程如下：

```bash
# 1. 啟動 gh auth login（前景執行，給較長 timeout）
# 輸出會顯示裝置代碼和 URL
unset GITHUB_TOKEN   # ← 重要！否則 gh 會吃錯誤的 token 值
gh auth login --web -s "repo,workflow"

# 輸出範例：
# ! First copy your one-time code: DAC5-1DD4
# Open this URL to continue in your web browser: https://github.com/login/device

# 2. 把 URL + 代碼給使用者（訊息發到對話平台）
# 3. 使用者用手機/電腦打開網址、輸入代碼、授權
# 4. gh 會持續 polling GitHub API，
#    使用者授權後自動儲存 token 到 ~/.config/gh/hosts.yml
```

**陷阱：**
- ⚠️ `GITHUB_TOKEN` 環境變數有值時，`gh` 優先吃 token 而非走裝置流程，會報錯：`The value of the GITHUB_TOKEN environment variable is being used for authentication.`  → 務必先 `unset GITHUB_TOKEN`
- ⚠️ 背景啟動（`background=true`）的 process 可能因 stdio 緩衝無法輸出裝置碼。正確做法：寫 script 將輸出導到檔案，再用 `tee` 同時顯示與存檔
- ⚠️ 裝置碼有 15 分鐘有效期，逾時需重新產生
- ⚠️ 認證後 `gh auth status` 若仍顯示未登入，可能是上一次的 `gh auth login` 程序在 timeout 後已遺失 token，需重新啟動一次並正常等待使用者完成認證
- ⚠️ 認證成功後 `gh` 將 token 以純文字存於 `~/.config/gh/hosts.yml`，這是正常行爲

**完整可重複流程：**
```bash
# 1. 寫入 script 捕捉輸出
cat > /tmp/gh_login.sh <<'SCRIPT'
#!/bin/bash
unset GITHUB_TOKEN
gh auth login --web -s "repo,workflow" 2>&1 | tee /tmp/gh_auth_output.txt
echo "EXIT_CODE=$?" >> /tmp/gh_auth_output.txt
SCRIPT
chmod +x /tmp/gh_login.sh

# 2. 背景執行（notify_on_complete=true 才能得知完成）
bash /tmp/gh_login.sh

# 3. 等幾秒後讀取 /tmp/gh_auth_output.txt 取得裝置碼
# 4. 把 URL + 代碼發給使用者
# 5. 使用者認證後 script 自動完成，token 存好
# 6. 驗證：gh auth status
```

**HTTPS push 失敗 → SSH 切換（重要）：**
`gh auth` 經裝置流程取得的 token 僅供 `gh` CLI 使用。`git push` 使用 HTTPS 時，若未另設定 credential helper，會跳出 `could not read Username` 錯誤。解決方式：
```bash
git remote set-url origin git@github.com:<owner>/<repo>.git
```
然後用 SSH 金鑰 push。`gh` 管 API、SSH 管 git，各司其職。
- ⚠️ 認證後 `gh auth status` 若仍顯示未登入，可能是上一次的 `gh auth login` 程序在 timeout 後已遺失 token，需重新啟動一次並正常等待使用者完成認證

### 🔑 認證策略：SSH 優先

**SSH 金鑰認證比 PAT 更可靠。** Fine-grained PAT（`github_pat_*`）經常遇到權限問題：
- 需要逐倉庫設定存取權
- 需要另外啟用 Account permissions（如 Create repositories）
- git push 時可能 403 即使 gh auth status 顯示 ✅

**建議流程：**
1. 優先嘗試 SSH 連線（`ssh -T git@github.com`）
2. 若無 SSH 金鑰，產生一組 `ssh-keygen -t ed25519` 並加到 GitHub 設定
3. 若環境不支援 SSH 再退而求其次用 PAT

### 常見問題

| 問題 | 解法 |
|------|------|
| `git push` 要求密碼 | GitHub 已停用密碼認證，改用 PAT 或 SSH |
| Fine-grained PAT 403（push） | Token 缺少 repo 寫入權限，到設定頁面啟用 Contents: Read and write |
| Fine-grained PAT 403（topics/labels） | 修改 repository topics 需要 **Administration: Read and Write** 權限（不只是 Contents），若無法更新 PAT，改用 README badge 替代標籤功能 |
| `gh pr create` 403（createPullRequest） | Fine-grained PAT 缺少 **Pull requests: Read & Write** 權限；備案：直接給用戶 push 輸出顯示的 PR 網址 |
| `gh repo create` 403 | Fine-grained PAT 缺少「Create repositories」帳戶權限 |
| `gh repo edit --add-topic` 403 但 `gh repo view` 正常 | topics API（PUT /repos/:owner/:repo/topics）需 Administration 權限，較新版的 gh 要求更高；備案：用 markdown badge 寫在 README 頂端 |
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

## 💡 推送策略判定（先判斷再行動）

代理執行修復前先判定情境，避免推錯分支：

| 情境 | 策略 | 原因 |
|------|------|------|
| 個人專案（owner repo），老闆說「修」 | **直接 push main** — `git checkout main && 改 && git push origin main` | 老闆不想走 PR 流程，feature branch 沒意義 |
| 協作專案 / fork / 多人 repo | **feature branch → PR** 標準流程 | 需要 code review / CI |
| gh CLI 403（createPullRequest） | **放棄開 PR，直接 push main** 並告知用戶 push 結果 | PAT 權限不足時，不要卡住 |

⚠️ **陷阱**：習慣性開 feature branch + PR 會讓老闆多等一輪。老闆的個人專案（zhiyan-legal 等）直接改 main 即可。

### 程式碼審查 → 修正工作流程（老闆的偏好）

收到 🔴🟡🟢 結構化審查報告或詳細問題列表時：

```bash
# Step 1: 驗證每個 claim — 不要直接照修！
# 逐一讀取被點名的原始碼，確認問題真實存在
# 審查報告可能有誤報（docstring 矛盾、邊界邏輯不完整），先驗再修

# Step 2: 回報驗證結果
# 逐項標註 ✅ 確認 / ❌ 誤報，讓老闆知道哪些會修

# Step 3: 開 branch 一次修完
git checkout -b fix/short-description

# Step 4: 測試
source .venv/bin/activate 2>/dev/null || python3 -m venv .venv && source .venv/bin/activate
pip install pytest -q
PYTHONPATH=src python -m pytest tests/ -v

# Step 5: 合併到 main
git checkout main && git merge --no-ff fix/short-description -m "merge: 摘要"
git push origin main

# Step 6: 通知老闆「已推送，SHA: xxx，可驗證」

# Step 7: 更新 CHANGELOG.md（若有封閉性修復或新功能）
# 在 CHANGELOG.md 的 [Unreleased] 區塊記錄變更
# 結構化描述：🔴 Bug Fixes / 🟡 Improvements / 🟢 Features / 🧪 Testing
# 附 commit SHA 索引表

⚠️ **陷阱**：不要跳過驗證直接照單全收修 — 審查報告可能有誤報（如邊界邏輯不完整、斷言條件錯誤），先讀原始碼確認。

⚠️ **陷阱**：習慣性開 feature branch + PR 會讓老闆多等一輪。老闆的個人專案（zhiyan-legal 等）直接 merge 到 main 即可。只在協作 repo 才走標準 PR 流程。

⚠️ **陷阱 — 文件同步遺漏**：當更新 provider 範例模型、URL 或任何跨檔案參考時，務必檢查專案中所有引用該資訊的位置。zhiyan-legal 中 provider 資料散佈在 7 個位置（.env.example、README × 2 表 × 2 code block、setup.sh、runner.py docstring），漏一個就造成不一致。詳見 `references/zhiyan-legal-codebase.md` 的檢查清單。

### 處理 🔴🟡🟢 層級審查報告

老闆經常提供結構化的程式碼審查報告，格式固定：

```
## 🔴 高風險錯誤（須立即修正）
### N. filename — 問題描述

## 🟡 中風險問題（建議修正）
...

## 🟢 確認無誤項目
...

## 📋 修正優先序
| 優先 | 檔案 | 問題 | 影響 |

**信心標記：🟢 XX%**
```

應對流程：
1. **先驗證** — 讀取原始碼逐一確認每個 claim，不是所有 claim 都正確
2. **分類** — 哪些是真的 bug、哪些是設計取捨、哪些是誤報
3. **回報** — 簡短告知老闆驗證結果
4. **一次修完** — 同類型問題開一個 branch 全部處理
5. **跑測試** — 確認沒有 regression
6. **推送** — commit message 用結構化摘要對應 🔴🟡🟢 層級

## 3. PR 工作流程（標準協作模式）

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

### 推送防護（Secret Scanning）

當 GitHub Push Protection 阻擋推送時：

```
remote: - GITHUB PUSH PROTECTION
remote:     - Push cannot contain secrets
remote:       —— OpenRouter API Key ——————————————————
remote:        path: vm/hermes-config.txt:6
```

**處理步驟：**

1. **先置換密鑰為佔位符** — 用 `sed` 或 `patch` 將實際密鑰改為 `<REDACTED>`
2. **重寫 commit** — `git add . && git commit --amend -m "..."` 取代舊的 commit
3. **強制推送** — `git push --force-with-lease` 或 `git push --force`

**預防（推配置備份前必做）：**
```bash
# 掃描檔案中是否有真實密鑰
grep -rn "sk-or-\|ghp_\|github_pat\|api_key: [a-zA-Z0-9_]\{10,\}" vm/ skills/ --include="*.txt" --include="*.md"
# 或用 sed 全域遮罩
sed -i 's|api_key: sk-or-[^ ]*|api_key: <REDACTED>|g' vm/hermes-config.txt
```

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