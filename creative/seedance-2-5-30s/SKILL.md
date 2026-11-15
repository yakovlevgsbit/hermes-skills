---
name: seedance-2-5-30s
description: Seedance 2.5 30s hard lock.
---

# Seedance 2.5 – 30s Hard Lock

## Hard Lock (non-negotiable, overrides everything below)

- **Duration is locked at 30 seconds.** Always pass `duration: 30`.
- **One single continuous segment.** One tool call = one complete 30-second video. This is the only delivery path.
- **Model is locked to Seedance 2.5.** Always pass `model_version: "seedance_2.5"` explicitly in every call.

### Anti-spreading rules – never do any of these:

- Never split into two 15-second clips or any multi-part sequence.
- Never propose, offer, suggest, or mention a two-segment / two-clip / chaptered / multi-part delivery.
- Never offer a "single 15s compressed" alternative or any shorter-compressed fallback.
- Never present a "platform limitation", "tool cap", "runtime doesn't support 30s" disclaimer, Plan B, fallback, or workaround.
- Never ask the user to choose between split options, segment counts, or duration fallbacks.
- Never use the words "split", "segments", "clips", "chapters", "15s", "fallback", or "Plan B" in a confirmation summary.

### Special case – user explicitly requests under 30 seconds:

If the user explicitly requests a duration shorter than 30 seconds, still use **one single call**, with `duration` set to the requested length (within the 5–30s range supported by the tool). No splitting. This is the only exception to the 30-second default, and it only applies when the user themselves specifies a shorter duration.

### Longer than 30 seconds:

If the user requests longer than 30 seconds: still **one single 30-second call** compressing the narrative arc. No splitting.

### Maximum videos per reply:

**2 (hard cap)** – each is its own complete single-segment video.

---

## Core Capability

This skill generates videos using the Seedance 2.5 model (`model_version: "seedance_2.5"`). Seedance 2.5 produces complete 30-second videos in a single generation call. Always generate one continuous 30-second segment. A single 30-second call is the only path.

## Model Specification

- **Model:** Seedance 2.5 (`seedance_2.5`) – always specify explicitly.
- **Duration:** 30 seconds, single continuous segment.
- **Supported ratios:** 21:9, 16:9, 4:3, 1:1, 3:4, 9:16.
- **Maximum videos per reply:** 2 (hard cap).
- **Input modes:** text-to-video (`text_to_video`), image-to-video (`image_to_video`).

---

## Workflow

### 1. Planning Phase

Design the concept as **one cohesive 30-second narrative arc** covering beginning, middle, and end. Structure the prompt with clear pacing and shot progression:

- **Opening (0–5s):** establish subject, scene, atmosphere.
- **Development (5–20s):** main action, escalation, camera movement.
- **Resolution (20–30s):** climax, payoff, closing shot.

Include all visual details: subjects and their appearance, wardrobe, props, action beats, scene/environment, style, lighting, color grade, camera movement, mood, and pacing.

### 2. Confirmation Requirements

Before generation, present a confirmation summary. It must include:

- **Duration:** 30 seconds (single continuous segment)
- **Model:** Seedance 2.5
- **Ratio:** e.g. 21:9, 16:9, 9:16
- **Style:** full visual style description
- **Scene / characters / props:** all key visual elements
- **Lighting:** key light, fill, rim, color temperature
- **Content:** full 30-second narrative / shot progression
- **Negative constraints:** anything to avoid
- **Audio note:** generation is visual-only – dialogue/SFX/music expressed through mouth shapes, expression, and action timing; no audio track is generated; audio must be added in post.

The confirmation summary must contain **no fallback, Plan B, clip split, two-segment, duration-alternative, or platform-limitation language.** The output is one 30-second video.

Wait for explicit user confirmation (go, confirm, generate, start, yes, etc.) before calling the tool.

### 3. Generation Phase

After the user says "go":

Call `text_to_video` (or `image_to_video` if reference images are used) with:

- `model_version: "seedance_2.5"`
- `duration: 30`
- `ratio:` confirmed ratio
- `prompt:` comprehensive full 30-second description
- `image_reference_url_list:` only URLs returned by `FileBatchUpload` (for image-to-video)

Deliver the resulting video via `NotifyHuman`, including a renderable video asset (`video_url`, `output_url`, `url`, `result_url`, or local path).

That is the entire generation flow. **One call. One 30-second video. No splitting.**

---

## Parameter Clarification

Confirm before generation:

- **Duration:** 30 seconds default (or custom shorter duration only if the user explicitly specifies one)
- **Ratio:** 21:9, 16:9, 4:3, 1:1, 3:4, 9:16
- **Detailed content:** subject, action, scene, style, camera movement, mood, lighting, color palette, shot progression
- **Input type:** text-only or with reference images
- **Negative constraints:** anything to exclude

If the user provides only a brief concept, infer reasonable parameters and present them for confirmation. Do not infer any split or fallback.

---

## Image-to-Video with Seedance 2.5

When using reference images:

1. Inspect all local image files with `Read` first (visual inspection is required before reasoning about a frame's content).
2. Upload local images via `FileBatchUpload` to obtain public URLs.
3. Use only the returned URLs in `image_reference_url_list`.
4. Describe in the prompt which visual characteristics must be preserved (subject, style, composition, lighting).

---

## Generation Rules

- **One call, one 30-second video** – never split into multiple clips. Never propose a fallback. Never mention two-segment delivery.
- **Never exceed 2 videos per reply** – hard cap.
- **Always confirm parameters** before generation.
- Use `model_version: "seedance_2.5"` explicitly in every call.
- Use `duration: 30` for full-length generation.
- Deliver videos via `NotifyHuman` – include a renderable video asset.
- **Audio is visual-only** – state this in every confirmation summary.

---

## Prompt Crafting for 30-Second Videos

A strong 30-second prompt includes:

- **Opening hook (0–5s):** subject, scene, atmosphere established.
- **Development (5–20s):** main action, escalation, camera progression.
- **Resolution / payoff (20–30s):** climax, punchline, closing shot.
- **Technical specifics:** lighting, color palette, lens, camera style, pacing, frame-rate feel.
- **Atmosphere:** mood, tone, environmental details.
- **Negative constraints:** what to avoid (text, watermark, wrong palette, drift, etc.).

---

## Tool Call Pattern – Single 30-Second Segment (the only pattern)

### Text-to-video:

```
text_to_video(
  model_version: "seedance_2.5",
  duration: 30,
  ratio: "<confirmed-ratio>",
  prompt: "<comprehensive 30-second narrative prompt>"
)
```

### Image-to-video (add reference URLs only from FileBatchUpload):

```
image_to_video(
  model_version: "seedance_2.5",
  duration: 30,
  ratio: "<confirmed-ratio>",
  prompt: "<comprehensive 30-second narrative prompt>",
  image_reference_url_list: ["<url-from-FileBatchUpload>", ...]
)
```