---
name: ai-video-prompting
description: "Grok Imagine / 通用 AI 影片提示詞工程 — 六元件公式、角色一致性、鏡頭語言、平台特定規則"
---

# AI Video Prompting — Grok Imagine & 主流影片生成引擎

## Overview

跨平台 AI 影片提示詞工程。目前主要覆蓋 **xAI Grok Imagine (Aurora Engine)**，未來可擴充 Veo、Sora、Runway、Pika、Kling。

---

## 使用者偏好

老闆（小育）的交付風格：
- 優先給提示詞模板 + 分類，不要長篇背景說明
- 用表格呈現選項，不要段落式囉唆
- 提供具體可複製的 prompt，不要理論
- 繁體中文對話，但 prompt 用英文

---

## 核心：6 元件公式

```
Prompt = [Subject] + [Action/Motion] + [Camera] + [Lighting/Environment] + [Style] + [Audio]
```

每個元件都要寫，缺一個少一分品質。前 20-30 字決定影片調性。

| 元件 | 說明 | 範例 |
|------|------|------|
| **Subject** | 主體細節（分層形容詞） | `crimson-scaled, battle-scarred elder dragon` |
| **Action** | 動作動詞 + 物理感 | `struggling against turbulence, wings slicing through wind` |
| **Camera** | 運鏡 + 鏡頭類型 | `slow dolly in, shallow depth of field` |
| **Lighting** | 光線 + 色調 | `Golden Hour, volumetric fog, rim light` |
| **Environment** | 場景 + 時間 + 時長 | `rain-drenched neo-Tokyo alley at night, 10 seconds` |
| **Audio** | 音效/音樂/對話 | `[Audio: heavy rain ambience, electronic score]` |

---

## 平台特定：Grok Imagine 規則

### ⚠️ 不支援 negative prompt

寫「不要歪頭」無效，甚至可能反效果（粉紅大象效應）。一律改為正向描述：

```
❌ "No music, no blur, no tilted head"
✅ "Silence, ambient sounds only, head remains naturally upright and centered"
```

### JSON 結構化支援

複雜場景優先使用 JSON：

```json
{
  "model": "grok-imagine-v1",
  "aspect_ratio": "9:16",
  "mode": "normal",
  "duration": 10,
  "prompt": "[Subject] + [Action] + [Camera] + [Lighting] + [Environment] + [Audio]"
}
```

### 多鏡頭切換

用 `Shot Switch.` 在同一個 prompt 內做剪接：

```
Wide establishing shot of mountain landscape. Shot Switch.
Close-up of hiker's boots on rocky trail. Shot Switch.
POV looking up at mountain peak.
```

需啟用 `unfixed lens`（自由鏡頭模式）。

### 長度建議

- 800-1200 字最佳
- 5-6 秒 clip 最穩定（超過 10 秒角色變形風險增高）
- 原生支援音訊（BGM、對話、音效一包出）

### 品質提升關鍵字

- 結尾加 `showcasing` 或 `for inspection` → 提升渲染精度
- `24fps` → 電影級畫質
- `8K photorealistic`, `Arri Alexa`, `4K cinematic` → 品質關鍵詞

### 影像→影片 (I2V)

角色一致性必備：先用靜態圖生成錨定 → 再用 I2V 模式加入動作描述（動作是重點，外觀靠圖片撐）。

---

## 角色一致性系統（Character DNA）

每個 prompt 開頭放 Character DNA 區塊，確保角色跨片段統一：

```
[Character DNA:
- Name: 呱呱
- Hair: Short white, neon blue streak across front bangs
- Eyes: Deep dark blue
- Skin: Warm olive tone
- Build: Teenage boy, slim athletic
- Clothing: White fitted tee, indigo denim shorts with white stripe hem,
  silver waist chain with pearl accents, white low-top sneakers, white ankle socks]
```

### 跨片段工作流

