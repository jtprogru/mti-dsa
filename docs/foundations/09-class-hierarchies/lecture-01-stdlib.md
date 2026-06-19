# Лекция 1. Стандартная библиотека Python и стандартные модули Go (Standard Library)

Стандартная библиотека Python весьма обширна и включает множество инструментов. Она содержит как *встроенные модули* (написанные на C), предоставляющие доступ к системным функциям, так и модули, написанные на Python, предлагающие стандартные решения для множества задач программирования.

В стандартной библиотеке есть несколько видов компонентов:

- *типы данных «ядра» языка* — числа, строки, списки, словари, множества;
- *встроенные функции и исключения* — `print`, `len`, `range`, `ValueError` и др. — не требуют импорта;
- *набор модулей*, импортируемых по необходимости.

Полный справочник: <https://docs.python.org/3/library/index.html>. В Go аналогичный справочник — <https://pkg.go.dev/std>.

## Встроенные функции Python

Не требуют импорта; список можно получить так:

```python
import builtins
print(sorted(name for name in dir(builtins) if not name.startswith("_")))
```

Краткая выборка самых востребованных:

| Функция | Параметры | Результат | Описание |
|---------|-----------|-----------|----------|
| `abs` | `int`/`float` | число | Абсолютная величина. |
| `all` | iterable | `bool` | True, если все элементы истинны. |
| `any` | iterable | `bool` | True, если есть хотя бы один истинный. |
| `bin`, `oct`, `hex` | `int` | `str` | Преобразование в строку (2/8/16-ричную). |
| `chr`, `ord` | `int` ↔ `str` | str/int | Символ по коду / код по символу. |
| `dir` | `[obj]` | `list` | Атрибуты объекта. |
| `divmod` | `a, b` | `(частное, остаток)` |  |
| `enumerate` | iterable [, start=0] | iterator | Пары `(index, item)`. |
| `eval`, `exec` | `str` | any | *Опасно при работе с недоверенным вводом.* |
| `filter`, `map` | func, iterable | iterator | Фильтрация / преобразование. |
| `format` | value, spec | `str` | Форматирование. |
| `getattr`, `setattr`, `hasattr`, `delattr` | obj, name | — | Работа с атрибутами по имени. |
| `globals`, `locals`, `vars` | — | `dict` | Таблицы символов. |
| `hash` | obj | `int` | Хеш объекта. |
| `id` | obj | `int` | Идентификатор. |
| `input` | `[prompt]` | `str` | Чтение строки. |
| `isinstance`, `issubclass` | obj, cls | `bool` | Проверка типа. |
| `iter`, `next` | iterable / iterator | — | Работа с итераторами. |
| `len` | obj | `int` | Длина контейнера. |
| `max`, `min`, `sum` | iterable | any | Минимум, максимум, сумма. |
| `open` | path, mode | file | Открытие файла. |
| `pow` | x, y [, z] | число | `x**y mod z` (с опц. модулем). |
| `print` | *objs | — | Вывод. |
| `range` | start, stop, step | iterator | Числовой диапазон. |
| `repr` | obj | `str` | Формальное представление. |
| `reversed`, `sorted` | iterable | iterator/list | Обратный обход / сортировка. |
| `round` | float, ndigits=0 | float | Округление. |
| `super` | — | proxy | Доступ к родителю. |
| `zip` | *iterables | iterator | Параллельный обход. |

## Стандартная библиотека Python — обзор по модулям

### `sys` — интерпретатор

Содержит функции и константы для взаимодействия с интерпретатором:

- `sys.argv` — аргументы командной строки;
- `sys.platform` — идентификатор платформы (`'linux'`, `'darwin'`, `'win32'`);
- `sys.stdin`, `sys.stdout`, `sys.stderr` — стандартные потоки;
- `sys.version`, `sys.version_info` — версия Python;
- `sys.path` — пути поиска модулей;
- `sys.exit(code)` — завершение программы.

### `os` и `os.path` — взаимодействие с ОС

```python
import os
import os.path

os.environ["HOME"]              # переменная окружения
os.getcwd()                     # текущий каталог
os.listdir(".")                 # содержимое каталога

os.path.join("/tmp/1", "x.txt")  # '/tmp/1/x.txt'
os.path.dirname("/tmp/1/x.txt")  # '/tmp/1'
os.path.basename("/tmp/1/x.txt") # 'x.txt'
os.path.exists("/tmp/1/x.txt")   # False
```

