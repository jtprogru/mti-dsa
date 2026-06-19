# Лекция 4. Файлы, JSON и работа с БД (`database/sql`)

## Файлы: `os` и `io`

Базовые операции — пакет `os`:

```go
f, err := os.Open("data.txt")          // только чтение
if err != nil {
    return err
}
defer f.Close()
```

```go
f, err := os.Create("out.txt")         // создать/обрезать для записи
f, err := os.OpenFile("log.txt",
    os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)  // дописать в конец
```

`*os.File` реализует `io.Reader`, `io.Writer`, `io.Closer`, `io.Seeker` — все стандартные интерфейсы для I/O. Это значит, файл взаимозаменяем с буфером в памяти, сетевым соединением, gzip-стримом и т. п.

### Прочитать файл целиком

```go
data, err := os.ReadFile("data.txt")    // []byte
// или
text := string(data)
```

```go
if err := os.WriteFile("out.txt", data, 0644); err != nil {
    return err
}
```

Эти функции удобны для маленьких файлов. Для больших — стримите через `bufio.Scanner` или `io.Copy`, иначе уляжется в память.

### Чтение построчно: `bufio.Scanner`

```go
f, _ := os.Open("big.log")
defer f.Close()

scanner := bufio.NewScanner(f)
for scanner.Scan() {
    line := scanner.Text()
    fmt.Println(line)
}
if err := scanner.Err(); err != nil {
    log.Printf("scan: %v", err)
}
```

По умолчанию `Scanner` ограничен буфером 64 КБ — для очень длинных строк увеличьте через `scanner.Buffer(buf, maxSize)`.

### Запись с буферизацией: `bufio.Writer`

```go
f, _ := os.Create("out.txt")
defer f.Close()

w := bufio.NewWriter(f)
defer w.Flush()    // важно! иначе остаток буфера потеряется

for i := 0; i < 1000; i++ {
    fmt.Fprintln(w, i)
}
```

`defer w.Flush()` обязательно, иначе последние записи останутся в буфере.

### Пути и директории: `path/filepath`

```go
import "path/filepath"

// Кросс-платформенный join (на Windows будет '\', на Unix '/')
p := filepath.Join("data", "input", "file.txt")

// Базовое имя и директория
filepath.Base("/etc/hosts")    // "hosts"
filepath.Dir("/etc/hosts")     // "/etc"
filepath.Ext("file.tar.gz")    // ".gz"

// Абсолютный путь
abs, _ := filepath.Abs("./data.txt")

// Обход дерева
filepath.WalkDir(".", func(path string, d fs.DirEntry, err error) error {
    if err != nil {
        return err
    }
    if !d.IsDir() && filepath.Ext(path) == ".go" {
        fmt.Println(path)
    }
    return nil
})
```

`path/filepath` — для путей файловой системы (учитывает OS-разделитель). `path` (без `filepath`) — только для слешевых путей (URL, slash-only).

### `io/fs` — абстракция над файловой системой

С Go 1.16 появился пакет `io/fs` и тип `embed.FS` для встраивания файлов в бинарник:

```go
import "embed"

//go:embed templates/*.html
var templates embed.FS

data, _ := fs.ReadFile(templates, "templates/index.html")
```

Это удобно для статики веб-приложений, миграций SQL, ассетов CLI-утилит — всё попадает прямо в бинарник.

## JSON: `encoding/json`

### Сериализация (Marshal)

```go
type User struct {
    ID       int    `json:"id"`
    Name     string `json:"name"`
    Email    string `json:"email,omitempty"`   // пропустить, если пустое
    password string                              // без тега + lowercase → не сериализуется
}

u := User{ID: 1, Name: "Alice"}
data, _ := json.Marshal(u)
fmt.Println(string(data))
// {"id":1,"name":"Alice"}
```

Или с отступами:

```go
data, _ := json.MarshalIndent(u, "", "  ")
```

### Десериализация (Unmarshal)

```go
data := []byte(`{"id": 1, "name": "Alice"}`)

var u User
if err := json.Unmarshal(data, &u); err != nil {
    return err
}
```

Передаём указатель на структуру (иначе Go не сможет заполнить её, ведь функция получит копию).

### Стримовое (де)кодирование

Для больших данных или работы с `io.Reader`/`io.Writer` — `Encoder`/`Decoder`:

```go
// Запись в файл
f, _ := os.Create("users.json")
defer f.Close()
json.NewEncoder(f).Encode(users)

// Чтение из HTTP-ответа
var users []User
if err := json.NewDecoder(resp.Body).Decode(&users); err != nil {
    return err
}
```

