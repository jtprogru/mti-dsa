# Лекция 1. HTTP-клиент и HTTP-сервер (HTTP Client and Server)

В стандартной библиотеке Python для работы с HTTP есть:

- `urllib.request` — клиент (надстройка над `http.client`);
- `http.server` — учебный сервер;
- `socket` — низкоуровневая работа с TCP/UDP.

У всех этих модулей есть один большой недостаток — *неудобство работы*: обилие классов и функций, код получается не pythonic. Поэтому в реальной разработке для HTTP-клиента в Python используют сторонний пакет [**requests**](https://requests.readthedocs.io/) (или асинхронный [**httpx**](https://www.python-httpx.org/)).

В Go ситуация противоположная — стандартный пакет `net/http` *уже идиоматичен и production-ready*, сторонние HTTP-клиенты практически не нужны.

## Сравнение: стандартный urllib vs `requests`

=== "Стандартная библиотека Python"

    ```python
    import urllib.request

    with urllib.request.urlopen("https://httpbin.org/get") as response:
        body = response.read()
        print(body)
        print(response.getheader("Server"))
        print(response.getcode())
    ```

=== "`requests`"

    ```python
    import requests

    r = requests.get("https://httpbin.org/get")
    print(r.content)
    print(r.json())             # автоматически парсит JSON
    print(r.headers.get("Server"))
    print(r.status_code)
    ```

=== "Go (`net/http`)"

    ```go
    package main

    import (
        "fmt"
        "io"
        "net/http"
    )

    func main() {
        resp, err := http.Get("https://httpbin.org/get")
        if err != nil {
            panic(err)
        }
        defer resp.Body.Close()

        body, _ := io.ReadAll(resp.Body)
        fmt.Println(string(body))
        fmt.Println(resp.Header.Get("Server"))
        fmt.Println(resp.StatusCode)
    }
    ```

Разница на лицо — `requests` (и `net/http` в Go) выигрывают по эргономике у `urllib.request`.

В `requests` есть:

- множество методов HTTP-аутентификации;
- сессии с куками;
- полноценная поддержка SSL;
- методы-плюшки вроде `.json()` для парсинга;
- проксирование;
- грамотная и логичная работа с исключениями.

## Обработка ошибок

> **При работе с внешними сервисами никогда не стоит полагаться на их отказоустойчивость.** Всё упадёт рано или поздно — нужно быть готовыми заранее.

Возможные проблемы:

- хост недоступен (DNS lookup failure);
- таймаут соединения / чтения;
- HTTP-ошибки (4xx, 5xx);
- ошибки SSL (просрочен сертификат, не доверен, и т. д.).

Базовый класс исключения в `requests` — `RequestException`. От него наследуются `HTTPError`, `ConnectionError`, `Timeout`, `SSLError`, `ProxyError`.

```python
import requests
from requests.exceptions import ConnectTimeout, ReadTimeout, ConnectionError, HTTPError

try:
    r = requests.get("https://httpbin.org/user-agent", timeout=(3.05, 27))
    r.raise_for_status()
except ConnectTimeout:
    print("Таймаут соединения")
except ReadTimeout:
    print("Таймаут чтения")
except ConnectionError:
    print("Ошибка соединения / DNS")
except HTTPError as e:
    print(f"HTTP {e.response.status_code}: {e.response.text}")
```

В Go проверка ошибок везде через возвращаемое значение `error`:

```go
resp, err := http.Get(url)
if err != nil {
    if urlErr, ok := err.(*url.Error); ok {
        if urlErr.Timeout() {
            // таймаут
        }
    }
    return err
}
defer resp.Body.Close()

if resp.StatusCode >= 400 {
    return fmt.Errorf("HTTP %d", resp.StatusCode)
}
```

Для таймаута в `net/http` нужен `http.Client` с настройкой:

```go
client := &http.Client{Timeout: 10 * time.Second}
resp, err := client.Get(url)
```

## Быстрый старт с `requests`

### GET, POST, PUT, DELETE

```python
r = requests.get("https://api.github.com/events")
r = requests.post("https://httpbin.org/post", data={"key": "value"})
r = requests.put("https://httpbin.org/put", data={"key": "value"})
r = requests.delete("https://httpbin.org/delete")
r = requests.head("https://httpbin.org/get")
```

### Передача параметров в GET

```python
payload = {"key1": "value1", "key2": "value2"}
r = requests.get("https://httpbin.org/get", params=payload)
print(r.url)  # https://httpbin.org/get?key1=value1&key2=value2
```

### JSON в запросе и ответе

```python
# отправить JSON
r = requests.post(url, json={"some": "data"})

# распарсить JSON-ответ
data = r.json()  # dict
```

### Настраиваемые заголовки

```python
headers = {"User-Agent": "my-app/0.0.1"}
r = requests.get(url, headers=headers)
```

### Отправка файлов

```python
with open("report.xlsx", "rb") as f:
    files = {"file": ("report.xlsx", f, "application/vnd.openxmlformats")}
    r = requests.post(url, files=files)
```

> При передаче файлов обязательно открывайте их в *бинарном* режиме (`"rb"`), иначе заголовок `Content-Length` может быть посчитан неверно.

### Куки

```python
# чтение
r = requests.get(url)
print(r.cookies["session"])

# отправка
r = requests.get(url, cookies={"session": "abc"})
```

### Redirects и история

По умолчанию `requests` следует за редиректами:

```python
r = requests.get("http://github.com/")
print(r.url)        # https://github.com/ (после редиректа)
print(r.history)    # [<Response [301]>]
```

Отключить:

```python
r = requests.get(url, allow_redirects=False)
```

### Timeout

```python
# единый таймаут (применяется ко всем фазам)
r = requests.get(url, timeout=5)

# отдельно на соединение и на чтение
r = requests.get(url, timeout=(3.05, 27))
```

Без явного таймаута запрос может зависнуть надолго — *всегда* указывайте таймауты в production-коде.

## Аутентификация

### Basic Authentication

> Данные просто упакованы в base64 — использовать *только через HTTPS*.

```python
import requests

# явная форма
r = requests.get("https://api.github.com/user",
                 auth=requests.auth.HTTPBasicAuth("user", "pass"))

# короткая
r = requests.get("https://api.github.com/user", auth=("user", "pass"))
```

В Go:

```go
req, _ := http.NewRequest("GET", "https://api.github.com/user", nil)
req.SetBasicAuth("user", "pass")
resp, _ := http.DefaultClient.Do(req)
```

### Bearer (OAuth, JWT)

```python
headers = {"Authorization": f"Bearer {token}"}
r = requests.get(url, headers=headers)
```

## HTTP-сервер

### Стандартный `http.server` в Python (учебный)

> Документация Python предупреждает: для production он не подходит.

```python
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        # ... обработка body
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"created": true}')

httpd = HTTPServer(("localhost", 8080), Handler)
httpd.serve_forever()
```

### Production HTTP-сервер на Go

В Go всё иначе — `net/http` *подходит* для production. Большинство микросервисов в индустрии написаны именно на нём:

```go
package main

import (
    "encoding/json"
    "log"
    "net/http"
)

type Response struct {
    Status string `json:"status"`
}

func handleGet(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(Response{Status: "ok"})
}

func handlePost(w http.ResponseWriter, r *http.Request) {
    var data map[string]any
    if err := json.NewDecoder(r.Body).Decode(&data); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    w.WriteHeader(http.StatusCreated)
    json.NewEncoder(w).Encode(map[string]bool{"created": true})
}

func main() {
    mux := http.NewServeMux()
    mux.HandleFunc("GET /", handleGet)
    mux.HandleFunc("POST /", handlePost)  // pattern matching с Go 1.22+

    srv := &http.Server{
        Addr:    ":8080",
        Handler: mux,
    }
    log.Fatal(srv.ListenAndServe())
}
```

В Python для production-веб-приложений используют **Flask** / **FastAPI** / **Django** (см. [Тему 11](../11-application-development/index.md)).

## Что выбрать?

| Задача | Python | Go |
|--------|--------|-----|
| Простой HTTP-запрос | `requests.get(url)` | `http.Get(url)` |
| Production HTTP-клиент | `requests` или `httpx` (async) | `http.Client` |
| Production HTTP-сервер | Flask / FastAPI / Django (фреймворки) | `net/http` (стандартный) |
| WebSocket | `websockets` | `gorilla/websocket` или `net/http` (с Go 1.21+) |
| GraphQL | `strawberry`, `ariadne` | `graphql-go/graphql` |
| gRPC | `grpcio` | `google.golang.org/grpc` |

## Контрольные вопросы

- Чем `requests` лучше `urllib.request` для повседневной разработки?
- Какие исключения может бросить `requests` при неудачном запросе? Как их обработать?
- Почему важно всегда указывать `timeout` в HTTP-клиенте?
- Чем стандартный `http.server` в Python отличается от `net/http` в Go по применимости в production?
- В каких случаях нужно использовать сессии (`requests.Session`)?
