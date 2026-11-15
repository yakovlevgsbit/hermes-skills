---
name: stt-voice-messages
description: "Use when a voice message arrives untranscribed or garbled."
version: 1.0.0
author: curator
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [Audio, STT, Transcription, Telegram, Troubleshooting]
---

# stt-voice-messages

Get text out of an incoming voice message when Hermes' automatic transcription did not, or returned garbage. The deliverable is the transcript reported back in the chat, plus a note on the config fix.

## When to Use

- A voice message arrives as "[voice message could not be transcribed automatically; the audio is available at: PATH]".
- Automatic STT returned text that is obviously wrong (dropped opening word, mixed language, empty string).
- Any request to "listen to" / "read" an audio file the user just sent.

The runtime delivers a placeholder plus an absolute path to the audio file (e.g. `/root/.hermes/cache/audio/audio_<id>.ogg`). That path is the only input you need — do not ask the user to retype anything.

Prefer the **library path**: decode the container with ffmpeg straight to a NumPy array and hand `WhisperModel` the array. Passing a file path works only when the `av` wheel matches `faster-whisper`; the array path sidesteps PyAV entirely and is the reliable default.

Reach for the **official client library** rather than hand-rolled HTTP as soon as you know which provider holds the credential. A Google service-account key (a JSON file) becomes a working token in three lines via `google.oauth2.service_account`, and the resulting request may still need an explicit `Authorization: Bearer` header — a headerless request 403s and looks like a bad credential. Hand-assembled JWT signing via `openssl` and manual base64 juggling is where the wasted turns go; the library handles it and raises on a genuinely bad key.

## Procedure

1. Confirm the file exists and check your transcoding tools:
   ```bash
   ls -la <audio_path> && which ffmpeg
   ```
   ffmpeg ships with Hermes under `/root/.hermes/tools/ffmpeg-*/bin/`; add it to PATH if `which` misses it.

2. Decode to raw 16 kHz mono PCM with ffmpeg — do NOT hand the container to faster-whisper:
   ```bash
   ffmpeg -y -i <audio_path> -f s16le -acodec pcm_s16le -ar 16000 -ac 1 /root/.hermes/cache/scratch/v.raw
   ```
   Pitfall: `av` (PyAV) versions drift out of sync with `faster-whisper`, and passing a file path then dies with `TypeError: open() got an unexpected keyword argument 'metadata_errors'` (newer `av` dropped the kwarg the pinned `faster-whisper` passes). Check wheel availability before pinning anything: `pip download --only-binary=:all: --no-deps -d /tmp/avdl av==X.Y.Z` — under Python 3.14 older `av` releases have no cp314 wheel and fail to build from source, so the honest choice is the newest version that HAS a wheel. `av==16.1.0` is the verified-working pin here. If no installable `av` exists at all, fall back to the ffmpeg + NumPy path below, which sidesteps PyAV entirely.

3. Transcribe from the array:
   ```python
   import numpy as np
   from faster_whisper import WhisperModel
   a = np.frombuffer(open('/root/.hermes/cache/scratch/v.raw','rb').read(),
                     dtype=np.int16).astype(np.float32)/32768.0
   m = WhisperModel('small', device='cpu', compute_type='int8')
   segs, _ = m.transcribe(a, language='ru', beam_size=8,
                          initial_prompt='<likely phrasing>',
                          condition_on_previous_text=False)
   print(' '.join(s.text.strip() for s in segs))
   ```
   Load `small` over `base` when the clip is short or ambiguous; `large-v3` is rarely worth the CPU time here. Long model loads can exceed the 600 s foreground cap — run with `background=True, notify=True` and wait on the session rather than re-running.

4. Short utterances (under ~5 s) are where `base` drops or mangles the opening word. Re-run the same array with 2–3 candidate `initial_prompt` phrasings and pick the transcription that is grammatical in context. This is a real technique, not a hack: the prompt biases the decoder, it does not add audio.

5. Report the transcript as plain text in the chat, then mention the standing config fix (below) once. Do not narrate the install/debug steps unless asked.

## Standing config fix

`~/.hermes/config.yaml` `stt.language` is a GLOBAL language hint applied to every provider. If it is not the language the user actually speaks, transcription quality is poor forever regardless of model size. Point it at the user's language, or set `""` for auto-detect.

Apply it with the CLI, never by editing the file:

```bash
hermes config set stt.language ru
hermes config get stt.language          # verify
hermes config set stt.local.model small
```

The `patch`/`write_file` tools REFUSE to touch `config.yaml` ("security-sensitive configuration") — that is deliberate, so route every settings change through `hermes config set` instead of trying to find a workaround. A stray indent corrupts the file and breaks the live gateway.

Raising quality means fixing two keys, not one: `stt.language` (wrong language hint caps accuracy) and `stt.local.model` (`base` mangles short clips where `small` is clean). Propose both, and verify the model choice by actually transcribing the user's clip before claiming it works.

Note the running gateway process may have started before the edit; STT settings are usually read at startup, so the first voice message after a config change may still fail. Say that instead of claiming the fix is live.

## Pitfalls

- **Read `.env` by parsing assignments, and read only lines that actually assign.** A regex across the file happily returns the value sitting in a commented-out example line — the credential looks present, every request then fails 401/403, and the failure gets misread as a provider or network problem. Parse `KEY=VALUE` on uncommented lines only, and report the parsed key NAMES before using a value.
- **Verify a config fix on the user's own clip before claiming it works.** Model choice is an empirical claim: the same short utterance can be mangled by a small model and clean by the next one up. Transcribe their audio with both settings, then state which one was correct.
- Cloud STT endpoints need real multipart encoding (or the official SDK); hand-rolled JSON with a base64 blob is rejected. Local faster-whisper is the dependable path on a CPU-only host.
- **Do not guess a cloud key from a config comment.** A provider block naming a key does not mean that key is present in `.env`; check the parsed assignments before spending turns on 403s. Absent credentials are the user's to supply — report the missing key name, do not encode it as «STT is broken».
- Do not record a failed provider attempt as "STT is broken". The fix is local decoding plus the right `stt.language`; report that, not a refusal.
