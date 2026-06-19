# Лекция 1. Логирование (Logging)

Python предлагает мощную библиотеку логирования в стандартной библиотеке — модуль `logging`. Многие программисты используют `print()` для отладки, но `logging` даёт куда больше возможностей: уровни сообщений, форматирование, конфигурацию через файл/словарь, ротацию файлов, разделение по модулям.

## Уровни логирования

В порядке возрастания «серьёзности»:

| Уровень   | Назначение                                                                       |
|-----------|----------------------------------------------------------------------------------|
| `DEBUG`   | Подробная отладочная информация — обычно отключена в production.                  |
| `INFO`    | Подтверждение, что всё идёт по плану.                                              |
| `WARNING` | Что-то неожиданное, но программа работает.                                         |
| `ERROR`   | Из-за более серьёзной проблемы программа не смогла выполнить какую-то функцию.     |
| `CRITICAL` | Серьёзная ошибка — программа может не выполнять основные функции.                  |

## Самый простой логгер

```python
import logging

logging.basicConfig(filename="sample.log", level=logging.INFO)

logging.debug("DEBUG-сообщение — не попадёт в лог (уровень INFO выше)")
logging.info("INFO-сообщение")
logging.error("Что-то пошло не так")
```

Результат в `sample.log`:

```text
INFO:root:INFO-сообщение
ERROR:root:Что-то пошло не так
```

> По умолчанию логи *добавляются* в файл. Для перезаписи укажите `filemode="w"`.
>
> Часть `root` означает, что сообщение пришло от корневого логгера. Без `basicConfig` логи выводятся на консоль (stderr).

### Логирование исключения

```python
import logging

log = logging.getLogger("ex")

try:
    1 / 0
except ZeroDivisionError:
    log.exception("Деление на ноль!")
    # exception() = error() + traceback в лог
```

## Логирование из нескольких модулей

Хорошая практика — для каждого модуля иметь свой логгер с именем модуля:

```python
# main.py
import logging
import otherMod

def main():
    logging.basicConfig(filename="app.log", level=logging.INFO)
    logging.info("Program started")
    otherMod.add(7, 8)
    logging.info("Done!")

if __name__ == "__main__":
    main()
```

```python
# otherMod.py
import logging

log = logging.getLogger(__name__)

def add(x, y):
    log.info("added %s and %s to get %s", x, y, x + y)
    return x + y
```

Чем больше модулей пишут в лог, тем важнее понимать, *кто* записал сообщение.

## Форматирование лога

Чтобы в логе была понятная информация (время, имя логгера, уровень, сообщение) — настроим `Formatter`:

```python
import logging

log = logging.getLogger("exampleApp")
log.setLevel(logging.INFO)

fh = logging.FileHandler("app.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh.setFormatter(formatter)
log.addHandler(fh)

log.info("Program started")
```

Результат:

```text
2026-06-01 10:30:00,000 - exampleApp - INFO - Program started
```

Полный список атрибутов LogRecord — в официальной документации Python.

## Конфигурация: код, файл или словарь

Существует три способа сконфигурировать логирование:

### 1. Через код (показано выше)

Гибко, но конфигурация смешивается с кодом приложения.

### 2. Через INI-файл (`logging.config.fileConfig`)

```ini
# logging.conf
[loggers]
keys=root,exampleApp

[handlers]
keys=fileHandler,consoleHandler

[formatters]
keys=myFormatter

[logger_root]
level=WARNING
handlers=consoleHandler

[logger_exampleApp]
level=INFO
handlers=fileHandler
qualname=exampleApp
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=WARNING
formatter=myFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
formatter=myFormatter
args=("app.log",)

[formatter_myFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

```python
import logging
import logging.config

