---
name: dewiar-reverse-engineering
description: "Use when building voice AI assistants or LLM tools."
---

# Dewiar - Reverse-Engineering Analysis

GitHub: https://github.com/dwr-git/dewiar-app
Python 3.10+, 93 core modules, ~45k LOC.

> **Полный разбор всех 93 модулей** (64 КБ): `/root/kb/projects/dewiar-reverse-engineering.md`
> Читай этот файл для деталей — здесь только краткая выжимка.

## Architecture

```
main.py -> Bridge (WebSocket) + Engine (God Object from 9 Mixins)
Engine: AudioMixin -> AnswerMixin -> ToolsMixin -> MusicMixin -> BrainMixin -> RemoteMixin -> CommandsMixin -> IntroMixin -> HealthMixin
Threads: audio(32ms) -> stt -> name-check -> brain(LLM) -> tts_worker -> speaker
+ sync, cloud, obsidian, diary, night, telegram, max, calendar, backup, knowledge-watch, updates, welcome, brain-watch, tg-sync, radio-check, close
```

## Key Patterns Worth Reusing

### 1. Model-Agnostic LLM Abstraction (core/llm.py, 1417 lines)
- Profile: {active, profiles: {name: {url, key, model, kind}}}
- stream_chat() returns generator of ("text", chunk) and ("tools", calls)
- ThinkStripper cuts think tags from stream (gate=60 chars)
- probe_tools() checks function calling, remembers per-address
- discover_local() auto-detects Ollama(11434), LM Studio(1234), llama.cpp(8080)
- Graceful degradation: no tools -> describes tools as text

### 2. Name Spotting (core/engine_base.py:find_name)
- difflib.SequenceMatcher, threshold 0.75/0.86
- Two modes: normal (first 3 words) and strict (first word only)
- Word gluing: "Де Виар" -> "девиар"
- Short names (<=4 chars): only exact match in strict mode

### 3. Skill System (core/skills.py, 312 lines)
- Agent Skills format: SKILL.md with frontmatter (name, description)
- Model sees only descriptions; full text via use_skill tool
- parse_skill() returns {name, title, description, body, dir}
- User skills override builtin; scripts only via run_command

### 4. Exam System (core/exam.py, 1180 lines)
- 50+ scenarios in data/exam/scenarios.json
- Each: say -> answer -> expect (words/numbers) + state (reminders/tasks) + LLM judge (0-10, pass >=6)
- Judge: "Сверяй слова с ДЕЛАМИ: сказал открыл, а действия не было - выдумка"
- Code: task_create -> tests + hidden tests

### 5. VAD + STT + TTS Pipeline
- Silero VAD (ONNX, 32ms frames) -> WakeSpotter (Vosk partial) -> GigaAM/Vosk/Remote -> LLM -> Vosk/Piper/Qwen3
- Barge-in: interrupt by voice or name
- EchoCancel: WebRTC AEC via PipeWire (Linux), full-duplex on Windows

### 6. Android WebView Bridge (Bridge.java, 660 lines)
- @JavascriptInterface methods called as window.Dewiar.*
- Short calls return immediately; long operations via events
- safe(name) - path traversal protection
- PixelCopy for screenshots

### 7. Voiceprint (core/voiceprint.py, 193 lines)
- MFCC features + DTW matching
- Works for any word, fast, no models needed
- Training: say name 3 times via GigaAM

### 8. Dialogue Without LLM (multiple modules)
- when.py - time parsing (завтра в 9 утра -> datetime)
- quickmath.py - math expressions
- capture.py - закинуть идею
- pc.py - volume, power (выключи компьютер)
- money.py - expenses (купил кофе за 8 рублей)
- smarthome.py - smart home (включи свет)
- music.py - radio (включи джаз)

### 9. Long-Running Tasks (core/tasks.py, 1634 lines)
- Folder per task: задача.json, история.json, план.md, журнал.md, блокнот.md, outputs/
- Statuses: running -> waiting/sleeping -> done/failed/stopped
- Tools: update_plan, log, ask_user, finish, remember, notify, wait, spawn_parts
- Code mode: code_read, code_edit, code_write, code_run, code_undo, code_diff
- LoopGuard - detects stuck loops

### 10. Близкие (Close) - E2E Encrypted Messaging
- X25519 key exchange, HMAC-SHA256 + keystream encryption
- Messages between assistants of different people via cloud relay
- Server sees only encrypted metadata

### 11. Core Modules Reference

| Module | Lines | Purpose |
|--------|-------|---------|
| main.py | 134 | Entry point, logging, systemd |
| engine.py | 627 | God Object (9 Mixins) |
| engine_base.py | 365 | Imports, find_name, stop_word, redact |
| engine_audio.py | 1185 | Audio loop, VAD, STT |
| engine_answer.py | 1500 | Response generation |
| engine_tools.py | 1312 | Tool execution, confirmation |
| engine_brain.py | 839 | LLM selection, cloud, proxy |
| engine_commands.py | 1253 | UI commands |
| llm.py | 1417 | LLM abstraction |
| tasks.py | 1634 | Background tasks |
| conversation.py | 176 | Conversation history |
| sync.py | 844 | Cloud sync |
| bridge.py | 175 | WebSocket bridge |
| vault.py | 204 | Password vault |
| mcp.py | 322 | MCP client |
| crypt.py | 111 | Encryption (SHAKE-256 + HMAC) |
| close.py | 830 | E2E messaging |
| closecrypto.py | 141 | X25519 + keystream encryption |
| knowledge.py | 411 | BM25 knowledge base |
| obsidian.py | 477 | Obsidian sync |
| settings.py | 293 | Settings, LLM presets |
| workspace.py | 656 | File workspace |
| when.py | 445 | Time parsing |
| guard.py | 417 | Action protection |
| night.py | 208 | Night maintenance |
| diary.py | 281 | Diary |
| soul.py | 245 | Constitution and soul |
| personas.py | 704 | Characters |
| skills.py | 312 | Skills |
| tools.py | 2537 | Tools and reminders |
| audio_io.py | 658 | Audio I/O |
| stt.py | 221 | Speech recognition |
| tts.py | 583 | Speech synthesis |
| listen.py | 186 | VAD and WakeSpotter |
| voiceprint.py | 193 | Voice fingerprint |
| prompter.py | 715 | Meeting prompter |
| quality.py | 710 | Quality checks |
| backup.py | 385 | Backups |
| updater.py | 306 | Auto-updates |
| telegram.py | 617 | Telegram bot |
| maxbot.py | 380 | MAX messenger |

## Dependencies

numpy, onnxruntime, vosk, onnx-asr, piper-tts, httpx, websockets, pywebview, Pillow, pulsectl, imageio-ffmpeg, pypdf, socksio