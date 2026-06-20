---
name: grok-video-prompts
title: Grok Imagine Video Prompts
description: Engineering effective prompts for xAI Grok Imagine video generation. Covers the 6-component formula, JSON schema, camera movements, styles, lighting, sound design, character consistency, and troubleshooting.
category: media
triggers:
  - grok video prompt
  - grok imagine
  - video generation prompt
  - ai video prompt engineering
  - xai video
---

# Grok Imagine Video Prompt Engineering

## When to Use

Load this skill when the user asks about writing, optimizing, or troubleshooting prompts for **Grok Imagine** (xAI's video generation on the X/Twitter platform). Also load when the user mentions video prompt techniques for TikTok/Reels/Shorts content that uses Grok.

---

## Core Differences from Other AI Video Tools

| Feature | Grok Imagine | Veo / Sora / Runway |
|---------|-------------|---------------------|
| Negative prompts | ❌ **Not supported** — describe what you WANT | ✅ Supported |
| Prompt length | 800–1200 chars recommended | Varies |
| Native audio | ✅ BGM, dialogue, singing all built-in | Often separate |
| JSON structured | ✅ Supported for complex prompts | Varies |
| Generation speed | ~17 seconds avg | Minutes |
| Duration | 6–15 seconds | Varies |
| Aspect ratios | 16:9, 9:16, 1:1, 4:3, 3:4 | Varies |
| Modes | normal, fun, spicy, meme | Varies |

### The Negative Prompt Paradox

Grok **ignores** exclusion instructions. Writing "No music" or "Don't show hands" often causes those elements to appear (Pink Elephant Effect).

**Fix:** Use positive rephrasing:
- ❌ "No music" → ✅ "Silence, ambient sounds only"
- ❌ "Not blurry" → ✅ "Sharp focus, high fidelity, crystal clear"
- ❌ "No glasses" → ✅ "Clear face, uncovered eyes"

---

## The 6-Component Formula

```
Prompt = [Subject] + [Action] + [Camera] + [Lighting] + [Environment] + [Audio]
```

| Component | Description | Best Practice |
|-----------|-------------|---------------|
| **Subject** | Who/what is in frame | Use layered adjectives: "crimson-scaled, battle-scarred elder dragon" not just "dragon" |
| **Action/Motion** | How subject moves | Include physics: "struggling against turbulence, wings slicing through wind" |
| **Camera Movement** | Viewpoint control | Use "Camera" as subject: "Camera pans left" to avoid ambiguity |
| **Visual Style** | Quality, medium, aesthetic | Equipment names work: "Arri Alexa", "35mm film", "VHS" |
| **Environment** | Place, time, atmosphere | Light conditions (Golden Hour), weather, explicit duration |
| **Audio Direction** | Sound instructions | Use brackets: `[Audio: ambient sounds only]` for better recognition |

---

## Prompt Best Practices

1. **Front-load important details** — first 20–30 words set the tone
2. **One style only** — don't mix multiple aesthetics
3. **Explicit colors** — "red apple" not just "apple"
4. **Avoid pronouns** — use specific names, not "she/he/it"
5. **Use THEN for sequences** — "Bird flies THEN lands" for staged actions
6. **End prompts with `showcasing` or `for inspection`** — quality boosters

### Multi-Scene with Shot Switch

Use `Shot Switch.` to create cuts between scenes:

```
Wide establishing shot of mountain landscape. Shot Switch.
Close-up of hiker's boots on rocky trail. Shot Switch.
POV looking up at mountain peak.
```

**Requirement:** Set lens mode to `unfixed` (free camera) when using Shot Switch.

---

## JSON Structured Prompts

For complex scenes, structured JSON provides more precise control:

```json
{
  "model": "grok-imagine-v1",
  "aspect_ratio": "9:16",
  "mode": "normal",
  "duration": 10,
  "prompt": "Subject: [description]. Action: [movement]. Camera: [shot type and movement]. Lighting: [light description]. Style: [aesthetic]. Audio: [sound instructions]."
}
```

### 6-Component Full Example (TikTok)

```json
{
  "model": "grok-imagine-v1",
  "aspect_ratio": "9:16",
  "mode": "normal",
  "duration": 10,
  "prompt": "Subject: An anime-style cute teenage boy with short white hair and a neon blue streak across his bangs, deep dark blue eyes, wearing a white fitted t-shirt, indigo denim shorts with white stripe trim, and a silver waist chain with pearl accents. Action: He performs energetic hand gestures and finger-tutting moves in sync with a beat, precise joint articulation at high speed. Camera: Medium close-up, tight framing on upper body and both hands. Slow dolly in during the build-up. Lighting: Neon blue and hot pink pulses wash across his white t-shirt, rim light separating his white hair from the dark background. Style: Anime cinematic, 4K, high shutter speed, crisp depth of field. Audio: Heavy bass beat drop sync, subtle electronic hi-hats in background."
}
```

### Image-to-Video (I2V) Pattern

When animating a static image:

```json
{
  "model": "grok-imagine-v1",
  "image_urls": ["https://your-storage.com/character.jpg"],
  "mode": "normal",
  "prompt": "Action: The character turns their head slowly to look at the camera and smiles warmly. Hair flows gently in a breeze. Eyes blink naturally. Camera: Static shot with shallow depth of field. Lighting: Preserve original lighting. Audio: Soft wind sound, distant birds chirping."
}
```

---

## Audio Instructions

- BGM: Describe mood and genre
- SFX: Specify environmental sounds
- Dialogue: Include exact spoken words in quotes
- Singing: Describe vocal style

**Trigger word matching** — match the same word in visual and audio descriptions for better sync:
```
Visual: "The balloon pops suddenly"
Audio: "Loud popping sound"
```

---

## Character DNA System

For consistent character appearance across multiple clips, include a Character DNA block at the start of EVERY prompt:

```
[Character DNA:
- Name: Guagua
- Hair: Short white, neon blue streak across front bangs
- Eyes: Deep dark blue
- Skin: Warm olive tone
- Build: Teenage boy, slim athletic
- Clothing: White fitted tee, indigo denim shorts with white stripe hem,
  silver waist chain with pearl accents, white low-top sneakers, white ankle socks]
```

---

## References

See `references/` for detailed keyword dictionaries covering:
- `camera-movements.md` — all shot types, lens effects, speed modifiers
- `styles-aesthetics.md` — technical quality, film references, art movements
- `lighting-color.md` — lighting types, color grading, atmospheric effects

---

## Pitfalls

### Face/Body Morphing
- Use I2V (Image-to-Video) mode with a reference image
- Add stability keywords: "Detailed anatomy, perfect hands, symmetrical face, consistent proportions, stable identity"
- Reduce motion intensity for sensitive subjects
- Keep clips 5–6 seconds for maximum stability
- Post-fix: FaceFusion for face consistency

### Audio Desynchronization
- Use trigger word matching (same word in visual and audio descriptions)
- Explicit timing cues: "At the exact moment of impact, loud crash sound"
- Simplify audio requests (fewer elements = better sync)
- Shorter clips (5–6s) maintain sync better

### Text Rendering
- Keep to 1–3 word signs for ~70% accuracy
- Quote the text: `A neon sign that says "OPEN"`
- Use familiar formats: "STOP", "EXIT", "CAFE"
- For important text, add in post-production

### Unwanted Music
- Don't use negatives — specify what you DO want:
  - ✅ "Silence, ambient sounds only"
  - ✅ "Environmental audio only"
  - ✅ "Muted atmosphere, natural sounds"

### Generation Stuck at 0%
- Wait and retry (server overload)
- Review prompt for silent moderation triggers
- Free/basic limits use 24-hour SLIDING windows (not daily resets)
- Test with simple prompt: "Blue sky with clouds" to verify account status

### Style Conflicts
- Don't mix incompatible styles:
  - ❌ "anime + photorealistic + watercolor"
  - ✅ "Cinematic anime with soft lighting"

---

## Workflow: The Last Frame Method

Extend video beyond the default duration:

1. Generate Scene 1 (Text-to-Video)
2. Extract final frame as high-quality PNG
3. Use Image-to-Video with extracted frame
4. Describe next action in prompt
5. AI upscale between cycles (Topaz, Magnific) to prevent quality degradation
6. Limit to 3–4 cycles before quality reset

---

## TikTok-Specific Tips

- Use 9:16 aspect ratio
- 5–10 second clips for short-form content
- First 2–3 words = hook
- Audio sync is critical — use trigger word matching
- Shot Switch for visual variety
- Front-load camera direction for dynamic openings
