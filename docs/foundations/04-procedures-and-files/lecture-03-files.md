# Лекция 3. Работа с файлами и форматами данных

В каждой программе чуть сложнее «hello world» данные нужно как-то сохранять и загружать: настройки пользователя, входные параметры, результаты обработки, логи. В этой лекции — как делать это в Python и в Go.

План:

- типы файлов и способы доступа;
- открытие, чтение, запись текстовых и бинарных файлов;
- работа с файловой системой (`os` / `pathlib` / `os`/`io/fs`);
- популярные форматы данных: CSV, JSON, YAML, TOML, INI;
- сериализация Python-объектов (`pickle`).

## Типы файлов

Файлы условно делят на три категории:

| Тип | Особенности |
|-----|-------------|
| **Текстовые** | Нет фиксированной длины записи. Структура — строки, разделённые переводом строки (`\n` в Unix, `\r\n` в Windows). Открывают в текстовом режиме, читают по строкам. |
| **Типизированные (бинарные с фиксированной структурой)** | Хранят последовательность одинаковых записей известной структуры. Открывают в бинарном режиме, читают порциями фиксированного размера. |
| **Нетипизированные (бинарные с произвольной структурой)** | Заголовок описывает структуру, дальше блоки данных разного формата (например, `.wav`, `.png`). |

Скорость работы с текстовыми файлами обычно ниже, чем с бинарными, потому что нужно искать разделители строк в буфере. Но для большинства задач это не критично — современные ОС агрессивно кешируют диск.

## Способы доступа к файлам

| Способ | Описание |
|--------|----------|
| **Последовательный** | Читаем/пишем «от начала к концу». Простой и универсальный. |
| **Прямой (random)** | Можем перемещаться в любую позицию через `seek`/`tell` (см. следующую лекцию). |
| **Индексный** | Поверх random-доступа — структура «индекс + данные». Используется в БД. |

Эта лекция — про последовательный доступ. Прямой — в [следующей](lecture-04-binary-random-access.md).

## Открытие файла

### Python: `open()`

```python
fh = open("data.txt", mode="r", encoding="utf-8")
```

Основные параметры:

- `file` — путь или файловый дескриптор;
- `mode` — режим:

    | Символ | Значение |
    |--------|----------|
    | `r` | чтение (по умолчанию) |
    | `w` | запись (файл создаётся или обрезается) |
    | `x` | создание (ошибка, если файл существует) |
    | `a` | дозапись в конец |
    | `+` | чтение + запись |
    | `t` | текстовый режим (по умолчанию) |
    | `b` | бинарный режим |

    Комбинируются: `rb`, `w+`, `ab`.

- `encoding` — кодировка для текстового режима (всегда указывайте явно — `"utf-8"`);
- `newline` — управление переводами строк (`""` — оставлять как есть);
- `buffering` — размер буфера.

### Кодировки по умолчанию

```python
import locale
print(locale.getpreferredencoding(False))
# 'utf-8' на macOS/Linux
# 'cp1251' на русифицированной Windows (или 'cp65001' для UTF-8)
```

**Всегда указывайте `encoding="utf-8"` явно.** Без этого код, работающий на macOS, может ломаться на Windows.

### Закрытие файла

Открытый файл нужно закрыть, чтобы освободить ресурсы ОС:

```python
fh = open("data.txt", encoding="utf-8")
try:
    data = fh.read()
finally:
    fh.close()
```

Но в идиоматическом Python используется **контекстный менеджер** `with`:

```python
with open("data.txt", encoding="utf-8") as fh:
    data = fh.read()
# Файл закрыт автоматически, даже если внутри было исключение.
```

Это сокращает код и убирает целый класс багов «забыл закрыть файл».

### Go: `os.Open` / `os.Create`

```go
f, err := os.Open("data.txt")   // только для чтения
if err != nil {
    return err
}
defer f.Close()  // закрыть при выходе из функции
```

Запись:

```go
f, err := os.Create("output.txt") // создаёт или обрезает
if err != nil {
    return err
}
defer f.Close()
```

Для полного контроля над флагами и режимом:

```go
f, err := os.OpenFile("log.txt",
    os.O_WRONLY|os.O_APPEND|os.O_CREATE, 0644)
```

`defer` — отложенный вызов, выполнится перед возвратом из функции. Это идиоматический способ освобождать ресурсы в Go.

## Чтение и запись текстовых файлов

### Чтение целиком

=== "Python"

    ```python
    # Всё содержимое — одной строкой:
    with open("data.txt", encoding="utf-8") as fh:
        text = fh.read()

    # Все строки — в список:
    with open("data.txt", encoding="utf-8") as fh:
        lines = fh.readlines()  # ['line1\n', 'line2\n', ...]

    # Построчно (самый памятно-эффективный способ):
    with open("data.txt", encoding="utf-8") as fh:
        for line in fh:
            print(line.rstrip())
    ```

