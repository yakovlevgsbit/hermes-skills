---
name: youtube-video-download
description: "Use when asked to download a YouTube video or short."
version: 1.0.0
author: Hermes Agent (Мария)
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [YouTube, Video, Download, yt-dlp, Media]
    related_skills: [youtube-content]
---

# YouTube video download

## When to use

Георгий даёт ссылку на YouTube (shorts/watch/youtu.be) и говорит «скачай».
Отличие от скилла `youtube-content`: тот про транскрипты и текст, этот — про сам файл видео.

## Правило №1: отдавать публичную ссылку, а не путь в scratch

`/root/.hermes/cache/scratch/` чистится прунингом (24h idle) — файлы оттуда
исчезают, а выданный путь перестаёт работать. Кроме того scratch не обслуживается
HTTP-сервером, а поднимать свой нельзя: **порт 8765 занят SMM-панелью**
(FastAPI, проксируется nginx'ом в `/smm/`). `python3 -m http.server 8765` тихо
падает с EADDRINUSE — ссылка вида `http://127.0.0.1:8765/x.mp4` не работает
никогда, не выдавай её.

Единственный правильный способ отдать файл — `publish_kp.py`, он кладёт файл в
nginx-контейнер и печатает публичный URL:

```bash
python3 /root/kp-gen/publish_kp.py /root/.hermes/cache/scratch/short-XXXXXXXXXXX.mp4
# -> https://openclaw70846.hostkey.in/kp/short-xxxxxxxxxxx.mp4
```

Имя слагифицируется в нижний регистр (video ID латиницей не меняется).
Проверять отдачу: `curl -sI <url>` → 200 + `content-type: video/mp4`.

`MEDIA:/abs/path` уместен только как дополнительный показ видео прямо в чате;
«ссылку на скачивание» он не заменяет — Георгий это отдельно поправлял.

## Установка yt-dlp (системный pip не держится)

Пакет, поставленный через `pip install yt-dlp` в активированное окружение Hermes,
исчезает — `yt-dlp: command not found` в следующей сессии. Держать в отдельном venv:

```bash
python3 -m venv /root/.local/venvs/ytdlp
/root/.local/venvs/ytdlp/bin/pip install -q yt-dlp
ln -sf /root/.local/venvs/ytdlp/bin/yt-dlp /usr/local/bin/yt-dlp
yt-dlp --version
```

Для скачивания нужен ffmpeg — он уже есть в PATH (`/root/.hermes/tools/ffmpeg-*/bin`).

## Скачивание

```bash
cd /root/.hermes/cache/scratch
yt-dlp -q --no-warnings \
  -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" \
  --merge-output-format mp4 \
  -o "short-<VIDEO_ID>.%(ext)s" "https://www.youtube.com/shorts/<VIDEO_ID>"
```

Имя файла = `short-<VIDEO_ID>`, а не `youtube_short2`, — по нему видно источник
и не путаются файлы при нескольких ссылках подряд. После скачивания сразу
публиковать через `publish_kp.py`.

`WARNING: No supported JavaScript runtime could be found` — не ошибка, скачивание
проходит (достаётся HLS-поток 616+140). Игнорировать.

## Питфолл: age-gate

Часть видео отдаёт `ERROR: Sign in to confirm your age` — YouTube требует cookies.
Подмена клиента (`--extractor-args "youtube:player_client=tv_simply,web_embedded,android_vr"`)
это **не** лечит. Не выдумывать обходной путь и не отдавать чужой/похожий файл:
сказать Георгию прямо, что это видео требует авторизации, и предложить cookies
(`--cookies-from-browser` или `--cookies`), если он готов их дать.

## Чек-лист перед ответом

1. Файл существует, размер не нулевой (`ls -lh`), длительность читается (`ffprobe`).
2. `publish_kp.py` вернул URL, `curl -sI` по нему даёт 200 и `video/mp4`.
3. Побочные эффекты проверены: `ss -ltnp | grep 8765` — SMM на месте,
   `curl -s -o /dev/null -w '%{http_code}' https://openclaw70846.hostkey.in/smm/` → 200,
   левых `http.server` в процессах нет.
4. В ответе — публичная ссылка (и MEDIA, если уместно), а не путь в scratch.
