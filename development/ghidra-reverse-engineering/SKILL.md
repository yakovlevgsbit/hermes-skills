---
name: ghidra-reverse-engineering
description: "Use when analyzing binaries with Ghidra."
---

# Ghidra — Reverse Engineering Framework

GitHub: https://github.com/NationalSecurityAgency/ghidra
Apache-2.0, 87.6k stars. By NSA.

> **Полный разбор**: `/root/kb/projects/ghidra-reverse-engineering.md`

## What It Is

Ghidra — SRE фреймворк от NSA. Disassembly, decompilation, graphing, scripting.

## Architecture

```
Ghidra Framework
├─ Core Engine
│  ├─ Sleigh (processor specs)
│  ├─ P-Code (IR for decompilation)
│  ├─ Decompiler (P-Code → C pseudocode)
│  ├─ Graph (call graphs)
│  └─ Script (Jython/Python 2.7)
├─ UI: Swing (CodeBrowser, Function Graph, Listing)
└─ Extensions: GhidraDev (Eclipse) / VS Code
```

## Supported Architectures

x86 (16/32/64), ARM (A32/Thumb/A64), AArch64, MIPS, PowerPC, SPARC, AVR, 68k, Z80, 8051, MSP430, JVM, EVM, + dozens more.

## File Formats

PE, ELF, Mach-O, RAW, COFF, GZIP, PDF, DMG, JAR, APK, ZIP, ROM, SREC, HEX...

## Modes

| Mode | What |
|------|------|
| Interactive | GUI: CodeBrowser, Function Graph, Decompiler |
| Headless | CLI (analyzeHeadless) for automation |
| Scripting | Jython/Python inside Ghidra |
| PyGhidra | Python via JPype (CPython) |

## Installation

```bash
# Requires JDK 25 (64-bit)
unzip ghidra_11.x_PUBLIC_*.zip
./ghidraRun  # or ghidraRun.bat on Windows
./support/pyghidraRun  # PyGhidra
```

## Comparison with REA

| What | REA | Ghidra |
|------|-----|--------|
| Approach | MCP + AI agent | GUI + scripts |
| AI integration | Native | Via REA or manual |
| Decompilation | Via provider | Built-in |
| Price | MIT (needs Hopper/IDA) | Completely free |
| Learning curve | Low (agent) | High (GUI) |

## Key Patterns

1. **P-Code IR** — universal IR for decompilation
2. **Sleigh specs** — extensible disassembler via .slaspec files
3. **Headless automation** — for batch analysis
4. **Jython scripting** — Python 2.7 inside Java
5. **Plugin architecture** — Eclipse + VS Code
6. **Multi-architecture** — one tool for dozens of processors

## Итог

Ghidra — 87.6k stars, NSA, full RE framework. P-Code IR, Sleigh specs, headless automation, multi-architecture, free.

Самое ценное для Георгия:
- **P-Code IR** — универсальный подход к декомпиляции
- **Sleigh спецификации** — расширяемый дизассемблер
- **Headless automation** — для пакетного анализа
- **Много архитектур** — один инструмент для всего
- **Free** — в отличие от IDA Pro
- **REA provider** — интеграция с REA