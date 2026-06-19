# Лекция 1. Модули, пакеты и управление зависимостями

Один `.py`-файл умещает простой скрипт, но в реальных проектах кода — сотни и тысячи файлов. Как организовать его, как делиться им и как подключать чужие готовые решения — об этом сегодня.

План:

- что такое модуль и пакет в Python и в Go;
- идиома `if __name__ == "__main__"`;
- как Python ищет модули (`sys.path`);
- установка сторонних пакетов: `pip` и современный `uv`;
- управление зависимостями: `pyproject.toml`, `uv.lock`, `requirements.txt`;
- виртуальные окружения;
- параллель: `go mod`, `go get`, `go.sum`;
- FFI: вызов DLL/`.so` из Python (`ctypes`) и из Go (`cgo`).

## Модули в Python

**Модуль** — это любой Python-файл. Имя модуля = имя файла без `.py`.

```python
# math_utils.py
def square(x: int) -> int:
    return x * x

PI = 3.14159
```

Использование в другом файле:

```python
# main.py
import math_utils

print(math_utils.square(5))
print(math_utils.PI)


# или импортировать конкретные имена
from math_utils import square, PI

print(square(5))


# или с псевдонимом
import math_utils as mu
from math_utils import square as sq
```

### Идиома `if __name__ == "__main__"`

В Python все модули равноправны: нет «главного» файла. Любой можно и импортировать, и запустить как точку входа.

Чтобы код выполнялся **только при запуске напрямую**, а не при импорте, используют:

```python
def main() -> None:
    print("Запущено напрямую")


if __name__ == "__main__":
    main()
```

Когда модуль импортируется, в нём `__name__` равно его имени (`"math_utils"`). Когда модуль запускают через `python math_utils.py` — `__name__` становится `"__main__"`.

Зачем это нужно:

- модуль может быть и библиотекой, и CLI-утилитой одновременно;
- тесты импортируют код, но не должны его запускать;
- избегаем побочных эффектов при импорте.

## Пакеты

**Пакет** — каталог с модулями. Раньше требовалось наличие файла `__init__.py` (можно пустого) — он сообщал интерпретатору, что каталог — это пакет. Современный Python поддерживает **неявные пакеты** (без `__init__.py`), но `__init__.py` всё равно используют для экспорта публичного API.

```
my_app/
├── __init__.py          # делает каталог пакетом
├── __main__.py          # python -m my_app выполнит этот файл
├── core.py
├── api/
│   ├── __init__.py
│   ├── client.py
│   └── server.py
└── utils/
    ├── __init__.py
    └── strings.py
```

Импорты внутри пакета:

```python
# my_app/api/client.py
from my_app.core import some_function          # абсолютный импорт
from ..utils.strings import slugify            # относительный
from .server import Server                      # относительный, тот же подкаталог
```

> **Стиль:** в библиотеках предпочитают абсолютные импорты — они яснее. Относительные удобны при перемещении подпакетов.

### `__init__.py` как публичное API

```python
# my_app/__init__.py
from .core import some_function
from .api.client import Client

__all__ = ["some_function", "Client"]
__version__ = "1.2.3"
```

Теперь пользователи могут писать `from my_app import Client` вместо `from my_app.api.client import Client`. Это инкапсулирует внутреннюю структуру — вы можете её менять, не ломая клиентский код.

### `__main__.py` — точка входа пакета

Если в пакете есть `__main__.py`, его можно запустить через `python -m my_app`:

```python
# my_app/__main__.py
from my_app.core import main

if __name__ == "__main__":
    main()
```

## Как Python ищет модули: `sys.path`

При `import foo` Python ищет файл `foo.py` (или каталог `foo/__init__.py`) в:

1. Каталоге, где находится скрипт-точка-входа.
2. Каталогах из переменной окружения `PYTHONPATH`.
3. **Site-packages** текущего интерпретатора (там лежат установленные пакеты).
4. Каталогах из `sys.path` (можно посмотреть и изменить из кода).

```python
import sys
for p in sys.path:
    print(p)
```

