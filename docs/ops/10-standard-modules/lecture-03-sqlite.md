# Лекция 3. SQLite (SQLite Database)

**SQLite** — это встраиваемая кроссплатформенная БД, которая поддерживает достаточно полный набор команд SQL. По умолчанию БД — это *один файл* в кроссплатформенном формате.

## Чем интересна SQLite

- **Везде.** SQLite — самая распространённая БД в мире. Она встроена в смартфоны (iOS и Android используют её для большинства приложений), браузеры, операционные системы, медиаплееры.
- **Надёжность.** Перед выпуском версии проходит около 2 млн автоматических тестов, покрытие кода тестами — 100 %.
- **Минимальный, но полный набор SQL.** Старается соответствовать SQL-92 без сложных штук, но добавляет полезные удобства.
- **Один файл — вся база.** Легко переносить, копировать, версионировать.
- **In-memory режим.** База может жить полностью в RAM — удобно для тестов и кеша.
- **Множество встроенных функций SQL:** <https://www.sqlite.org/lang_corefunc.html>.

### Чего нет в SQLite

- Нельзя удалить или изменить столбец *классически* (с версии 3.35+ есть `ALTER TABLE DROP COLUMN`; `ALTER COLUMN` всё ещё нет).
- Поддержка foreign key есть, но по умолчанию *отключена* (нужно включать через `PRAGMA foreign_keys = ON`).
- Нет хранимых процедур.
- Тип столбца не определяет тип хранимого значения *жёстко* — в любой столбец можно занести почти любое значение (так называемая *type affinity*).

## SQLite в многопоточных приложениях

SQLite может быть собран в разных режимах:

- **Single-threaded** (без поддержки потоков) — максимальная скорость, но нельзя использовать из нескольких потоков.
- **Multi-thread** (`SQLITE_OPEN_NOMUTEX`) — нельзя одновременно использовать *одно и то же* соединение из нескольких потоков, но разные соединения — можно. Обычный режим.
- **Serialized** (`SQLITE_OPEN_FULLMUTEX`) — потоки могут как угодно обращаться к одному соединению; вызовы строго последовательны.

Большинство дистрибутивов SQLite собраны в `Multi-thread` режиме.

## База данных в памяти

Если при открытии передать имя файла как `":memory:"`, SQLite создаст соединение к новой БД в памяти. По логике использования — неотличимо от файловой.

Полезно для тестов и кеширования часто используемых данных.

## SQLite в Python (`sqlite3`)

Python имеет встроенную поддержку SQLite — ничего устанавливать не нужно:

```python
import sqlite3
```

> Python может работать и с другими СУБД через сторонние пакеты:
>
> | СУБД | Пакет |
> |------|-------|
> | PostgreSQL | `psycopg` (v3) / `psycopg2` |
> | MySQL/MariaDB | `mysql.connector` / `PyMySQL` |
> | ODBC | `pyodbc` |
> | Универсальный ORM | `SQLAlchemy` |

### Соединение и курсор

```python
import sqlite3

with sqlite3.connect("test.sqlite") as conn:
    cursor = conn.cursor()
    # ... работа с базой
# при выходе из `with` соединение коммитится и закрывается
```

### Чтение

```python
cursor.execute("SELECT name FROM artist ORDER BY name LIMIT 3")
rows = cursor.fetchall()
print(rows)
# [('A Cor Do Som',), ('Aaron Copland & London Symphony Orchestra',), ('Aaron Goldberg',)]
```

> После `.fetchall()` повторный вызов вернёт пустой список — данные «забраны». Нужно повторить `.execute()`.

### Запись

```python
cursor.execute("INSERT INTO artist VALUES (NULL, 'A Aagrh!')")
conn.commit()  # обязательно для записи (или используйте `with conn:`)
```

### Многострочные запросы

```python
cursor.execute("""
    SELECT name
    FROM artist
    ORDER BY name
    LIMIT 3
""")
```

### Несколько запросов одним вызовом

`cursor.execute()` принимает *один* запрос за раз. Для нескольких — `cursor.executescript()`:

```python
cursor.executescript("""
    INSERT INTO artist VALUES (NULL, 'A Aagrh!');
    INSERT INTO artist VALUES (NULL, 'A Aagrh-2!');
""")
```

### Подстановка значений — параметризованные запросы

> **Важно!** Никогда не используйте конкатенацию строк (`+`) или f-строки для подстановки значений в SQL — это открывает дверь *SQL-инъекциям*.

Правильно — через параметры:

```python
# позиционная подстановка (плейсхолдеры ?)
cursor.execute("SELECT name FROM artist ORDER BY name LIMIT ?", (3,))

# именованная подстановка
cursor.execute("SELECT name FROM artist ORDER BY name LIMIT :limit",
               {"limit": 3})
```

### Массовая вставка

```python
new_artists = [
    ("A Aagrh!",),
    ("A Aagrh-2!",),
    ("A Aagrh-3!",),
]
cursor.executemany("INSERT INTO artist VALUES (NULL, ?)", new_artists)
```

### Получение по одной строке

```python
cursor.execute("SELECT name FROM artist ORDER BY name LIMIT 3")
print(cursor.fetchone())  # ('A Cor Do Som',)
print(cursor.fetchone())  # ('Aaron Copland...',)
print(cursor.fetchone())  # None — когда строки закончились
```

### Курсор как итератор

```python
for row in cursor.execute("SELECT name FROM artist ORDER BY name LIMIT 3"):
    print(row)
```

### Row factory — словарный доступ к строкам

По умолчанию строки — кортежи. Можно настроить доступ по имени колонки:

```python
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
for row in cursor.execute("SELECT id, name FROM artist LIMIT 3"):
    print(row["name"], row["id"])
```

