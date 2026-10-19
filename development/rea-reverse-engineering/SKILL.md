---
name: rea-reverse-engineering
description: "Use when reverse engineering binaries or apps."
---

# REA — Reverse Engineer Anything

GitHub: https://github.com/morluto/rea
MIT, 324.7k stars. By morluto.

> **Полный разбор**: `/root/kb/projects/rea-reverse-engineering.md`

## What It Is

Один MCP-сервер для реверс-инженерии чего угодно. Подключаешь к AI-агенту — он может инспектировать нативные бинарники, JavaScript/Electron, .NET, Android APK, firmware, WASM, EVM, веб-сайты и живые процессы.

## Architecture

```
Агент (Claude Code, Codex, Cursor, Gemini)
  ↕ MCP (stdio)
REA (rea-agents)
  ├─ Native → Hopper / Ghidra / IDA / Rizin
  ├─ JS/Electron → Wakaru
  ├─ .NET → статический CIL
  ├─ Android → JADX + Apktool
  ├─ Firmware → Binwalk / Unblob
  ├─ WASM → WABT (WAT)
  ├─ EVM → offline bytecode
  ├─ Go/Rust → статический ELF/PE/Mach-O
  ├─ Websites → Chrome CDP
  ├─ Process → PTY capture
  └─ Packets → TShark
```

## What You Can Analyze

| Цель | Возвращает | Требования |
|------|-----------|------------|
| Native binaries | Pseudocode, assembly, strings | Hopper/Ghidra/IDA |
| JavaScript/Electron | Modules, imports, routes, IPC | Node.js |
| .NET | Metadata, CIL instructions | None (static) |
| Android APK | Manifest, classes, methods | JADX + JDK |
| Firmware | Regions, extraction | Binwalk/Unblob |
| WASM | Validation, WAT forms | WABT |
| EVM | Selectors, arguments | Linux x64 |
| Go/Rust | Compiler version, modules | Built-in |
| Websites | Structure, scripts, network | Chrome |
| Process | Output, interactions | Linux/macOS PTY |

## Key Concepts

1. **Evidence-backed** — каждый finding с evidence и limitations
2. **Local-first** — анализ локально, без загрузки
3. **Provider-agnostic** — Hopper, Ghidra, IDA, Rizin, JADX, Wakaru
4. **MCP + CLI dual** — один движок, два интерфейса
5. **Agent-native** — интеграция с агентами из коробки

## Installation

```bash
npx rea-agents setup          # первая установка
npm install --global rea-agents  # глобально
rea update                    # обновление
```

## Showcases

- DX-Ball: реконструкция sound-pan (3,205 тестов, 63 байта)
- Notion: трассировка Electron clipboard bridge
- TH04: восстановление DOS bullet-ring

## Key Patterns

1. **MCP for RE** — один MCP для всего RE
2. **Evidence-backed** — как Graphify EXTRACTED/INFERRED
3. **Local-first** — приватность из коробки
4. **Multi-target** — один интерфейс для всего
5. **Provider-agnostic** — не залочен
6. **MCP + CLI** — двойной интерфейс
7. **Showcase-driven** — реальные кейсы

## Итог

REA — 324.7k stars, один MCP для реверс-инженерии чего угодно. Multi-target, evidence-backed, provider-agnostic.