---
name: web-assistant-deploy
description: Skill for deploying web-assistant landing on nginx
---

# Web-ассистент разворачивается на VPS

## Когда использовать
Когда нужно развернуть лендинг или веб-интерфейс на VPS через nginx, отдавая статические файлы, и устранить 502 ошибки, вызванные проксированием на неработающий gateway.

## Порядок действий

### 1. Проверить, что файлы лендинга уже существуют
- `ls -la /usr/share/nginx/html/web-assistant/` — должны быть `index.html`, `landing.html`, `styles.css`, `script.js`.
- Если файлов нет — сначала собрать проект, потом разворачивать.

### 2. Найти, какой контейнер запускает nginx
- `docker ps -a` — найти контейнер с nginx (в этом проекте `nginx-nginx-1`, образ `jonasal/nginx-certbot:6.2.0-nginx1.31.0`).
- Или проверять `ps aux | grep nginx` на хосте.

### 3. Проверить, какая конфигурация сейчас загружает nginx
- `docker exec <container> nginx -T` или `nginx -T` на хосте
- `ls -la /etc/nginx/conf.d/` и `ls -la /etc/nginx/user_conf.d/` в контейнере
- Искать server block для домена `openclaw70846.hostkey.in`.

### 4. Добавить локацию `/web-assistant/` для отдачи статических файлов
В конфиг сервера для домена добавить:
```nginx
location ^~ /web-assistant/ {
    root /usr/share/nginx/html;
    try_files $uri $uri/ =404;
}

location = /web-assistant {
    return 301 https://$host/web-assistant/;
}
```
Важно: эта локация должна идти ДО `location /` (который проксирует на gateway), чтобы nginx выбирал её по префиксу.

### 5. Убедиться, что нет проксирования на неработающий gateway
- Проверить, что `location /` не ведёт на `127.0.0.1:18789` (openclaw gateway) или что gateway запущен.
- Если gateway не нужен — либо удалить этот `location /`, либо заменить на статическую отдачу.

### 6. Перезагрузить nginx
- `docker exec nginx-nginx-1 nginx -t` (валидация)
- `docker exec nginx-nginx-1 nginx -s reload`

### 7. Проверить все URL
```bash
curl -s -o /dev/null -w "HTTP %{http_code}\n" https://openclaw70846.hostkey.in/web-assistant/
curl -s -o /dev/null -w "HTTP %{http_code}\n" https://openclaw70846.hostkey.in/web-assistant/index.html
curl -s -o /dev/null -w "HTTP %{http_code}\n" https://openclaw70846.hostkey.in/web-assistant/landing.html
curl -s -o /dev/null -w "HTTP %{http_code}\n" https://openclaw70846.hostkey.in/web-assistant/styles.css
curl -s -o /dev/null -w "HTTP %{http_code}\n" https://openclaw70846.hostkey.in/web-assistant/script.js
```
Все должны быть 200.

## Проверенные файлы
- Landing: `/usr/share/nginx/html/web-assistant/index.html` (5707 байт)
- Packaged: `/usr/share/nginx/html/web-assistant/landing.html` (12370 байт)
- Styles: `styles.css` (4740 байт)
- Scripts: `script.js` (1661 байт)
- Nginx config: `/etc/nginx/user_conf.d/openclaw70846.hostkey.in.conf` (в контейнере)
- Backup config: `/etc/nginx/user_conf.d/openclaw70846.hostkey.in.conf.bak-20261004-1736`

## Проверенные файлы
- Landing: `/usr/share/nginx/html/web-assistant/index.html` (5707 байт)
- Packaged: `/usr/share/nginx/html/web-assistant/landing.html` (12370 байт)
- Styles: `styles.css` (4740 байт)
- Scripts: `script.js` (1661 байт)
- Nginx config: `/etc/nginx/user_conf.d/openclaw70846.hostkey.in.conf` (в контейнере)
- Backup config: `/etc/nginx/user_conf.d/openclaw70846.hostkey.in.conf.bak-20261004-1736`

## Ключевые правила
- Если nginx проксирует на порт 18789 и 502 — сначала убить/удалить openclaw, либо обойти прокси для нужных путей.
- `location ^~ /path/` приоритетнее `location /`.
- `try_files $uri $uri/ =404;` — нужен, чтобы fallback на 404 работал для несуществующих файлов.
- Локальный тест: `python3 -m http.server 8000 --bind 127.0.0.1` в директории с файлами.

## Production-write process
Для любых изменений в продакшн (nginx config, деплой на сервер, подключение внешних сервисов) применяй строгий порядок:

1. **Сделай числовой diff** — покажи, что изменится, целыми строками.
2. **Объясни, зачем это нужно** — 2–3 репозитория.
3. **Спроси у пользователя подтверждение** перед записью.
4. **Пакетируй связанные правки в один проход** — не делай 5 отдельных запросов на то же изменение.
5. **После применения заново проверяй** все URL/команды, которые были затронуты.

Это предотвращает рассинхрон конфигурации и гарантирует, что inventory-сеть знает о внесённых изменениях до их применения.

## Telegram-бот: интеграция чата
- Токен ботов хранится в `/root/web-assistant/.env` (переменная `TELEGRAM_BOT_TOKEN`).
- Для веба токен выносится в конфиг, который читает клиент (backend) или `chat.yaml` рядом с `chat.js`.
- `chat.js` читает `CHAT_CONFIG.botToken` и отправляет POST в `https://api.telegram.org/bot<TOKEN>/sendMessage`.
- Перед стартом бота сверяй `getMe`: `curl -s "https://api.telegram.org/bot<TOKEN>/getMe"`.
- Если в `chat.js` токен заглушается на `8903101653:***`, это не валидный токен — на сервере будет `404` от Telegram API.
- Перед сменой токена в коде проверяй, что в `.env` так же обновлён. Команда:
  ```bash
  sed -i "s/^TELEGRAM_BOT_TOKEN=.*/TELEGRAM_BOT_TOKEN=<НОВЫЙ_ТОКЕН>/" /root/web-assistant/.env
  cd /root/web-assistant && nohup python3 scripts/bot.py > /tmp/bot.log 2>&1 &
  ```