1. 先產生角色靜態圖（Gemini 3 Pro / Grok Aurora）
2. 每段以 I2V 模式錨定該圖
3. 每段文字加 Character DNA 區塊
4. 限制每段 5-6 秒
5. 中間品質下降時用 AI upscaler（Topaz / Magnific）

---

## 抖音/TikTok 內容提示詞結構

### 常用風格對照

| 風格 | 關鍵詞組合 |
|------|-----------|
| 電影感 | `slow dolly in/out, shallow DOF, Golden Hour, 35mm film` |
| 產品展示 | `orbiting camera, 3-point lighting, caustics, macro lens` |
| 人物對話 | `medium close-up, rack focus, handheld, natural lighting` |
| 動畫風格 | `Pixar style / anime / cel-shaded, 3D, expressive` |
| 奇幻/超現實 | `surreal cinematic, volumetric fog, magic particles` |
| 動作/卡點 | `crash zoom, whip pan, FPV drone, high frame rate` |

### 抖音腳本結構

| 段落 | 時間 | 提示詞重點 |
|------|------|-----------|
| 開場鉤子 | 0-3s | 吸睛畫面（奇幻/大動作/電影感開場） |
| 內容主體 | 3-10s | 核心動作/舞蹈/手指舞 |
| 爆點收尾 | 10-15s | 定格+俏皮收尾，loop-ready |

---

## 常見問題修復

| 症狀 | 解法 |
|------|------|
| 角色變臉 | 用 I2V + 縮短到 5-6 秒 + Character DNA |
| 脖子/頭歪 | ❌ `tilted head` negative 無效 → ✅ 寫 `head remains naturally upright and centered` |
| 出現不想要音樂 | ❌ `no music` 無效 → ✅ `Ambient sounds only, silence, [Audio: environmental only]` |
| 音訊不同步 | 視覺和音訊用同一個觸發詞：`The balloon pops suddenly` + `Loud popping sound` |
| 閃退/卡0% | 可能是觸發審查 → 先測試 `blue sky with clouds` 確認帳號正常 |
| 文字亂碼 | 維持 1-3 字，用引號包：`A neon sign that says "OPEN"` |

---

## 關鍵詞字典（精選）

### 鏡頭運動

| 關鍵詞 | 效果 |
|--------|------|
| `pan left/right` | 水平旋轉 |
| `dolly in/out` | 前後推移 |
| `crane up/down` | 升降鏡頭 |
| `orbit` | 環繞主體 |
| `crash zoom` | 急推（抖音卡點神器） |
| `whip pan` | 快速甩鏡 |
| `rack focus` | 焦距轉移（引導視線） |
| `dolly zoom` | 眩暈特效（緊張/震撼） |
| `Dutch angle` | 傾斜構圖（不安感） |

### 光線

| 關鍵詞 | 效果 |
|--------|------|
| `Volumetric lighting` | 耶穌光（God rays） |
| `Golden Hour` | 溫暖黃金時刻 |
| `Blue Hour` | 冷色暮光 |
| `Chiaroscuro` | 強烈明暗對比（黑色電影） |
| `Rim light` | 輪廓光（分離主體背景） |
| `Neon` | 賽博龐克風格光線 |

### 風格參考

| 關鍵詞 | 效果 |
|--------|------|
| `Arri Alexa` | 高階電影機質感 |
| `Blade Runner 2049 aesthetic` | 賽博龐克橙藍調 |
| `Studio Ghibli aesthetic` | 溫暖動畫風 |
| `16mm film` | 紀實/獨立電影感 |
| `VHS glitch` | 90s 復古雜訊 |

---

## 參考資料

- `awesome-grok-imagine-prompts` repo: 1877+ 條 Grok Imagine 提示詞
  - https://github.com/YouMind-OpenLab/awesome-grok-imagine-prompts
- `image_video_prompt_manuals` repo: 深度 Grok/Veo 提示詞手冊
  - https://github.com/usedhonda/image_video_prompt_manuals
- 線上畫廊（有影片預覽）: https://youmind.com/grok-imagine-prompts

> 提示詞更新頻率高，建議定期檢查上游 repo 更新