Современная альтернатива — `pathlib`:

```python
from pathlib import Path

p = Path("/tmp/1/x.txt")
print(p.parent)   # /tmp/1
print(p.name)     # x.txt
print(p.exists()) # False
```

### `datetime` — дата и время

Модуль предоставляет классы: `date`, `time`, `datetime`, `timedelta`, `tzinfo`.

```python
from datetime import datetime, timedelta, timezone

now = datetime.now(timezone.utc)
print(now.isoformat())

tomorrow = now + timedelta(days=1)
print(tomorrow.isoformat())
```

### `collections` — специальные контейнеры

```python
from collections import OrderedDict, defaultdict, Counter, deque, namedtuple

# Counter — словарь для подсчёта
words = "to be or not to be".split()
print(Counter(words))  # Counter({'to': 2, 'be': 2, 'or': 1, 'not': 1})

# defaultdict — словарь с default для отсутствующих ключей
groups = defaultdict(list)
for word in words:
    groups[len(word)].append(word)
# {2: ['to', 'be', 'or', 'to', 'be'], 3: ['not']}

# deque — двусвязная очередь
d = deque("abc")
d.appendleft("z")  # deque(['z', 'a', 'b', 'c'])
d.pop()            # 'c'

# namedtuple — кортеж с именованными полями
Point = namedtuple("Point", ["x", "y"])
p = Point(1, 2)
print(p.x, p.y)
```

### `contextlib` — контекстные менеджеры

API менеджера контекста — методы `__enter__` и `__exit__`:

```python
with open("data.txt", "w") as fh:
    fh.write("Hello")
# fh автоматически закрывается
```

Свой менеджер контекста через декоратор:

```python
from contextlib import contextmanager

@contextmanager
def measured(name):
    import time
    t0 = time.perf_counter()
    try:
        yield  # значение для as (необязательно)
    finally:
        print(f"{name}: {time.perf_counter() - t0:.3f}s")

with measured("calc"):
    sum(i*i for i in range(10**6))
```

### `abc` — абстрактные базовые классы

Модуль определяет метакласс `ABCMeta` и декоратор `abstractmethod` для абстрактных классов:

```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

class Circle(Shape):
    def __init__(self, r: float):
        self.r = r
    def area(self) -> float:
        import math
        return math.pi * self.r ** 2

# Shape()  # TypeError: Can't instantiate abstract class
print(Circle(5).area())
```

### `re` — регулярные выражения

Регулярные выражения — мощное средство обработки текста. Шаблоны записывают *сырыми строками* (с префиксом `r`), чтобы избежать двойного экранирования.

```python
import re

text = "A1 c123 a12, b abc (b987)."
pattern = re.compile(r"[a-b][0-9]*")
print(pattern.findall(text))         # ['a12', 'b', 'a', 'b', 'b987']

# поиск и замена
print(re.sub(r"\d+", "*", "abc123def456"))  # abc*def*

# именованные группы
m = re.match(r"(?P<year>\d{4})-(?P<month>\d{2})", "2026-06")
print(m["year"], m["month"])  # 2026 06
```

### `string` — строковые константы

```python
import string
import random

chars = string.ascii_letters + string.digits
print("".join(random.choices(chars, k=8)))  # случайный пароль из 8 символов
```

### Работа с архивами и сжатием

В стандартной библиотеке: `bz2`, `gzip`, `tarfile`, `zipfile`, `zlib`.

```python
from zipfile import ZipFile

# запись
with ZipFile("archive.zip", "w") as z:
    z.writestr("file.txt", "содержимое")

# чтение
with ZipFile("archive.zip", "r") as z:
    for info in z.infolist():
        print(info.filename, info.file_size)
```

### `csv`, `json`

```python
import json
data = {"name": "John", "age": 30}
print(json.dumps(data, ensure_ascii=False))  # '{"name": "John", "age": 30}'

# csv
import csv
with open("data.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["a", "b", "c"])
    writer.writerow([1, 2, 3])
```

### `hashlib` — хеш-функции

```python
import hashlib

h = hashlib.sha256(b"hello world")
print(h.hexdigest())
# 'b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9'
```

Поддерживаются MD5, SHA-1, SHA-2, SHA-3, BLAKE2 и др. *MD5 и SHA-1 не криптостойки* — использовать только для контрольных сумм, не для безопасности.

Для шифрования (симметричного, асимметричного) стандартной библиотеки недостаточно — используют `cryptography` (PyCA).

