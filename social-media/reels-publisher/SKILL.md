---
name: reels-publisher
description: Use when publishing a reel to Instagram, TikTok, YouTube.
---

# Публикация рилсов через Upload-Post

Публикует вертикальные видео в Instagram Reels, TikTok и YouTube Shorts одним вызовом через Upload-Post API (официальные API платформ, без риска бана).

## Когда срабатывать

Пользователь присылает видеофайл (или ссылку на видео) и просит опубликовать: «опубликуй», «запости рилс», «выложи везде», «опубликуй в тикток» и т.п. Если видео есть, но явной команды публиковать нет — уточнить, нужно ли публиковать.

## Процесс (обязательный порядок)

1. **Собрать входные данные**: файл видео (путь после скачивания из ТГ) или URL, текст поста. Если текст не дан — предложить свой вариант и согласовать.
2. **Показать превью публикации и получить подтверждение** (публикация необратима):
   - платформы (по умолчанию все три: instagram, tiktok, youtube);
   - заголовок/подпись (для YouTube title обязателен — макс. 100 символов);
   - время: сразу или по расписанию (`--schedule "2026-08-25T19:00:00" --timezone Europe/Moscow`).
3. **Опубликовать**: запустить `scripts/publish_reel.py` (см. ниже).
4. **Дождаться результата** (скрипт сам поллит статус) и доложить по каждой платформе: ✅ ссылка или ❌ текст ошибки. Если TikTok вернул `fallback_to_inbox: true` — видео НЕ опубликовано, оно лежит черновиком во входящих TikTok, нужно сказать пользователю опубликовать из приложения.
5. Ошибку одной платформы не считать полным провалом: доложить, какие платформы успешны, по упавшей — предложить retry или переавторизацию в кабинете upload-post.com.

## Запуск

```bash
python3 ~/.hermes/skills/social-media/reels-publisher/scripts/publish_reel.py \
  --video /path/to/reel.mp4 \
  --title "Текст подписи" \
  --youtube-title "Заголовок для YouTube" \
  --platforms instagram tiktok youtube \
  --wait
```

- `--video` — локальный файл ИЛИ публичный URL.
- `--title` — общая подпись (Instagram/TikTok caption). TikTok лимит 2200 символов.
- `--youtube-title` — заголовок YouTube (если не задан, берётся первая строка title, макс 100 симв.).
- `--youtube-description` — описание YouTube (по умолчанию = title).
- `--platforms` — подмножество; по умолчанию все три.
- `--schedule "ISO-дата"` + `--timezone Europe/Moscow` — отложенная публикация (вместо --wait).
- `--tiktok-mode draft` — загрузить в TikTok как черновик (MEDIA_UPLOAD): видео попадает во входящие, пользователь публикует руками из приложения. По данным Upload-Post это даёт лучший органический охват. По умолчанию `direct`.
- Instagram Trial Reels: `--platforms instagram --media-type REELS --share-mode TRIAL_REELS_DONT_SHARE_TO_FOLLOWERS` — только пробный рилс без авто-переноса к подписчикам. `TRIAL_REELS_SHARE_TO_FOLLOWERS_IF_LIKED` не использовать, если не нужен авто-выпуск по перформансу. Для обложки: `--cover-image /path/cover.jpg` или `--cover-url https://...`.
- `--ai-generated` — пометить видео как AI-контент на всех платформах (обязательно для реалистичных AI-видео, EU AI Act).
- `--dry-run` — проверить файл/ключ/аккаунты, ничего не публиковать.

Ключ API: `UPLOAD_POST_API_KEY` (переменная окружения или файл `.env`, скрипт читает сам). Профиль Upload-Post обязателен: флаг `--user` или переменная `UPLOAD_POST_USER`.

## Проверка статуса/истории вручную

```bash
KEY=$(grep '^UPLOAD_POST_API_KEY=' .env | cut -d= -f2)   # или из переменной окружения
# статус по request_id
curl -s "https://api.upload-post.com/api/uploadposts/status?request_id=XXX" -H "Authorization: Apikey $KEY"
# история
curl -s "https://api.upload-post.com/api/uploadposts/history" -H "Authorization: Apikey $KEY"
# подключённые аккаунты
curl -s "https://api.upload-post.com/api/uploadposts/users" -H "Authorization: Apikey $KEY"
```

## Питfalls

- **Дневные лимиты**: TikTok 15/день, Instagram 50/день, YouTube 10/день на аккаунт. При 429 — подождать до следующих суток или перенести в расписание.
- **TikTok fallback_to_inbox**: при дневном капе активных пользователей API TikTok пост уходит черновиком во входящие с `success: true` — обязательно проверять флаг `fallback_to_inbox` в результате, иначе соврём, что опубликовано.
- **YouTube title обязателен** — без него весь вызов может отклониться; всегда передавать.
- **Хэштеги**: в TikTok/Instagram работают прямо в caption; в YouTube — только в description (3 штуки показываются над заголовком).
- **Видео**: вертикаль 9:16, mp4 h264; Upload-Post сам транскодирует (`video_was_transcoded` в ответе — норма).
- **Новые аккаунты** — прогрев: первые 2–4 недели не более 1–3 постов/день, иначе платформы режут охваты.
- **scheduled_date** всегда в будущем; с timezone=Europe/Moscow время московское.
- **Idempotency**: скрипт шлёт `Idempotency-Key` (sha1 файла+title) — повторный запуск после таймаута не создаст дубль.
- **Async PENDING**: Upload-Post может ответить `processing` после `--wait`-таймаута. Если в summary `PENDING` (exit 3) — это НЕ провал: сначала дождаться и проверить `/api/uploadposts/status?request_id=...`, только потом mark-published или mark-failed.
- **Никогда не писать `upload-post://<platform>/<request_id>` как URL поста.** Это внутренний id запроса, а не ссылка. HTTP-ответ означает только «задача поставлена в очередь»; настоящий `post_url` и `platform_post_id` появляются в `/api/uploadposts/status` ПОСЛЕ завершения. Если записать успех сразу — панель соврёт: пост может упасть через минуту, а оператор не узнает. Ждать вердикта: `status=completed` + `success=true` + непустой `post_url`. `success=false` с `error_message` — это провал, даже если HTTP был 200.
- **Threads подключается БЕЗ бизнес-аккаунта** (в отличие от Instagram: там нужен Business/Creator + страница Facebook). Лимит щедрый: 250 постов/сутки против 25 у Instagram. Подпись — параметр `threads_title` (не `title`), лимит 500 символов.
- Не публиковать без явного подтверждения пользователя на превью — посты публичны и необратимы (удаление только руками в приложениях).

## Аналитика (если спросит просмотры)

GET `https://api.upload-post.com/api/uploadposts/analytics?platform=instagram` (и tiktok/youtube) с тем же заголовком — followers/impressions/reach; per-post метрики — по media_id.