### Распространённые теги

```go
type Event struct {
    ID        string    `json:"id"`
    Type      string    `json:"type"`
    Timestamp time.Time `json:"timestamp"`
    Payload   any       `json:"payload,omitempty"`
    Internal  string    `json:"-"`                    // никогда не сериализуется
}
```

Опции после имени: `omitempty` (пропустить нулевое значение), `string` (закодировать число как строку — полезно для JS, где Number теряет точность на больших int64).

### Кастомные типы и `Marshaler`/`Unmarshaler`

Если нужна нестандартная сериализация — реализуйте интерфейсы:

```go
type Date time.Time

func (d Date) MarshalJSON() ([]byte, error) {
    return []byte(fmt.Sprintf(`"%s"`, time.Time(d).Format("2006-01-02"))), nil
}

func (d *Date) UnmarshalJSON(data []byte) error {
    s := strings.Trim(string(data), `"`)
    t, err := time.Parse("2006-01-02", s)
    if err != nil {
        return err
    }
    *d = Date(t)
    return nil
}
```

Кстати, `"2006-01-02 15:04:05"` — это **референсное время** в Go (моментальное мнемоническое: 01/02 03:04:05PM '06 -0700). Никаких `YYYY-MM-DD`-плейсхолдеров, как в Python.

### Карта вместо структуры

Если структура неизвестна заранее:

```go
var raw map[string]any
json.Unmarshal(data, &raw)
```

Потом — type assertion для доступа к значениям. Это удобно для конфигов и динамических данных, но теряется типобезопасность.

## Работа с БД: `database/sql`

`database/sql` — это **абстракция** над БД. Сам он не «знает» ни одного конкретного диалекта — нужен **драйвер** (отдельный пакет), который регистрирует себя в `database/sql`.

### Драйверы

| БД                | Драйвер                                    |
|-------------------|--------------------------------------------|
| PostgreSQL        | `github.com/jackc/pgx/v5` (или `pq`)        |
| MySQL/MariaDB     | `github.com/go-sql-driver/mysql`            |
| SQLite (cgo)      | `github.com/mattn/go-sqlite3`               |
| SQLite (pure Go)  | `modernc.org/sqlite`                        |

Импорт драйвера почти всегда делается через blank import:

```go
import (
    "database/sql"
    _ "modernc.org/sqlite"
)
```

`_` нужен, потому что мы используем драйвер только через `init()` — он регистрирует себя под именем (`"sqlite"`). Свои API драйвера мы не вызываем.

### Подключение

```go
db, err := sql.Open("sqlite", "./app.db")
if err != nil {
    log.Fatal(err)
}
defer db.Close()

// sql.Open не открывает соединения — это ленивый объект
// проверим, что БД доступна
if err := db.PingContext(ctx); err != nil {
    log.Fatal(err)
}

// настройки пула соединений
db.SetMaxOpenConns(25)
db.SetMaxIdleConns(5)
db.SetConnMaxLifetime(5 * time.Minute)
```

`*sql.DB` — это **пул соединений**, не одно соединение. Его создают на старте программы один раз и шарят между горутинами.

### `Exec`, `Query`, `QueryRow` — три формы запроса

**`Exec` — для DDL и INSERT/UPDATE/DELETE без выборки:**

```go
result, err := db.ExecContext(ctx,
    "INSERT INTO users (name, email) VALUES (?, ?)",
    "Alice", "alice@example.com",
)
if err != nil {
    return err
}
id, _ := result.LastInsertId()
n, _ := result.RowsAffected()
```

**`QueryRow` — одна строка:**

```go
var u User
err := db.QueryRowContext(ctx,
    "SELECT id, name, email FROM users WHERE id = ?", id).
    Scan(&u.ID, &u.Name, &u.Email)
if errors.Is(err, sql.ErrNoRows) {
    return nil, ErrUserNotFound
}
if err != nil {
    return nil, err
}
```

**`Query` — много строк:**

```go
rows, err := db.QueryContext(ctx, "SELECT id, name FROM users WHERE active = ?", true)
if err != nil {
    return nil, err
}
defer rows.Close()

var users []User
for rows.Next() {
    var u User
    if err := rows.Scan(&u.ID, &u.Name); err != nil {
        return nil, err
    }
    users = append(users, u)
}
if err := rows.Err(); err != nil {
    return nil, err
}
return users, nil
```

Не забудьте `defer rows.Close()` и проверку `rows.Err()` после цикла — там копятся ошибки итерации.

### Защита от SQL-инъекций — параметризация

**Всегда** используйте плейсхолдеры (`?` для SQLite/MySQL, `$1, $2, ...` для PostgreSQL):

```go
// ✅ ПРАВИЛЬНО — параметризация
db.QueryRow("SELECT * FROM users WHERE email = ?", email)