### Сеть: `urllib`, `http`, `socket`

```python
import urllib.request
import json

with urllib.request.urlopen("https://httpbin.org/json") as resp:
    data = json.load(resp)
    print(data)
```

В реальных проектах для HTTP-клиента чаще используют сторонний `requests` или асинхронный `httpx`.

### `smtplib` — отправка email

```python
import smtplib
from email.message import EmailMessage

msg = EmailMessage()
msg["From"] = "from@example.com"
msg["To"] = "to@example.com"
msg["Subject"] = "Тест"
msg.set_content("Привет!")

with smtplib.SMTP("smtp.example.com", 587) as server:
    server.starttls()
    server.login("login", "password")
    server.send_message(msg)
```

### `sqlite3` — встраиваемая БД

SQLite поставляется вместе с Python — отдельной установки не требует.

```python
import sqlite3

with sqlite3.connect("example.db") as conn:
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stocks
        (date TEXT, symbol TEXT, qty REAL, price REAL)
    """)
    cur.execute(
        "INSERT INTO stocks VALUES (?, ?, ?, ?)",
        ("2026-01-05", "RHAT", 100, 35.14),
    )
    for row in cur.execute("SELECT * FROM stocks"):
        print(row)
```

### `threading`, `multiprocessing`, `asyncio`

- **`threading`** — потоки. Из-за GIL (Global Interpreter Lock) полезность для счётных задач ограничена. Хорош для I/O-bound.
- **`multiprocessing`** — отдельные процессы, обходят GIL, подходят для CPU-bound.
- **`asyncio`** — асинхронный I/O в одном потоке. Лучший выбор для большого количества соединений.

### `unittest` — модульное тестирование

```python
import unittest

class TestMath(unittest.TestCase):
    def test_add(self):
        self.assertEqual(2 + 2, 4)

    def test_div_zero(self):
        with self.assertRaises(ZeroDivisionError):
            1 / 0

if __name__ == "__main__":
    unittest.main()
```

Современная альтернатива — `pytest` (сторонний). Подробнее в [Теме 12](../../ops/12-code-quality-and-testing/index.md).

### `logging` — журналирование

```python
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

logger.info("Запуск")
logger.error("Ошибка %s", "детали")
```

### `subprocess` — запуск внешних процессов

```python
import subprocess

result = subprocess.run(
    ["ls", "-la"],
    capture_output=True, text=True, check=True,
)
print(result.stdout)
```

### `copy` — поверхностное и глубокое копирование

```python
import copy

a = [[1, 2], [3, 4]]
b = copy.copy(a)      # поверхностное
c = copy.deepcopy(a)  # глубокое

a[0][0] = 99
print(a)  # [[99, 2], [3, 4]]
print(b)  # [[99, 2], [3, 4]] — общие вложенные списки
print(c)  # [[1, 2], [3, 4]]  — независимые
```

## Стандартная библиотека Go

В Go стандартная библиотека столь же обширна. Импорт — через путь: `import "fmt"`, `import "net/http"`, `import "encoding/json"`.

### `fmt` — форматированный I/O

```go
import "fmt"

fmt.Println("Hello", "World")
fmt.Printf("число %d, строка %q\n", 42, "test")
s := fmt.Sprintf("результат: %.2f", 3.14159)  // "результат: 3.14"
```

### `os`, `path/filepath` — взаимодействие с ОС

```go
import (
    "fmt"
    "os"
    "path/filepath"
)

cwd, _ := os.Getwd()
fmt.Println(cwd)

home := os.Getenv("HOME")
fmt.Println(home)

p := filepath.Join("/tmp/1", "x.txt")
fmt.Println(filepath.Dir(p))   // /tmp/1
fmt.Println(filepath.Base(p))  // x.txt
```

### `time` — дата, время, таймеры

```go
import "time"

now := time.Now().UTC()
fmt.Println(now.Format(time.RFC3339))

tomorrow := now.Add(24 * time.Hour)
fmt.Println(tomorrow.Format(time.RFC3339))
```

### `encoding/json`, `encoding/csv`

```go
import "encoding/json"

type User struct {
    Name string `json:"name"`
    Age  int    `json:"age"`
}

u := User{Name: "John", Age: 30}
data, _ := json.Marshal(u)
fmt.Println(string(data))  // {"name":"John","age":30}

var u2 User
json.Unmarshal(data, &u2)
```

### `regexp` — регулярные выражения

