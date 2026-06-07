#!/usr/bin/env bash
# Hermes 技能雙向同步腳本
# 同步 ~/.hermes/skills/ <-> ~/lucian-station/skills/backup/

set -e

REPO_DIR="$HOME/lucian-station"
BACKUP_DIR="$REPO_DIR/skills/backup"
LOCAL_DIR="$HOME/.hermes/skills"
LOG_FILE="$REPO_DIR/sync.log"

echo "$(date '+%Y-%m-%d %H:%M:%S') === Hermes 技能同步開始 ===" >> "$LOG_FILE"

cd "$REPO_DIR"

# 1) Pull 最新
git pull --ff-only origin main 2>> "$LOG_FILE" || echo "git pull 失敗（可能無網路或首次），繼續同步" >> "$LOG_FILE"

CHANGED=0

# 2) 同步所有本地分類到備份庫
for cat_dir in "$LOCAL_DIR"/*/; do
    cat_name=$(basename "$cat_dir")
    mkdir -p "$BACKUP_DIR/$cat_name"

    # 2a) 處理分類內直接放的 SKILL.md（flat 結構）
    for f in "$cat_dir"SKILL.md "$cat_dir"DESCRIPTION.md "$cat_dir"*.txt "$cat_dir"*.json "$cat_dir"*.yaml; do
        [ ! -f "$f" ] && continue
        fname=$(basename "$f")
        if [ ! -f "$BACKUP_DIR/$cat_name/$fname" ] || ! diff -q "$f" "$BACKUP_DIR/$cat_name/$fname" >/dev/null 2>&1; then
            cp "$f" "$BACKUP_DIR/$cat_name/$fname"
            echo "  [備份] $cat_name/$fname" >> "$LOG_FILE"
            CHANGED=1
        fi
    done

    # 2b) 處理子目錄內的 skill（標準結構）
    for skill_dir in "$cat_dir"*/; do
        skill_name=$(basename "$skill_dir")
        [ "$skill_name" = "*" ] && continue
        mkdir -p "$BACKUP_DIR/$cat_name/$skill_name"
        for f in "$skill_dir"*; do
            [ ! -f "$f" ] && continue
            fname=$(basename "$f")
            if [ ! -f "$BACKUP_DIR/$cat_name/$skill_name/$fname" ] || ! diff -q "$f" "$BACKUP_DIR/$cat_name/$skill_name/$fname" >/dev/null 2>&1; then
                cp "$f" "$BACKUP_DIR/$cat_name/$skill_name/$fname"
                echo "  [備份] $cat_name/$skill_name/$fname" >> "$LOG_FILE"
                CHANGED=1
            fi
        done
    done
done

# 3) 備份庫 → 本機（補本機沒有的技能）
for cat_dir in "$BACKUP_DIR"/*/; do
    cat_name=$(basename "$cat_dir")
    mkdir -p "$LOCAL_DIR/$cat_name"

    # 3a) flat 檔案
    for f in "$cat_dir"SKILL.md "$cat_dir"DESCRIPTION.md "$cat_dir"*.txt "$cat_dir"*.json; do
        [ ! -f "$f" ] && continue
        fname=$(basename "$f")
        if [ ! -f "$LOCAL_DIR/$cat_name/$fname" ]; then
            cp "$f" "$LOCAL_DIR/$cat_name/$fname"
            echo "  [新增] $cat_name/$fname" >> "$LOG_FILE"
            CHANGED=1
        fi
    done

    # 3b) 子目錄內技能
    for skill_dir in "$cat_dir"*/; do
        skill_name=$(basename "$skill_dir")
        [ ! -d "$skill_dir" ] && continue
        [ "$skill_name" = "*" ] && continue
        mkdir -p "$LOCAL_DIR/$cat_name/$skill_name"
        for f in "$skill_dir"*; do
            [ ! -f "$f" ] && continue
            fname=$(basename "$f")
            if [ ! -f "$LOCAL_DIR/$cat_name/$skill_name/$fname" ]; then
                cp "$f" "$LOCAL_DIR/$cat_name/$skill_name/$fname"
                echo "  [新增] $cat_name/$skill_name/$fname" >> "$LOG_FILE"
                CHANGED=1
            fi
        done
    done
done

# 4) 更新 inventory
ls -1 "$BACKUP_DIR" 2>/dev/null | sort > "$REPO_DIR/skills/inventory.txt"

# 5) Commit + Push
if [ "$CHANGED" -eq 1 ] || [ -n "$(git status --porcelain)" ]; then
    git add -A 2>> "$LOG_FILE"
    git commit -m "auto-sync $(date '+%Y-%m-%d %H:%M')" 2>> "$LOG_FILE"
    git push origin main 2>> "$LOG_FILE" && echo "  => 已推送上 GitHub ✓" >> "$LOG_FILE" || echo "  => push 失敗（可能無網路）" >> "$LOG_FILE"
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') === 同步完成 ===" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