// ❌ ОПАСНО — конкатенация
db.QueryRow("SELECT * FROM users WHERE email = '" + email + "'")
```

`database/sql` сам экранирует параметры на уровне протокола БД, инъекции исключены.

### Транзакции

```go
tx, err := db.BeginTx(ctx, nil)
if err != nil {
    return err
}
defer tx.Rollback()   // безопасно: если уже Commit, Rollback просто ничего не делает

if _, err := tx.ExecContext(ctx, "UPDATE accounts SET balance = balance - ? WHERE id = ?", amount, fromID); err != nil {
    return err
}
if _, err := tx.ExecContext(ctx, "UPDATE accounts SET balance = balance + ? WHERE id = ?", amount, toID); err != nil {
    return err
}

return tx.Commit()
```

Идиома `defer tx.Rollback()` сразу после `BeginTx` — обязательная: страхует от ранних `return err`.

### Prepared statements

Для запросов, которые выполняются много раз с разными параметрами:

```go
stmt, err := db.PrepareContext(ctx, "INSERT INTO logs (ts, msg) VALUES (?, ?)")
if err != nil {
    return err
}
defer stmt.Close()

for _, msg := range messages {
    if _, err := stmt.ExecContext(ctx, time.Now(), msg); err != nil {
        return err
    }
}
```

### Миграции

`database/sql` не умеет миграции — используйте сторонние утилиты:

- [`golang-migrate/migrate`](https://github.com/golang-migrate/migrate) — CLI + библиотека, файлы вида `001_init.up.sql` / `001_init.down.sql`;
- [`pressly/goose`](https://github.com/pressly/goose) — то же, чуть проще, миграции можно писать на Go;
- [`atlasgo.io`](https://atlasgo.io/) — современная альтернатива, declarative.

В простых учебных проектах достаточно выполнить DDL прямо в `init`-функции при старте.

### ORM или нет

В Go-сообществе нет такого ORM-доминирования, как Django/SQLAlchemy в Python. Доминирующий подход — писать SQL руками. Есть популярные библиотеки-помощники:

- [`sqlx`](https://github.com/jmoiron/sqlx) — `database/sql` + удобные методы (`Select`, `Get` — заполнить срез/структуру одним вызовом).
- [`sqlc`](https://github.com/sqlc-dev/sqlc) — кодогенерация: пишете SQL, получаете типобезопасные Go-функции.
- [`gorm`](https://gorm.io/) — full-blown ORM, ближе к ActiveRecord/SQLAlchemy. Удобно для прототипов, но скрывает слишком много магии в продакшене.

Хорошее правило: для большинства задач `database/sql` + `sqlx` или `sqlc` хватает, а ORM добавляйте только если действительно нужны.

## Параллель с Python

| Python                                                  | Go                                              |
|---------------------------------------------------------|--------------------------------------------------|
| `open("file.txt").read()`                               | `os.ReadFile("file.txt")`                       |
| `with open(...) as f:`                                  | `f, _ := os.Open(...); defer f.Close()`         |
| `for line in f:`                                        | `bufio.NewScanner(f); for s.Scan() { ... }`     |
| `json.dumps(obj)`                                       | `json.Marshal(obj)`                             |
| `json.loads(s)`                                         | `json.Unmarshal(b, &v)`                         |
| `pathlib.Path`                                          | `path/filepath`                                 |
| `sqlite3.connect(...)`                                  | `sql.Open("sqlite", "...")`                     |
| `cursor.execute("... WHERE id=?", (1,))`                | `db.Query/Exec("... WHERE id=?", 1)`            |
| `conn.commit()` / `conn.rollback()`                     | `tx.Commit()` / `tx.Rollback()`                 |
| SQLAlchemy ORM                                          | `gorm` (если очень нужно)                       |
| Django migrations                                       | `migrate`, `goose`, `atlas`                     |

## Итог

`os` + `io` + `bufio` покрывают весь файловый I/O. `encoding/json` — стандарт для JSON, с возможностью кастомизировать через `Marshaler`/`Unmarshaler`. `database/sql` — низкоуровневый, но удобный слой над любой реляционной БД: пул соединений, параметризация (защита от инъекций), транзакции. ORM — по желанию; идиоматичный путь — писать SQL руками или генерировать через `sqlc`. В следующей лекции — бенчмарки, профилирование и race detector.