## SQLite в Go (`database/sql` + драйвер)

Go использует универсальный интерфейс `database/sql`. Драйверы подключаются отдельно — для SQLite популярны `github.com/mattn/go-sqlite3` (через CGO) и `modernc.org/sqlite` (pure Go).

```go
package main

import (
    "database/sql"
    "fmt"
    "log"

    _ "github.com/mattn/go-sqlite3"
)

func main() {
    db, err := sql.Open("sqlite3", "test.sqlite")
    if err != nil {
        log.Fatal(err)
    }
    defer db.Close()

    // Создание таблицы
    _, err = db.Exec(`
        CREATE TABLE IF NOT EXISTS artist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    `)
    if err != nil {
        log.Fatal(err)
    }

    // Вставка с параметрами
    _, err = db.Exec(`INSERT INTO artist(name) VALUES (?)`, "A Aagrh!")
    if err != nil {
        log.Fatal(err)
    }

    // Чтение
    rows, err := db.Query(`SELECT id, name FROM artist ORDER BY name LIMIT ?`, 3)
    if err != nil {
        log.Fatal(err)
    }
    defer rows.Close()

    for rows.Next() {
        var id int
        var name string
        if err := rows.Scan(&id, &name); err != nil {
            log.Fatal(err)
        }
        fmt.Println(id, name)
    }
}
```

### Транзакции в Go

```go
tx, err := db.Begin()
if err != nil { log.Fatal(err) }

if _, err := tx.Exec(`INSERT INTO artist(name) VALUES (?)`, "X"); err != nil {
    tx.Rollback()
    log.Fatal(err)
}
if _, err := tx.Exec(`INSERT INTO artist(name) VALUES (?)`, "Y"); err != nil {
    tx.Rollback()
    log.Fatal(err)
}

if err := tx.Commit(); err != nil {
    log.Fatal(err)
}
```

## Безопасность: SQL-инъекции

**SQL-инъекция** — внедрение злоумышленником SQL-кода через пользовательский ввод. Классический пример:

```python
# ОПАСНО — никогда так не делайте
name = input("Имя: ")
cursor.execute(f"SELECT * FROM users WHERE name = '{name}'")
```

Если пользователь введёт `' OR '1'='1' --`, запрос превратится в:

```sql
SELECT * FROM users WHERE name = '' OR '1'='1' --'
```

Который вернёт всех пользователей. Или хуже — введёт `'; DROP TABLE users; --`.

**Правильно** — параметризованные запросы:

```python
# Python
cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
```

```go
// Go
rows, err := db.Query(`SELECT * FROM users WHERE name = ?`, name)
```

В обоих случаях драйвер сам корректно экранирует значение — инъекция невозможна.

## Динамическая структура таблицы

SQLite не поддерживает изменение типа поля, но добавлять таблицы и поля можно. Простая функция, которая по описанию структуры создаёт/добавляет таблицы и поля:

```python
import sqlite3

def ensure_schema(cursor: sqlite3.Cursor, schema: list[dict]) -> None:
    """Проверяет структуру, добавляет таблицы и поля, если их нет."""
    for table in schema:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table["name"],),
        )
        if cursor.fetchone() is None:
            # таблица отсутствует — создаём
            cols = ", ".join(
                f"{f['name']} {f['type']} {f.get('add', '')}".strip()
                for f in table["fields"]
            )
            cursor.execute(f"CREATE TABLE {table['name']} ({cols})")
        else:
            # таблица есть — добавляем недостающие поля
            cursor.execute(f"PRAGMA table_info({table['name']})")
            existing = {row[1] for row in cursor.fetchall()}
            for field in table["fields"]:
                if field["name"] not in existing:
                    cursor.execute(
                        f"ALTER TABLE {table['name']} "
                        f"ADD COLUMN {field['name']} {field['type']} "
                        f"{field.get('add', '')}".strip()
                    )

# использование
schema = [
    {
        "name": "users",
        "fields": [
            {"name": "id", "type": "INTEGER", "add": "PRIMARY KEY AUTOINCREMENT"},
            {"name": "email", "type": "TEXT", "add": "UNIQUE NOT NULL"},
            {"name": "created_at", "type": "INTEGER"},
        ],
    },
]

with sqlite3.connect("app.sqlite") as conn:
    ensure_schema(conn.cursor(), schema)
```

> Для серьёзных приложений лучше использовать систему *миграций* (Alembic для SQLAlchemy в Python, `golang-migrate` или `goose` в Go). Они отслеживают версию схемы и применяют изменения поэтапно.

## ORM или сырой SQL?

- **Сырой SQL** (через `sqlite3` / `database/sql`) — полный контроль, минимум накладных расходов. Подходит для небольших проектов и DBA-задач.
- **ORM** — *Object-Relational Mapping* — отображение строк БД на объекты языка. Удобно для CRUD, миграций, валидации. В Python — *SQLAlchemy* и *Django ORM*; в Go — *GORM*, *ent*, *sqlc*.

Часто используют гибрид: ORM для CRUD, сырой SQL для сложных аналитических запросов.

## Контрольные вопросы

- Какие особенности отличают SQLite от «больших» СУБД (PostgreSQL, MySQL)?
- Что такое параметризованный запрос? Почему он защищает от SQL-инъекций?
- В чём отличие `cursor.execute()` от `cursor.executemany()` и `cursor.executescript()`?
- Зачем нужен метод `conn.commit()`?
- Что такое транзакция? Когда применять `rollback`?
- Что такое ORM? В каких случаях полезен сырой SQL?
- Как настроены потоки в SQLite (single-threaded / multi-thread / serialized)?