Если модуль не найден — `ModuleNotFoundError`.

> Хак «добавить путь в `sys.path`» — антипаттерн. Используйте либо правильную структуру пакета (`pyproject.toml`), либо переменную `PYTHONPATH`.

## Виртуальные окружения

Когда вы устанавливаете зависимости системно (`pip install requests`), они попадают в общую кучу. Разные проекты требуют разных версий, и через какое-то время начинаются конфликты.

**Виртуальное окружение** (virtualenv, venv) — изолированная папка с собственным интерпретатором и собственными пакетами. У каждого проекта — свой `.venv`.

### Стандартный способ: `venv` + `pip`

```bash
# Создание
python -m venv .venv

# Активация
source .venv/bin/activate          # macOS / Linux
.venv\Scripts\activate             # Windows PowerShell

# Установка зависимостей
pip install requests httpx

# Деактивация
deactivate
```

После активации `python` и `pip` указывают на `.venv/bin/python` и `.venv/bin/pip` — все установки попадают в `.venv`.

### Современный способ: `uv`

[`uv`](https://docs.astral.sh/uv/) — быстрый менеджер пакетов и окружений на Rust от Astral. Заменяет `pip`, `venv`, `pipx`, `poetry` одним инструментом. Установка одной командой, операции в 10–100× быстрее.

```bash
# Установка uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Создать проект (генерирует pyproject.toml, .venv, .python-version)
uv init my-project
cd my-project

# Добавить зависимость (автоматически создаст .venv, если нужно)
uv add requests httpx

# Удалить
uv remove httpx

# Синхронизировать окружение по lock-файлу
uv sync

# Запустить команду в окружении
uv run python script.py
uv run pytest

# Установить конкретную версию Python
uv python install 3.14
```

`uv` создаёт два файла:

- **`pyproject.toml`** — то, что вы декларируете: какие версии хотите.
- **`uv.lock`** — точные разрешённые версии всех зависимостей и их зависимостей. Коммитится в git.

### Pip + requirements.txt (legacy)

Старый способ — поддерживать список:

```text
# requirements.txt
requests>=2.31.0
httpx==0.27.0
```

```bash
pip install -r requirements.txt
pip freeze > requirements.txt
```

Минусы: `requirements.txt` не отличает «прямые» зависимости от «транзитивных», нет lock-файла, нет метаданных проекта. В новых проектах используйте `pyproject.toml` + `uv` (или `poetry`/`pdm`).

## `pyproject.toml` — манифест проекта

Стандарт PEP 621 для описания Python-проекта. Минимальный пример:

```toml
[project]
name = "my-project"
version = "0.1.0"
description = "Краткое описание"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.31",
    "httpx",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "ruff",
    "mypy",
]

[project.scripts]
my-cli = "my_project.__main__:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100

[tool.pytest.ini_options]
addopts = "-ra"
```

Один файл заменяет старые `setup.py`, `setup.cfg`, `requirements.txt`, конфиги линтеров. Современные инструменты (`pip`, `uv`, `poetry`, `hatch`, `pdm`) его понимают.

## Пакетный индекс PyPI

[PyPI](https://pypi.org) — центральный репозиторий Python-пакетов. Любой может опубликовать туда пакет (с помощью `uv publish` или `twine`), любой может установить (`uv add foo` / `pip install foo`).

### Поиск пакетов

- [pypi.org](https://pypi.org) — поиск + страницы пакетов;
- [libraries.io](https://libraries.io) — кросс-экосистемный поиск;
- [Awesome Python](https://github.com/vinta/awesome-python) — кураторский список.

### Что проверить перед использованием стороннего пакета

- **актуальность** — недавние коммиты, активные issue;
- **лицензия** — совместима ли с вашим проектом (MIT/BSD/Apache — почти всегда да; GPL — внимательно);
- **зависимости** — не тянет ли он 50 транзитивных;
- **тесты и CI** — есть ли badge с покрытием;
- **популярность** — звёзды на GitHub, количество загрузок (`pypistats`).

## Модули и пакеты в Go

В Go организация кода устроена иначе.

### Пакеты

**Пакет** — каталог с `.go`-файлами, у которых одинаковая декларация `package xxx` в начале:

```go
// math_utils/math_utils.go
package mathutils

const PI = 3.14159

func Square(x int) int {
    return x * x
}
```

```go
// main.go
package main

import "example.com/myapp/mathutils"

func main() {
    fmt.Println(mathutils.Square(5))
    fmt.Println(mathutils.PI)
}
```

Правила:

- имена с **заглавной буквы** (`Square`, `PI`) — **экспортируются**, видны из других пакетов;
- с маленькой (`square`, `pi`) — приватны, видны только внутри пакета;
- по соглашению имя пакета — последний компонент пути (`mathutils`).

### Модули

**Модуль** в Go — независимая единица версионирования. Описывается файлом `go.mod` в корне:

```text
module example.com/myapp

go 1.23

require (
    github.com/spf13/cobra v1.8.0
    golang.org/x/sync v0.5.0
)
```

Для версионирования всех зависимостей создаётся `go.sum` — аналог `uv.lock`/`Cargo.lock`.

### `go get`, `go mod`

```bash
# Инициализация модуля
go mod init example.com/myapp

# Добавить зависимость (можно указать версию)
go get github.com/spf13/cobra@latest
go get github.com/spf13/cobra@v1.8.0

# Обновить
go get -u ./...

# Подчистить лишние зависимости
go mod tidy

# Vendoring — сохранить копии зависимостей в vendor/
go mod vendor
```

### Точка входа

```go
// cmd/myapp/main.go
package main

import "example.com/myapp/api"

func main() {
    api.Run()
}
```

`package main` + функция `main()` = исполняемый бинарник. Сборка:

```bash
go build ./cmd/myapp
go install ./cmd/myapp   # копирует бинарь в $GOPATH/bin
go run ./cmd/myapp       # сборка + запуск
```

В Go нет `__name__ == "__main__"` — функция `main` либо есть, либо нет. Пакет `main` отделён от обычных пакетов.

## Сравнение Python ↔ Go

| Аспект | Python | Go |
|--------|--------|-----|
| Единица кода | модуль (`.py`-файл) | пакет (`.go`-файлы в одном каталоге) |
| Группа модулей | пакет (каталог с `__init__.py`) | модуль (каталог с `go.mod`) |
| Точка входа | любой модуль через `if __name__ == "__main__"` | `package main` + `main()` |
| Менеджер зависимостей | `uv` / `pip` / `poetry` | `go mod` (встроен) |
| Манифест проекта | `pyproject.toml` | `go.mod` |
| Lock-файл | `uv.lock` / `poetry.lock` | `go.sum` |
| Виртуальное окружение | `.venv` (нужно) | не нужно (всё пакетно изолировано) |
| Реестр пакетов | PyPI | proxy.golang.org (фактически — GitHub/GitLab) |
| Версионирование | semver, диапазоны (`>=2.31`) | semver, мажорная версия в пути (`/v2`) |
| Поиск имени | `sys.path` | `GOPATH` + module-aware режим |
| Vendoring | `pip download` (редко) | `go mod vendor` (часто) |

## Использование сторонних библиотек: FFI

Иногда нужно вызвать функцию из C-библиотеки (системная DLL, .so, .dylib). Это называется **Foreign Function Interface** (FFI).

### Python: `ctypes`

`ctypes` входит в стандартную библиотеку. Позволяет вызывать функции из C-совместимых DLL без компиляции.

```python
import ctypes
import platform

# Загрузить системную библиотеку
if platform.system() == "Windows":
    user32 = ctypes.WinDLL("user32.dll")
    # MessageBoxW (Unicode) принимает (hwnd, text, title, type)
    user32.MessageBoxW(0, "Привет из Python!", "Заголовок", 0)
elif platform.system() == "Darwin":
    libc = ctypes.CDLL("libc.dylib")
    print(libc.getpid())
else:  # Linux
    libc = ctypes.CDLL("libc.so.6")
    print(libc.getpid())
```

### Описание сигнатур

Чтобы передавать сложные типы, нужно описать сигнатуру функции:

```python
import ctypes

shell32 = ctypes.WinDLL("shell32.dll")
SHGetFolderPath = shell32.SHGetFolderPathW

SHGetFolderPath.argtypes = (
    ctypes.c_void_p,   # hwnd
    ctypes.c_int,      # csidl
    ctypes.c_void_p,   # hToken
    ctypes.c_uint32,   # dwFlags
    ctypes.c_wchar_p,  # pszPath (буфер)
)
SHGetFolderPath.restype = ctypes.c_uint32

CSIDL_LOCAL_APPDATA = 0x001C
MAX_PATH = 260

buf = ctypes.create_unicode_buffer(MAX_PATH)
if SHGetFolderPath(0, CSIDL_LOCAL_APPDATA, 0, 0, buf) == 0:
    print(buf.value)
```

Альтернативы:

- **`cffi`** — более удобный API, парсит C-заголовки.
- **`PyO3`** — для написания нативных расширений на Rust.

### Go: `cgo`

Go умеет включать C-код прямо в исходник через директиву `import "C"`:

```go
/*
#include <stdio.h>
#include <stdlib.h>

void say_hello(const char* name) {
    printf("Hello, %s!\n", name);
}
*/
import "C"

import "unsafe"

func main() {
    name := C.CString("World")
    defer C.free(unsafe.Pointer(name))
    C.say_hello(name)
}
```

`cgo` мощный, но имеет цену:

- сборка требует C-компилятора;
- кросс-компиляция усложняется;
- потери производительности на каждом вызове через границу Go ↔ C;
- сложнее отладка.

В Go-сообществе традиционно избегают `cgo`, когда можно — нативные библиотеки Go покрывают почти всё.

## Сравнение FFI

| Аспект | Python (`ctypes`) | Go (`cgo`) |
|--------|-------------------|------------|
| Доступ к C-API | да | да |
| Нужен ли компилятор | нет | да |
| Производительность | медленнее (на каждый вызов) | быстрее, но всё равно граница |
| Безопасность | type-only (можно «выстрелить») | type-only |
| Кросс-компиляция | лёгкая | усложняется |
| Альтернатива | `cffi`, нативные модули, Rust+PyO3 | переписать на pure Go |

## Типичные подводные камни

- **«Имя файла совпадает с системным модулем»** — назвать свой файл `email.py` и попытаться `import email` — Python загрузит ваш. То же для `random.py`, `string.py`.
- **Циркулярные импорты** — модуль A импортирует B, B импортирует A. Лечится либо вынесением общего кода в третий модуль, либо переносом импорта внутрь функции.
- **Изменение `sys.path` в коде** — работает, но мешает рефакторингу. Используйте `pyproject.toml`.
- **Глобальное состояние при импорте** — код вне функций выполняется ОДИН раз при импорте. Это удобно для констант, опасно для эффектов.
- **Несовместимость версий** — `requests==2.0` несовместим с `requests==2.31`. Lock-файл — единственный надёжный способ контроля.

---

## Контрольные вопросы

- Чем модуль отличается от пакета в Python?
- Зачем нужен `if __name__ == "__main__"`, и что без него произойдёт при импорте?
- Что делает `__init__.py` и можно ли без него обойтись в Python 3?
- Почему в одном Python-проекте обычно нужно своё виртуальное окружение?
- Чем `uv` лучше связки `venv + pip + requirements.txt`?
- Что такое `pyproject.toml` и какие файлы он заменяет?
- Зачем нужен `uv.lock` / `go.sum`, и зачем его коммитить в git?
- Чем `import` в Go отличается от `import` в Python (имена, пути, версии)?
- В каких случаях стоит прибегать к FFI (`ctypes` / `cgo`), а в каких этого лучше избегать?
- Что произойдёт, если назвать файл `string.py` и попытаться `import string`?
