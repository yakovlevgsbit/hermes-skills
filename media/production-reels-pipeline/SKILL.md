---
name: production-reels-pipeline
description: "Use when shipping production reels."
version: 1.0.0
author: curator
license: MIT
metadata:
  hermes:
    tags: [reels, video-generation, youtube, anymodel, production]
    related_skills: [reels-publisher, youtube-content, hermes-cron]
---

# Production Reels Pipeline

## When to Use

Use when the user asks to run the local reels-agent, generate an Anime Auto Lab
video, or publish a generated reel to the user's YouTube channel.

## Scope

Use this skill for the user's Anime Auto Lab flow: choose or accept a car concept,
generate a cover and a 9:16 video through the local `reels-agent`, publish directly
to YouTube, and verify the resulting public video. This is the production path,
not the generic Upload-Post publisher path.

## Standing channel rules

- YouTube title is **only the car make/model or the exact approved car title**.
  Do not put actions, scenery, mood, comparisons, or hashtags in the title unless
  the user explicitly changes this standing rule.
- YouTube description is **only space-separated English hashtags**. No prose,
prompt, weather, camera description, or call to action.
- Use English for prompts, car names, hashtags, and machine-facing metadata.
- Generated covers have no text, letters, logos, watermarks, or license plates
  unless the user explicitly requests otherwise.
- Default output is vertical 9:16, 10 seconds, 720p, public YouTube upload.

## Procedure

1. **Inspect before generating.** Check `/root/reels-agent/input/`, the Supabase
   queue with `python3 /root/reels-agent/supabase_pipeline.py --pending`, and
   existing process state. If a production run is already active, do not start a
   second one; monitor the existing log/process instead.

2. **Dry-run the exact pipeline.** Run:
   ```bash
   cd /root/reels-agent
   python3 auto_pipeline.py --dry-run
   ```
   Confirm the selected car is not an already-published duplicate, the environment
   is acceptable, the generated English hashtags are present, and the estimated
   cost fits the AnyModel balance. A dry-run is cheap and catches queue/state
   mistakes before spending tokens.

3. **Run the production pipeline.** For the autonomous AAL flow use:
   ```bash
   cd /root/reels-agent
   python3 auto_pipeline.py --max-wait 1200
   ```
   For a user-supplied exact image/video prompt, use
   `make_from_prompt.py` rather than `package.py`; the former preserves the
   supplied prompt and the latter asks an LLM to construct one from a topic.
   Keep the process tracked as a background job for the 1–3 minute video wait;
   do not rerun it just because an intermediate heartbeat says `pending`.

4. **Monitor to terminal state.** Follow the run log and wait for one of:
   `ГОТОВО ... -> https://youtu.be/... (public)`, quota failure, or a real error.
   A cover being ready is not completion; the video must be downloaded, copied to
   nginx, and uploaded.

5. **Verify external state.** Never trust the pipeline's success line alone. Read
   the exact YouTube video back through Data API v3 (`videos.list` with
   `part=snippet,status,statistics`) and verify all of:
   - channel is `Anime Auto Lab`;
   - title is the intended car title;
   - `privacyStatus=public`;
   - `uploadStatus=processed`;
   - description contains only the intended hashtags;
   - returned URL and video ID are present.
   Report the verified URL and current view count.

6. **Check the generated file when useful.** Use `ffprobe` to verify H.264,
   vertical dimensions, and approximately 10 seconds. Do not block delivery on
   an unavailable image library when `ffprobe` and the pipeline's byte-size checks
   already verify the video.

## API and metadata rules

- `yt_upload.py --hashtags` feeds YouTube's hidden `snippet.tags`; the visible
  description must still be populated with the hashtags. Before publishing, the
  upload wrapper must derive `description = " ".join("#" + tag for tag in tags)`
  when no explicit description is supplied.
- Validate the final title and description before upload, not after: the AAL OAuth
  token may have only `youtube.upload` and `youtube.readonly`. With those scopes,
  `videos.update` and `videos.delete` return insufficient-permission errors.
  A bad public upload may therefore require a second upload and manual deletion
  in YouTube Studio.
- Direct YouTube upload is preferred over Upload-Post for AAL because the direct
  OAuth path is already configured and the channel's public state can be verified
  through the Data API.

## Failure handling

- Treat `quota_exceeded` as a distinct state from a failed generation: the video
  may be complete and only YouTube's daily upload quota is exhausted.
- On a video-generation `pending` state, wait up to the configured max; do not
  spend again by launching a duplicate job.
- If upload returns a URL, still read the exact video back before claiming success.
- If metadata is wrong and the token lacks update/delete scopes, do not repeatedly
  retry destructive operations; preserve the verified IDs and tell the user what
  must be removed or reauthorized.
- Keep the generation log and final URL in the response, but do not expose API
  keys, refresh tokens, or other secret values.

## Compact verification checklist

- [ ] Queue and active processes checked before start.
- [ ] Dry-run completed and cost accepted by available balance.
- [ ] Cover generated without text.
- [ ] Video is vertical, about 10 seconds, and 720p/H.264.
- [ ] Upload completed as public and processed.
- [ ] YouTube API read-back confirms channel, title, hashtag-only description.
- [ ] Final URL is reported only after read-back verification.
