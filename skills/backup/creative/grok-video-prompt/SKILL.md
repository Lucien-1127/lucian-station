---
name: grok-video-prompt
description: Grok Imagine (xAI) 影片提示詞工程 — 15秒抖音/TikTok短片、角色一致性、多鏡頭編排、常見問題排錯
version: 2.1.0
author: Hermes Agent
tags: [grok, video, prompt-engineering, tiktok, short-video, ai-video]
---

# Grok Imagine 影片提示詞工程

## 適用時機

- 使用者要求用 Grok Imagine / xAI Grok 生成影片
- 使用者想優化 Grok 影片品質（頭歪、臉變形、動作奇怪）
- 使用者要製作抖音/TikTok/Reels 短影音內容
- 使用者需要角色一致的連續影片

## 核心公式：6 元件

```
Prompt = [Subject] + [Action] + [Camera] + [Lighting] + [Environment] + [Audio]
```

每個元件都要寫，缺一個就少一分品質。

## Grok 與其他平台的關鍵差異

| 特性 | 你該怎麼做 |
|------|-----------|
| ❌ **不支援 negative prompt** | 不要寫「不要歪頭」→ 寫「頭部自然直立」 |
| ✅ **800-1200 字最優** | 越詳細越好，前 20 字決定調性 |
| ✅ **JSON 結構化支援** | 複雜場景用 JSON 比純文字精準 |
| ✅ **原生音訊** | 用 `[Audio: ...]` 包音效指令辨識度最高 |
| ✅ **Shot Switch 多鏡頭** | 同一個 prompt 內用 `Shot Switch.` 做剪接 |
| ⚠️ **I2V 不支援 spicy mode** | 圖片轉影片只能用 normal mode |

## 角色一致性（Character DNA）

每個 prompt 開頭放這段定義塊，確保角色跨鏡頭不變：

```
[Character DNA:
- Name: 呱呱
- Hair: Short white, neon blue streak across front bangs
- Eyes: Deep dark blue
- Build: Teenage boy, slim athletic
- Clothing: White fitted tee, indigo denim shorts with white stripe hem,
  silver waist chain with pearl accents, white low-top sneakers]
```

進階作法：先用 Gemini 3 Pro 生成角色定裝照，再用 I2V 模式以該圖片為錨點生成影片。

## 多鏡頭編排（抖音 15 秒結構）

### 經典 4 鏡頭節奏

| 時間 | 鏡頭 | 內容 | 運鏡 |
|------|------|------|------|
| 0-3s | 開場吸睛 | 角色正面微笑，頭部自然直立 | dolly in, shallow DOF |
| 3-7s | 卡點爆發 | 重拍瞬間 sharp camera jolt + 鎖舞動作 | handheld, crash zoom |
| 7-11s | 手指舞高潮 | 上半身特寫，精準 finger-tutting | medium close-up, static |
| 11-15s | 定格收尾 | 手指槍指鏡頭 + 俏皮 wink | pull back to medium |

### 常用鏡頭術語（非用不可）

| 你寫 | 高手寫法 |
|------|---------|
| 鏡頭移動 | `slow dolly in` / `orbiting camera` |
| 快速 | `crash zoom` / `whip pan` |
| 主觀 | `FPV drone shot` |
| 專業感 | `Arri Alexa` / `anamorphic lens` / `35mm film` |
| 啟用移動 | `unfixed lens`（沒寫=靜態） |
| 多鏡頭 | `Shot Switch.` 做剪接 |

## 進階工作流技術

### 1. 原生影片擴展（Video Extension）

SuperGrok 訂閱可用。在 Web UI 生成第一段後按「Extend」，描述下一段動作：

```
1. T2V: "Samurai walking through rain in neon alley" (10s)
2. Extend: "He stops, draws katana, turns to face camera" (8s)
3. Extend: "Lightning flash reveals enemy behind him" (6s)
Total: 24 seconds
```

優點：不像 Last Frame Method 會累積畫質損失。

### 2. HD Upscaling（SuperGrok 限定）

先 720p 快速迭代 → 選最終版 → 按 HD upscale → 下載 1080p。

### 3. SFW Sandwich（防止帳號被標記）

把可能觸發審查的 prompt 夾在安全 prompt 之間：

```
1. "Blue sky with fluffy clouds" (Safe)
2. [實際 prompt]
3. "Cute kitten playing with yarn" (Safe)
4. [實際 prompt]
5. "Beautiful sunset over mountains" (Safe)
```

### 4. Magic Portal 場景切換

用魔法傳送門繞過複雜動畫（開門、進車等）：

```
A transparent magical portal opens, instantly teleporting the character
from the dark forest to a sunlit beach.
```

替代：wormhole, reality glitch, dream sequence transition, time skip。

### 5. FPV Drone 高速鏡頭

```
FPV drone shot racing through narrow alleyway, banking sharply around
corners, weaving between obstacles at high speed, motion blur on edges.
```

### 6. 音畫同步技巧（Audio Sync）

- 視覺和音訊用**同一個觸發詞**：`The balloon pops` + `Loud popping sound`
- 明確時間：`At the exact moment of impact, loud crash sound`
- 簡化音訊請求，越少元素同步越準

## 常見問題排錯

### 頭歪/脖子折
❌ Negative prompt 沒用 → ✅ 只寫 `head remains naturally upright and centered, neutral head posture throughout`
Negative prompt 加上：`tilted head, neck bent, unnatural head position, crooked head`

### 臉變形
- 用 I2V（圖片→影片）模式
- 縮短到 5-6 秒（越長越容易飄）
- 加穩定關鍵字：`Detailed anatomy, perfect hands, symmetrical face, consistent proportions`

### 不想要的音樂
❌ `No music` → 反而加音樂（Pink Elephant Effect）
✅ `Silence, ambient sounds only` / `Muted atmosphere, natural sounds`

### 生成卡 0%
- 伺服器超載 → 等 5-10 分鐘
- 觸發審查 → 先測 `blue sky with clouds`
- 滑動視窗限制 → 等最早的那次生成「過期」

## 參考檔案

- `references/prompt-formula.md` — 6 元件公式 + JSON schema + 實際範例
- `references/keywords.md` — 鏡頭、光線、風格雷關鍵字庫
- `references/troubleshooting.md` — 完整排錯指南
- `references/tiktok-workflow.md` — 抖音個人品牌內容規劃管道
- `references/mood-combos.md` — 情緒→鏡頭+光線快速組合表
- `templates/角色手势舞.md` — 多鏡頭角色一致性影片模板
