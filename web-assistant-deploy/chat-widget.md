---
name: chat-widget
description: Web-assistant chat widget — Telegram-bot integration on landing
---

# Web-ассистент — Чат-виджет

## Задача

Добавить на лендинг интерактивный чат-виджет:
1. Клиент пишет запрос и получает ответ от Telegram-бота.
2. Виджет показывает статусы: «Отправка…», «Ответ получен», «Ошибка».
3. Поддержка страницы `/chat` для отдельного чата.
4. Отчёт о файлах и тестах.

## Порядок действий

### 1. Создать файлы чата

```text
output/chat/
├── index.html
├── chat.css
├── chat.js
└── test.html
```

### 2. Страница /chat/index.html

Верстка:
- Заголовок «Чат с Web-Coding Assistant».
- Поле ввода.
- Кнопка отправки.
- Блок сообщений.
- Статус-индикатор.
- Кнопка «Перейти в Telegram».

### 3. CSS (chat.css)

Требования:
- Бокс чата внизу экрана.
- Приветливый дизайн.
- Отображение сообщений от клиента и от бота.
- Учёт мобильных устройств.

### 4. JS (chat.js)

Реализовать:
- `sendMessageToBot(text)` — отправка запроса в Telegram-бота.
- `renderMessage(text, sender)` — отрисовка сообщения.
- `setStatus(text)` — отображение статуса.
- Обработка ошибок сети.
- Очистка формы после отправки.

### 5. Интеграция с ботом

Использовать Telegram API (BOT_TOKEN) для отправки сообщений.

### 6. Тестирование

Локально:
```bash
cd output/chat
python3 -m http.server 8000
# открыть http://localhost:8000/index.html
```

На сервере:
```bash
curl -s -o /dev/null -w '%{http_code}' https://openclaw70846.hostkey.in/web-assistant/chat/index.html
```

### 7. Отчёт

Создать `output/chat/index.output` с:
- описанием файлов,
- инструкцией по проверке,
- ссылкой на страницу,
- результатами тестов.