logging.config.fileConfig("logging.conf")
log = logging.getLogger("exampleApp")
log.info("Program started")
```

### 3. Через словарь (`logging.config.dictConfig`) — рекомендуется

```python
import logging
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "formatter": "default",
            "filename": "app.log",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "loggers": {
        "exampleApp": {
            "level": "INFO",
            "handlers": ["file", "console"],
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
log = logging.getLogger("exampleApp")
log.info("Program started")
```

Словарную конфигурацию удобно хранить в YAML/JSON и подключать в зависимости от окружения (dev/staging/production).

## Полезные приёмы

### Ротация лог-файлов

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler("app.log", maxBytes=10_000_000, backupCount=5)
# создаёт app.log, app.log.1, app.log.2, ...
```

Также есть `TimedRotatingFileHandler` — ротация по времени (день, час).

### Структурированное логирование (JSON)

Для production-сервисов часто пишут логи в JSON — их легко парсить ELK/Loki/Splunk:

```python
import json
import logging

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        })
```

Существуют готовые библиотеки: `python-json-logger`, `structlog`, `loguru` (последний — современная альтернатива стандартному `logging`).

### Передача параметров — `%` vs `format`

В `log.info("user=%s", user)` строка форматируется *только если* сообщение реально попадёт в лог. Это эффективнее, чем `log.info(f"user={user}")` (последняя всегда форматирует).

## Логирование в Go (`log/slog`)

Начиная с Go 1.21 в стандартную библиотеку добавлен `log/slog` — структурированное логирование:

```go
package main

import (
    "log/slog"
    "os"
)

func main() {
    // JSON-handler для production
    logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
        Level: slog.LevelInfo,
    }))

    logger.Info("запуск", "version", "1.0", "env", "production")
    logger.Error("сбой подключения", "err", "connection refused", "retry", 3)

    // С контекстом — обогащение
    log := logger.With("request_id", "abc-123")
    log.Info("обработка запроса")
    log.Warn("медленный запрос", "duration_ms", 1500)
}
```

Вывод:

```json
{"time":"2026-06-01T10:30:00Z","level":"INFO","msg":"запуск","version":"1.0","env":"production"}
{"time":"2026-06-01T10:30:01Z","level":"ERROR","msg":"сбой подключения","err":"connection refused","retry":3}
{"time":"2026-06-01T10:30:02Z","level":"INFO","msg":"обработка запроса","request_id":"abc-123"}
```

Уровни в `slog`: `Debug`, `Info`, `Warn`, `Error`. По умолчанию текстовый вывод — `slog.NewTextHandler(...)`; для production — JSON.

Старый пакет `log` тоже доступен, но для нового кода предпочтителен `log/slog`.

## Что должно быть в логах

- **Время** (с миллисекундами и временной зоной).
- **Уровень.**
- **Имя логгера** (модуль / компонент).
- **Сообщение** — *короткое и обобщённое* (а не `"User john@example.com tried to log in at 10:30"` — лучше `msg="login attempt"` + `user="john@example.com"`).
- **Контекстные поля** — request_id, user_id, версия приложения и т. д.
- **При ошибках** — стек-трейс (`logger.exception(...)` в Python, `slog.Error(..., "err", err)` в Go).

## Что НЕ должно быть в логах

- **Пароли, токены, ключи** — никогда.
- **Персональные данные** (PII) — без необходимости и без согласия пользователя.
- **Тело больших HTTP-запросов** целиком — пишите только статус, размер и ключевые поля.
- **Кредитки, медицинские данные** — регулируется законами (PCI DSS, HIPAA, GDPR).

## Контрольные вопросы

- Какие уровни логирования есть в Python? Какой использовать по умолчанию в production?
- Зачем создавать отдельный логгер для каждого модуля?
- В чём отличие `logging.basicConfig` от `logging.config.dictConfig`?
- Что такое handler, formatter, logger?
- Что такое структурированное логирование? В чём его преимущество для production-сервисов?
- Чем `log/slog` в Go удобнее «классического» пакета `log`?
- Что *никогда* не следует писать в логи?
