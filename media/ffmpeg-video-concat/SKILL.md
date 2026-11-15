---
name: ffmpeg-video-concat
description: Use when gluing an outro/banner onto a video with ffmpeg.
---

# Appending clips to video with ffmpeg

Use when a video needs a banner/clip glued on (outro, intro, CTA), or two clips
of unknown provenance must be joined.

## The three traps (all produce a BROKEN file, not an error)

**1. Never use the concat DEMUXER for mismatched inputs.**
The demuxer (`-f concat -i list.txt`) requires identical codec, resolution,
fps, sample rate and channel layout. When anything differs it exits 0 and writes
a file that plays only the first segment, or freezes, or loses audio. Use the
concat **filter** — it normalises for you:

```
ffmpeg -y -i main.mp4 -i outro.mp4 \
  -filter_complex "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]" \
  -map "[v]" -map "[a]" -c:v libx264 -c:a aac out.mp4
```

**2. A clip with no audio track kills audio for the WHOLE result.**
The filter above references `[1:a]`, so an outro without sound breaks the join.
Detect it and synthesise silence of matching length:

```
ffmpeg -y -i outro.mp4 -f lavfi -t <DUR> -i anullsrc=channel_layout=stereo:sample_rate=44100 \
  -map 0:v -map 1:a -c:v libx264 -c:a aac -shortest outro_norm.mp4
```

**3. Normalise BOTH sides to the main video's geometry.**
Resolution and fps must match exactly. Target the MAIN clip's parameters (not the
outro's) and force even dimensions — H.264 rejects odd width/height:

```
scale=W:H:force_original_aspect_ratio=decrease,pad=W:H:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps=FPS
```

A still image becomes a clip with `-loop 1 -t <seconds>` plus an `anullsrc` track.

## Read the source parameters first

```
ffprobe -v error -print_format json -show_streams -show_format input.mp4
```
Grab `width`, `height`, `r_frame_rate` (a fraction like `30/1` — divide it), and
whether an audio stream exists. Never assume 1080x1920@30.

## Verify the result, don't trust exit code

Compare duration and streams against the expected sum:

```
ffprobe -v error -show_entries format=duration -show_entries stream=codec_type,width,height -of default=noprint_wrappers=1 out.mp4
```
A 6s main + 3s banner MUST report ~9s. Shorter means the join silently dropped a
segment. For publishing pipelines, download the file back from the destination
(Telegram `getFile`, etc.) and probe that — it proves what actually shipped.

## Encode settings that work everywhere

`-c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -c:a aac -b:a 128k`
plus `-movflags +faststart`. This plays on YouTube, Telegram, Instagram and TikTok.
On a 4-vCPU box expect roughly realtime (30s video ≈ 26s encode).

## Batch pipelines: bake once, reuse

When the same outro goes onto many videos, process at upload/apply time and store
the result, then have the publisher prefer the processed file. Re-encoding inside
a scheduler is slow and turns transient ffmpeg failures into missed posts.
