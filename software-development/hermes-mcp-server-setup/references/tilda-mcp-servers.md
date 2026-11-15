# Tilda MCP — два сервера

Tilda имеет два несвязанных между собой MCP-сервера. Ключи не взаимозаменяемы, выбирай по задаче и по тарифу.

| | Официальный (Tilda) | CDP-редактор |
|---|---|---|
| Ключ | `mcp_tilda_...` | `TILDA_PUBLIC_KEY` + `TILDA_SECRET_KEY` |
| Эндпоинт | `https://tilda.ru/api/mcp/` | локальный npm-пакет |
| Запись | да | да (через залогиненный Chrome) |
| Тариф | Personal / Business | любой |
| Инструментов | 235 | 16 |

## Официальный MCP-сервер

**Ключ** создаётся в профиле: Tilda → Профиль → MCP-сервер → Новый ключ. Показывается один раз, показывается с префиксом `mcp_tilda_`. Привязан к конкретному проекту и к тарифу Personal/Business; срок действия при создании задаётся и потом не меняется.

**Эндпоинт:** `https://tilda.ru/api/mcp/`

**Подключение к Hermes:**

```yaml
mcp_servers:
  tilda:
    url: https://tilda.ru/api/mcp/
    headers:
      Authorization: "Bearer mcp_tilda_..."
```

**Что умеет (235 инструментов):** страницы (`add_blank_page`, `delete_page`, `duplicate_page`, `move_page`), Zero Block (`get_zero_block`, `update_zero_block`), публикация (`publish_page`, `unpublish_page`, `page_preview`, `page_undo`, `page_redo`), настройки проекта и страниц, SEO (`update_project_robots_txt`, `update_project_sitemap_xml`, `update_project_redirects_301`), магазин (`store_*`, ~90), Потоки (`feeds_*`, ~25), `upload_image`.

Плюс 5 инструкций-инструментов (`zero_block_instructions`, `vibe_block_generation_instructions`, `vibe_block_design_instructions`, `vibe_block_forms_instructions`, `website_import_instructions`) — сервер просит вызывать их перед соответствующей операцией.

## Грабли

- **Хост `tilda.ru`, не `tilda.cc`.** Ключ привязан к российской версии аккаунта. На `tilda.cc` тот же ключ отдаёт `401 invalid_token` — это выглядит как мёртвый ключ, но ключ в порядке. Проверяй оба хоста.
- **Официальный API (`api.tildacdn.info/v1`) — только чтение.** Любые изменения сайта (Метрика, скрипты в код-блоках, ссылки, публикация) делаются либо через MCP-сервер, либо через браузер.
- **Пакет `@theyahia/tilda-mcp` — read-only.** README обещает создание страниц, блоки, публикацию; в коде — только 7 инструментов чтения (`get_projects`, `get_project_info`, `get_pages`, `get_page`, `get_page_body`, `get_page_export`, `get_page_export_body`). Не планируй запись через него. Он же требует `TILDA_PUBLIC_KEY` + `TILDA_SECRET_KEY`, а не MCP-ключ.
- **Debug-порт Chrome закрыт на профиле по умолчанию** (Chrome 136+ защищает cookies). Запускай Chrome на отдельном профиле: `--remote-debugging-port=9222 --user-data-dir="..."`.
