# Microsoft.PowerShell_profile.ps1
# Place at: $PROFILE (C:\Users\{name}\Documents\PowerShell\Microsoft.PowerShell_profile.ps1)

# ================== AI Agent Shortcuts ==================
# WSL absolute paths (NEVER use ~ in PowerShell WSL commands)
$WSL_HERMES = "/home/ysga1/.local/bin/hermes"

# chat = Hermes Agent dialogue (full tools: file access, terminal, search)
function chat {
    Write-Host "🗣️  Hermes Agent + Gemini 2.5 Flash" -ForegroundColor Green
    wsl -e $WSL_HERMES chat
}

# ai = interactive menu (no need to remember commands)
function ai {
    Clear-Host
    Write-Host ""
    Write-Host "  ════════════════════════════════════════" -ForegroundColor Yellow
    Write-Host "  🤖  AI 代理啟動中心" -ForegroundColor Yellow
    Write-Host "  ════════════════════════════════════════" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  ┌─────┬──────────────────────────────┐" -ForegroundColor DarkGray
    Write-Host "  │  1  │  🗣️  開始對話 (chat)          │" -ForegroundColor White
    Write-Host "  │  2  │  📊  查看狀態                │" -ForegroundColor White  
    Write-Host "  │  3  │  🌐  開啟 Dashboard         │" -ForegroundColor White
    Write-Host "  │  4  │  📋  查看當前設定            │" -ForegroundColor White
    Write-Host "  │  5  │  🏥  健康檢查                │" -ForegroundColor White
    Write-Host "  │  0  │  🚪  離開                    │" -ForegroundColor White
    Write-Host "  └─────┴──────────────────────────────┘" -ForegroundColor DarkGray
    Write-Host ""
    $choice = Read-Host "  請選擇 (0-5)"
    switch ($choice) {
        "1" { Write-Host "`n🚀 啟動對話中..." -ForegroundColor Green; wsl -e $WSL_HERMES chat }
        "2" { wsl -e $WSL_HERMES status; Write-Host "`n按 Enter 返回..." -ForegroundColor DarkGray; Read-Host; ai }
        "3" { Start-Process "http://localhost:8000"; Write-Host "✅ Dashboard 已開啟" -ForegroundColor Green; Start-Sleep 1; ai }
        "4" { 
            Write-Host "📋 設定：" -ForegroundColor Cyan
            Write-Host "  $(wsl -e grep 'default:' /home/ysga1/.hermes/config.yaml | Select-Object -First 1)"
            Write-Host "  $(wsl -e grep 'provider:' /home/ysga1/.hermes/config.yaml | Select-Object -First 1)"
            Write-Host "`n按 Enter 返回..." -ForegroundColor DarkGray; Read-Host; ai 
        }
        "5" { wsl -e $WSL_HERMES doctor; Write-Host "`n按 Enter 返回..." -ForegroundColor DarkGray; Read-Host; ai }
        "0" { Write-Host "再見！" -ForegroundColor Yellow; return }
        default { Write-Host "❌ 無效" -ForegroundColor Red; Start-Sleep 1; ai }
    }
}

# Hermes generic (passes through any args)
function hermes { wsl -e $WSL_HERMES $args }
function hermes-dash { Start-Process "http://localhost:8000" }
