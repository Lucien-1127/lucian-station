---
name: media-tools
description: 多媒體工具集 — GIF 搜尋、YouTube 逐字稿、音訊頻譜分析
version: 1.0.0
author: Lucian
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  commands: [python3, curl]
  pip:
    - youtube-transcript-api
  optional:
    - librosa
    - matplotlib
    - numpy
    env:
      TENOR_API_KEY: 用於 GIF 搜尋（https://tenor.com/gifapi）
---

# 多媒體工具集

合併自：gif-search、youtube-content、songsee

---

## 1. GIF 搜尋（Tenor）

透過 Tenor API 搜尋與下載 GIF。

```bash
# 搜尋 GIF
curl -s "https://tenor.googleapis.com/v2/search?q=cat&key=YOUR_KEY&limit=5" | jq '.results[] | {url: .url, description: .content_description}'

# 下載 GIF
curl -s "https://tenor.googleapis.com/v2/search?q=wave&key=YOUR_KEY&limit=1" | jq -r '.results[0].media_formats.gif.url' | xargs curl -o /tmp/output.gif
```

## 2. YouTube 逐字稿

取得 YouTube 影片逐字稿並轉為摘要、討論串或部落格文章。

```bash
# 安裝工具
pip install youtube-transcript-api

# 取得逐字稿
python3 -m youtube_transcript_api VIDEO_ID

# 或指定語言
python3 -m youtube_transcript_api VIDEO_ID --languages zh-TW
```

## 3. 音訊頻譜分析

透過 CLI 產出音訊頻譜圖與特徵（mel、chroma、MFCC）。

```bash
# 安裝相依套件
pip install librosa matplotlib numpy

# 產生頻譜圖
python3 -c "
import librosa, librosa.display, matplotlib.pyplot as plt, numpy as np
y, sr = librosa.load('audio.mp3')
plt.figure(figsize=(12, 4))
librosa.display.waveshow(y, sr=sr)
plt.savefig('waveform.png')

# Mel 頻譜
mel = librosa.feature.melspectrogram(y=y, sr=sr)
librosa.display.specshow(librosa.power_to_db(mel, ref=np.max), sr=sr, x_axis='time', y_axis='mel')
plt.savefig('mel-spectrogram.png')
"
```

### 特徵萃取

```bash
# MFCC 特徵
python3 -c "
import librosa
y, sr = librosa.load('audio.mp3')
mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
chroma = librosa.feature.chroma_stft(y=y, sr=sr)
spectral = librosa.feature.spectral_centroid(y=y, sr=sr)
print(f'MFCC shape: {mfcc.shape}')
print(f'Chroma shape: {chroma.shape}')
print(f'Spectral centroid mean: {spectral.mean():.2f} Hz')
"
```