=== "Go"

    ```go
    // Целиком в строку:
    data, err := os.ReadFile("data.txt")
    if err != nil {
        return err
    }
    text := string(data)

    // Построчно через bufio.Scanner:
    f, err := os.Open("data.txt")
    if err != nil {
        return err
    }
    defer f.Close()

    scanner := bufio.NewScanner(f)
    for scanner.Scan() {
        line := scanner.Text()
        fmt.Println(line)
    }
    if err := scanner.Err(); err != nil {
        return err
    }
    ```

### Запись

=== "Python"

    ```python
    with open("output.txt", "w", encoding="utf-8") as fh:
        fh.write("Первая строка\n")
        print("Вторая строка", file=fh)
        fh.writelines(["a\n", "b\n", "c\n"])
    ```

    Дозапись (не обрезать существующий файл):

    ```python
    with open("output.txt", "a", encoding="utf-8") as fh:
        fh.write("ещё строка\n")
    ```

=== "Go"

    ```go
    // Записать всё сразу:
    err := os.WriteFile("output.txt", []byte("hello\n"), 0644)

    // Или построчно через bufio.Writer:
    f, err := os.Create("output.txt")
    if err != nil {
        return err
    }
    defer f.Close()

    w := bufio.NewWriter(f)
    for _, line := range []string{"a", "b", "c"} {
        _, _ = fmt.Fprintln(w, line)
    }
    _ = w.Flush() // не забыть!
    ```

## Файловая система

Для работы с путями, проверкой существования, обходом каталогов в Python есть два модуля:

- **`os` + `os.path`** — традиционный (функции вроде `os.path.join`, `os.path.exists`).
- **`pathlib`** — современный объектно-ориентированный API. **Рекомендуется**.

### `pathlib` — современный подход

```python
from pathlib import Path

# Создание пути
p = Path("data") / "users" / "vasya.txt"
print(p)              # data/users/vasya.txt
print(p.parent)       # data/users
print(p.name)         # vasya.txt
print(p.stem)         # vasya
print(p.suffix)       # .txt

# Существование, тип
p.exists()
p.is_file()
p.is_dir()

# Чтение/запись «одним вызовом»:
text = Path("data.txt").read_text(encoding="utf-8")
Path("output.txt").write_text("hello\n", encoding="utf-8")

# Бинарные:
data = Path("photo.jpg").read_bytes()

# Текущий рабочий каталог
Path.cwd()

# Домашний каталог пользователя
Path.home()

# Создание каталогов (mkdir -p)
Path("nested/dirs").mkdir(parents=True, exist_ok=True)

# Поиск файлов с шаблоном
for file in Path("src").rglob("*.py"):
    print(file)

# Удаление
Path("temp.txt").unlink(missing_ok=True)
```

### Go: `os` + `io/fs` + `path/filepath`

```go
import (
    "io/fs"
    "os"
    "path/filepath"
)

// Соединить компоненты пути
p := filepath.Join("data", "users", "vasya.txt")

// Проверка существования
if _, err := os.Stat(p); errors.Is(err, fs.ErrNotExist) {
    // нет такого файла
}

// Текущий каталог
cwd, _ := os.Getwd()

// Домашний каталог
home, _ := os.UserHomeDir()

// Создать каталоги (mkdir -p)
_ = os.MkdirAll("nested/dirs", 0755)

// Прочитать файл целиком
data, err := os.ReadFile(p)

// Обойти каталог рекурсивно
_ = filepath.WalkDir("src", func(path string, d fs.DirEntry, err error) error {
    if err != nil {
        return err
    }
    if !d.IsDir() && filepath.Ext(path) == ".go" {
        fmt.Println(path)
    }
    return nil
})

// Удалить
_ = os.Remove("temp.txt")
```

## Форматы данных

Хранить данные «как попало» — путь к проблемам. Для разных задач есть устоявшиеся форматы:

| Формат | Когда выбирать | Стандартный модуль Python | Пакет Go |
|--------|----------------|---------------------------|----------|
| **CSV** | Табличные данные, обмен с Excel/БД | `csv` | `encoding/csv` |
| **JSON** | API, обмен с фронтом, конфиги без комментариев | `json` | `encoding/json` |
| **YAML** | Человекочитаемые конфиги | `pyyaml` (внешний) | `gopkg.in/yaml.v3` |
| **TOML** | Конфиги с типами (pyproject.toml, Cargo.toml) | `tomllib` (3.11+ read; `tomli-w` для записи) | `BurntSushi/toml` |
| **INI** | Простые конфиги (legacy) | `configparser` | `gopkg.in/ini.v1` |
| **XML** | Legacy-обмен | `xml.etree.ElementTree` | `encoding/xml` |
| **Protobuf** | Эффективный бинарный обмен между сервисами | `protobuf` | `google.golang.org/protobuf` |