```go
import "regexp"

re := regexp.MustCompile(`[a-b][0-9]*`)
matches := re.FindAllString("A1 c123 a12, b abc (b987).", -1)
fmt.Println(matches)  // [a12 b a b b987]
```

### `crypto/sha256`, `crypto/hmac`

```go
import (
    "crypto/sha256"
    "fmt"
)

h := sha256.Sum256([]byte("hello world"))
fmt.Printf("%x\n", h)
// b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9
```

### `net/http` — HTTP клиент и сервер из коробки

```go
import (
    "io"
    "net/http"
    "fmt"
)

// клиент
resp, _ := http.Get("https://httpbin.org/json")
defer resp.Body.Close()
body, _ := io.ReadAll(resp.Body)
fmt.Println(string(body))

// сервер
http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
    fmt.Fprintln(w, "Hello, world")
})
// http.ListenAndServe(":8080", nil)
```

### `database/sql` + драйверы

Go предоставляет универсальный интерфейс `database/sql` — драйверы (`github.com/mattn/go-sqlite3`, `github.com/lib/pq`, `github.com/go-sql-driver/mysql`) подключаются отдельно.

```go
import (
    "database/sql"
    _ "github.com/mattn/go-sqlite3"
)

db, _ := sql.Open("sqlite3", "example.db")
defer db.Close()

db.Exec(`CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)`)
db.Exec(`INSERT INTO users(name) VALUES (?)`, "Alice")

rows, _ := db.Query(`SELECT id, name FROM users`)
defer rows.Close()
for rows.Next() {
    var id int
    var name string
    rows.Scan(&id, &name)
    fmt.Println(id, name)
}
```

### `log` / `log/slog` — журналирование

```go
import "log/slog"

slog.Info("запуск", "version", "1.0")
slog.Error("ошибка", "err", "details")
```

`log/slog` (стандартный с Go 1.21) — структурированное логирование, аналог Python `logging` с json-handler.

### `testing` — модульное тестирование

```go
// math_test.go
package mathx

import "testing"

func TestAdd(t *testing.T) {
    if got := 2 + 2; got != 4 {
        t.Errorf("got %d, want 4", got)
    }
}
```

Запуск: `go test ./...`. Подробнее — в [Теме 12](../../ops/12-code-quality-and-testing/index.md).

### `sync`, `context` — конкурентность

- `sync.Mutex`, `sync.RWMutex` — мьютексы;
- `sync.WaitGroup` — ожидание группы горутин;
- `context.Context` — отмена и таймауты для длительных операций.

### Сравнение покрытия стандартной библиотеки

| Задача                  | Python                          | Go                                                          |
|-------------------------|---------------------------------|-------------------------------------------------------------|
| HTTP-клиент             | `urllib.request` / `requests`    | `net/http`                                                  |
| HTTP-сервер             | `http.server` (учебный)         | `net/http` (production-ready)                                |
| JSON                    | `json`                           | `encoding/json`                                              |
| CSV                     | `csv`                            | `encoding/csv`                                               |
| Регулярные выражения    | `re`                             | `regexp`                                                    |
| Криптография            | `hashlib`, `hmac`, `secrets`     | `crypto/*`                                                   |
| SQL                     | `sqlite3` (только SQLite)        | `database/sql` + драйверы                                    |
| Тестирование            | `unittest` (плюс сторонний `pytest`) | `testing` (встроенный, идиоматичный)                     |
| Логирование             | `logging`                        | `log` / `log/slog` (с 1.21)                                  |
| Параллелизм             | `threading`, `multiprocessing`, `asyncio` | горутины + каналы + `sync`                              |
| Дата/время              | `datetime`                       | `time`                                                      |
| Файловая система        | `os`, `pathlib`                  | `os`, `path/filepath`, `io/fs`                               |
| Архивы                  | `zipfile`, `tarfile`             | `archive/zip`, `archive/tar`                                 |
| Сериализация            | `pickle` (Python-only)            | `encoding/gob` (Go-only) или `encoding/json` (универсально)  |

---

## Контрольные вопросы

- Перечислите 5 встроенных функций Python и опишите их назначение.
- Что такое контекстный менеджер? Как создать свой через `contextlib.contextmanager`?
- Чем отличаются `os.path` и `pathlib`?
- Что такое GIL и какие проблемы он создаёт для многопоточности в Python?
- Как организовано HTTP в стандартной библиотеке Go? Почему `net/http` считается production-ready?
- Что такое `database/sql` в Go и почему драйверы поставляются отдельно?
