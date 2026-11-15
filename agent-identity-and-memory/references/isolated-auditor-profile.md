# Отдельный профиль-аудитор: проверенные факты

Собрано живыми командами на этой установке при подготовке второго независимого
агента (профиль-аудитор). Перед созданием любого изолированного профиля — читать целиком.

## Дерево именованного профиля (факт, подтверждено `profile create`)

`$HERMES_HOME/profiles/<name>/` содержит:

```
config.yaml      (может отсутствовать сразу — появляется после первого `config set`)
.env             (шаблон из комментариев; ключи профиля пишутся сюда, не в общий .env)
SOUL.md
profile.yaml     (description, description_auto)  ← читает kanban-оркестратор
memories/  skills/  sessions/  cron/  logs/
workspace/  home/  plans/  skins/
.no-bundled-skills   (маркер от `--no-skills`)
```

- `--no-skills` пишет маркер `.no-bundled-skills` — полный каталог bundled-скиллов
  в профиль не приезжает. Для узких ролей (аудитор, воркер) использовать всегда.
- `--description "..."` попадает в `profile.yaml` — это то, что видит kanban.
- Синтаксис и поведение проверяют на временном `HERMES_HOME`, не трогая рабочий профиль:

```bash
V=<installs/<id>/environments/<id>/venv/bin/python>
export HERMES_HOME=/tmp/th-probe/.hermes
$V -m hermes_cli.main profile create probe --no-skills --no-alias --description "throwaway"
$V -m hermes_cli.main -p probe config set model.default "<model>"
```

Изоляция `HERMES_HOME` реально работает: профиль создаётся в заданном каталоге,
`-p <name>` читает только его.

## Ловушка запуска: чем на самом деле стартует Hermes

Не всякий бинарь `hermes` приводит к рабочему CLI. Проверять, чем реально
запущен живой процесс: `ps -o pid,user,args -p <pid>` и `readlink /proc/<pid>/cwd`.

| Путь | Что с ним |
|---|---|
| launcher `<repo>/.hermes/bin/hermes` | вызывает `tools/python -I -c '...'` |
| `tools/python*/bin/python3` | **не видит пакеты проекта** — `ModuleNotFoundError: ruamel` |
| `installs/<id>/environments/<id>/venv/bin/python` | **рабочий**: `python -m hermes_cli.main <cmd>` |
| системный `/usr/bin/python3` | обычно не годится: нет `ruamel`, `prompt_toolkit`, `aiosqlite` |

Правило: для надёжного запуска Hermes-команды брать venv-python из `installs/`
и вызывать `-m hermes_cli.main`. Launcher может разрешиться в неполный интерпретатор.

## Периметр: профиль ≠ песочница

Профиль — это отдельный `HERMES_HOME`, а **не изоляция прав**. На local-бэкенде
агент сохраняет права ОС-пользователя; `terminal.cwd` меняет стартовый каталог,
но не границы доступа; обычный bind mount гарантией изоляции не является.

Что реально изолирует: **непривилегированный ОС-пользователь + права на ФС**.
Проверять границу до создания профиля:

```bash
runuser -u <user> -- ls /root          # ожидаем Permission denied
runuser -u <user> -- ls /srv/allowed   # ожидаем список файлов
```

Главная ловушка: если Hermes живёт внутри `/root` (режим `700 root:root`),
непривилегированный пользователь не дойдёт ни до интерпретатора, ни до venv —
`sudo -u <user> hermes` упадёт на доступе, а не на логике. Решение принять
**до** создания пользователя: вынести рантайм за пределы `/root` (копия в
`/opt/hermes-runtime` + лаунчер в `/usr/local/bin`). Не открывать `x` на `/root`
отдельными ACL ради одного подкаталога — одно `x` частично ломает весь периметр.

## Ограничение инструментов вместо правил в промпте

`platform_toolsets.cli` в `config.yaml` задаёт список toolsets. Набор
`[file, skills, vision, web]` означает: инструмента `terminal` у агента **нет
физически** — это сильнее любых запретов в SOUL.md. Готовый композит `safe`
(web+vision+image_gen) тоже без terminal.

Цена: без terminal агент сам не запустит `git diff`/`grep` — материалы
подаются готовыми файлами. Выбор «file-only vs file+terminal» делать с
пользователем, а не за него.

Полный реестр toolsets и инструментов:
```bash
<venv-python> -c "import sys; sys.path.insert(0,'<repo>'); \
  import tools.delegate_tool_toolsets as t; print(t.TOOLSETS)"
```

## Бэкап: SQLite под Hermes нельзя копировать через `cp`

`state.db`, `kanban.db`, `cron/*.db` живут в WAL-режиме — рядом `.db-wal` и
`.db-shm`, журнал бывает непустым (мегабайты). `cp` даст неконсистентную копию.
Правильный путь — sqlite backup API, без остановки сервисов:

```python
import sqlite3
src = sqlite3.connect('file:/root/.hermes/state.db?mode=ro', uri=True)
dst = sqlite3.connect('/root/<backup-dir>/state.db')
src.backup(dst)
```

Целостность проверяют `PRAGMA integrity_check` → `ok`; на живой базе — через
read-only URI, не копируя. Матрица:

| Объект | Способ | Почему |
|---|---|---|
| `state.db`, `kanban.db`, `cron/*.db` | backup API | WAL непустой |
| `config.yaml`, `memories/`, `SOUL.md`, `skills/`, `cron/jobs.json` | `tar` | статика |
| `/root/kb` | `git bundle` | история + целостность |
| `.env`, `.secrets/` | отдельно, `chmod 600`, не в общий tar | ключи не должны попасть в открытый текст |
| `installs/`, `tools/`, `cache/` | **исключить** | восстановимо |

Каталог бэкапа `0700`, архивы `0600`, `sha256sum` в MANIFEST. Не называть бэкап
выполненным, пока не создан, не проверен распаковкой и не посчитан SHA256.

## Скилл-критик vs профиль-аудитор

| | скилл + delegate_task | отдельный профиль |
|---|---|---|
| Память между вызовами | нет (блок-лист: `memory`) | **есть, своя** |
| Своя история/сессии | нет | **есть** |
| Живёт после процесса | нет | да |
| Своя модель | наследует родителя | **своя** |

Блок-лист детей в `tools/delegate_tool_toolsets.py`: `delegate_task`, `clarify`,
`memory`, `send_message`, `cronjob_manage`; `delegation.max_spawn_depth: 1`
запрещает вложенность.

Субагент со скиллом — консультант с амнезией в рамках одного вызова. Аудитор,
копящий историю замечаний между сессиями, — это профиль. Не обещать первое
вместо второго. Модель аудитора должна **отличаться** от модели родителя —
та же модель даёт те же слепые пятна, и аудит вырождается в самоподтверждение.
Перед назначением модели проверить баланс провайдера (`/api/v1/credits` у
OpenRouter) и доступность конкретной модели: пустой баланс выглядит как
«модель сломалась», а не «нет денег».