## CSV

CSV (Comma-Separated Values) — самый старый и распространённый табличный формат.

### Python: `csv`

```python
import csv

# Запись построчно
rows = [
    ["first_name", "last_name", "city"],
    ["Tyrese", "Hirthe", "Strackeport"],
    ["Jules", "Dicki", "Lake Nickolasville"],
]

with open("data.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(rows)

# Чтение
with open("data.csv", encoding="utf-8") as f:
    for row in csv.reader(f):
        print(row)
```

Часто удобнее работать со словарями (первая строка — заголовки):

```python
with open("data.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        print(row["first_name"], row["city"])

# Запись словарей
with open("data.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["first_name", "last_name", "city"])
    writer.writeheader()
    writer.writerow({"first_name": "Anna", "last_name": "Doe", "city": "Moscow"})
```

> `newline=""` нужен, чтобы Python сам не добавлял лишние `\r`. Это обязательно при работе с CSV.

### Go: `encoding/csv`

```go
import (
    "encoding/csv"
    "os"
)

// Запись
f, _ := os.Create("data.csv")
defer f.Close()

w := csv.NewWriter(f)
_ = w.Write([]string{"first_name", "last_name", "city"})
_ = w.Write([]string{"Tyrese", "Hirthe", "Strackeport"})
w.Flush()

// Чтение
f, _ := os.Open("data.csv")
defer f.Close()

r := csv.NewReader(f)
records, _ := r.ReadAll()
for _, row := range records {
    fmt.Println(row)
}
```

## JSON

JSON — текстовый формат, основанный на JavaScript. Очень близок к структурам Python (dict/list) и Go (struct/slice/map).

### Python: `json`

```python
import json

data = {
    "name": "Иванов",
    "scores": {"Математика": 90, "Физика": 70},
    "hobbies": ["рисование", "плавание"],
    "age": 25.5,
    "pet": None,
}

# Сериализация
text = json.dumps(data, ensure_ascii=False, indent=2)
print(text)

# Сразу в файл
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Десериализация
with open("data.json", encoding="utf-8") as f:
    loaded = json.load(f)

# Из строки
loaded = json.loads(text)
```

Параметры:

- `ensure_ascii=False` — оставить кириллицу как есть (по умолчанию экранируется в `\uXXXX`);
- `indent=2` — отступы для красивого вывода;
- `sort_keys=True` — отсортировать ключи (полезно для воспроизводимости diff'ов).

### Go: `encoding/json`

```go
import (
    "encoding/json"
    "os"
)

type Student struct {
    Name    string         `json:"name"`
    Scores  map[string]int `json:"scores"`
    Hobbies []string       `json:"hobbies"`
    Age     float64        `json:"age"`
    Pet     *string        `json:"pet"`
}

func main() {
    s := Student{
        Name:    "Иванов",
        Scores:  map[string]int{"Математика": 90, "Физика": 70},
        Hobbies: []string{"рисование", "плавание"},
        Age:     25.5,
    }

    // В строку с отступами
    b, _ := json.MarshalIndent(s, "", "  ")
    fmt.Println(string(b))

    // Сразу в файл
    f, _ := os.Create("data.json")
    defer f.Close()
    enc := json.NewEncoder(f)
    enc.SetIndent("", "  ")
    _ = enc.Encode(s)

    // Чтение
    raw, _ := os.ReadFile("data.json")
    var loaded Student
    _ = json.Unmarshal(raw, &loaded)
}
```

Теги структуры `json:"name"` управляют именами полей в JSON. Без тегов поле `Scores` сериализовалось бы как `"Scores"` (с заглавной).

## YAML

YAML — формат, близкий к JSON, но более человекочитаемый: с отступами, без скобок и кавычек везде. Стандарт для конфигов современных DevOps-инструментов (Kubernetes, Docker Compose, GitHub Actions).

### Python: `pyyaml` / `ruamel.yaml`

```bash
uv add pyyaml
```

```python
import yaml

with open("config.yaml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)  # safe_load — НЕ исполнять произвольные классы

with open("out.yaml", "w", encoding="utf-8") as f:
    yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
```

> Используйте `safe_load`, а не `load`. Обычный `yaml.load` может выполнить произвольный код при десериализации пользовательских тегов — это уязвимость.

### Go: `yaml.v3`

```go
import "gopkg.in/yaml.v3"

var cfg Config
raw, _ := os.ReadFile("config.yaml")
_ = yaml.Unmarshal(raw, &cfg)

out, _ := yaml.Marshal(cfg)
_ = os.WriteFile("out.yaml", out, 0644)
```

## TOML

TOML — современный формат для конфигов с типами. Используется в `pyproject.toml` (Python-проекты), `Cargo.toml` (Rust), `wrangler.toml` (Cloudflare).

### Python: `tomllib` (3.11+)

```python
import tomllib

with open("pyproject.toml", "rb") as f:  # обязательно "rb"!
    cfg = tomllib.load(f)

print(cfg["project"]["name"])
```

Для записи в стандартной библиотеке инструмента нет — нужен внешний `tomli-w`:

```bash
uv add tomli-w
```

```python
import tomli_w

with open("out.toml", "wb") as f:
    tomli_w.dump({"server": {"port": 8000}}, f)
```

### Go: `BurntSushi/toml`

```go
import "github.com/BurntSushi/toml"

var cfg Config
_, _ = toml.DecodeFile("config.toml", &cfg)

f, _ := os.Create("out.toml")
defer f.Close()
_ = toml.NewEncoder(f).Encode(cfg)
```

## INI

Старый формат для простых конфигов. В Windows раньше использовался повсеместно (теперь реестр), в мире Unix остаётся популярным.

### Python: `configparser`

```python
import configparser

# Создание
config = configparser.ConfigParser()
config["Settings"] = {
    "font": "Courier",
    "font_size": "10",
    "font_style": "Normal",
}
config["Theme"] = {"dark": "true"}

with open("settings.ini", "w") as f:
    config.write(f)

# Чтение
config = configparser.ConfigParser()
config.read("settings.ini")

font = config["Settings"]["font"]
size = config["Settings"].getint("font_size")
dark = config["Theme"].getboolean("dark")
```

Файл `settings.ini`:

```ini
[Settings]
font = Courier
font_size = 10
font_style = Normal

[Theme]
dark = true
```

### Go: `gopkg.in/ini.v1`

```go
import "gopkg.in/ini.v1"

cfg, _ := ini.Load("settings.ini")
font := cfg.Section("Settings").Key("font").String()
size, _ := cfg.Section("Settings").Key("font_size").Int()
```

## Сериализация Python-объектов: `pickle`

`pickle` умеет сохранять **любой** Python-объект в бинарный поток и обратно. Очень удобно для кеширования промежуточных результатов.

```python
import pickle

data = {"users": ["Аня", "Боря"], "budget": 1000}

with open("data.pkl", "wb") as f:
    pickle.dump(data, f)

with open("data.pkl", "rb") as f:
    loaded = pickle.load(f)
```

**Когда использовать pickle:**

- сохраняем промежуточные результаты для собственных скриптов;
- сериализуем сложные объекты, для которых нет другого формата (например, обученная ML-модель — хотя для этого предпочтительнее `joblib` или формат фреймворка).

**Когда НЕ использовать:**

- обмен с другими языками — pickle специфичен для Python;
- хранение данных от **недоверенного источника** — `pickle.load` может выполнить произвольный код. Это уязвимость.

В Go нативного аналога pickle нет — используют либо JSON, либо `encoding/gob` (бинарный формат, специфичный для Go).

## Сравнение Python ↔ Go: работа с файлами

| Аспект | Python | Go |
|--------|--------|-----|
| Открыть/закрыть | `with open(...) as f:` | `f, err := os.Open(); defer f.Close()` |
| Прочитать целиком | `Path(p).read_text()` | `os.ReadFile(p)` |
| Построчно | `for line in f:` | `bufio.NewScanner(f)` |
| Записать | `Path(p).write_text(...)` | `os.WriteFile(p, data, mode)` |
| Существование | `Path(p).exists()` | `os.Stat(p)` + `errors.Is(err, fs.ErrNotExist)` |
| Соединение пути | `Path(a) / b / c` | `filepath.Join(a, b, c)` |
| Обход каталога | `Path(p).rglob("*.py")` | `filepath.WalkDir(p, fn)` |
| JSON | `json.load(f)` | `json.NewDecoder(f).Decode(&v)` |
| CSV | `csv.DictReader(f)` | `csv.NewReader(f).ReadAll()` |
| Кодировки | явно через `encoding=` | `string(b)` если уже UTF-8 |

---

## Контрольные вопросы

- Чем отличаются режимы `r`, `w`, `a`, `x`? Что произойдёт при открытии существующего файла в режиме `w`?
- Почему всегда надо указывать `encoding="utf-8"` явно?
- Что произойдёт, если забыть `with` и не вызвать `close()`?
- В чём преимущество `pathlib.Path` перед `os.path`?
- Для каких задач подходит CSV, а для каких — JSON?
- Почему при работе с CSV в Python нужен `newline=""`?
- Чем `safe_load` отличается от `load` в `yaml`, и почему это важно?
- В каких случаях стоит использовать `pickle`, а в каких — категорически нет?
- Что такое `defer` в Go и почему он удобен для закрытия файлов?
- Как в Go обходить каталог рекурсивно, не используя сторонних библиотек?
