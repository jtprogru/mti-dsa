# Лекция 3. HTTP-клиент и HTTP-сервер на стандартной библиотеке

В теме 10 лекции 1 мы разбирали `urllib` и `requests` для Python и параллельно немного коснулись `net/http` в Go. Здесь — расширенный разбор: production-ready клиент, маршрутизация на Go 1.22+, middleware, graceful shutdown.

## HTTP-клиент

### Простейший GET

```go
package main

import (
    "fmt"
    "io"
    "net/http"
)

func main() {
    resp, err := http.Get("https://api.github.com")
    if err != nil {
        panic(err)
    }
    defer resp.Body.Close()

    body, _ := io.ReadAll(resp.Body)
    fmt.Println(resp.StatusCode)
    fmt.Println(string(body))
}
```

Ключевые вещи:

1. `resp.Body.Close()` через `defer` — обязательно. Иначе TCP-соединение не вернётся в пул.
2. `resp.Body` — это `io.ReadCloser`. Стандартные читатели (`io.ReadAll`, `bufio.NewScanner`, `json.NewDecoder`) с ним работают.

### Не используйте `http.DefaultClient` в продакшене

`http.Get`, `http.Post`, `http.DefaultClient` — это **глобальные клиенты без таймаутов**. Если сервер не отвечает — горутина будет висеть вечно. В обучающем коде сойдёт, но не для прода.

```go
client := &http.Client{
    Timeout: 10 * time.Second,
    Transport: &http.Transport{
        MaxIdleConns:        100,
        MaxIdleConnsPerHost: 10,
        IdleConnTimeout:     90 * time.Second,
    },
}
```

`http.Client.Timeout` — суммарный таймаут на запрос (включая dial, TLS, чтение тела). Для более тонкого контроля — настройки внутри `Transport`.

### Запрос с заголовками и контекстом

```go
req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewReader(body))
if err != nil {
    return err
}
req.Header.Set("Content-Type", "application/json")
req.Header.Set("Authorization", "Bearer "+token)

resp, err := client.Do(req)
if err != nil {
    return fmt.Errorf("post %s: %w", url, err)
}
defer resp.Body.Close()

if resp.StatusCode >= 400 {
    body, _ := io.ReadAll(resp.Body)
    return fmt.Errorf("status %d: %s", resp.StatusCode, body)
}
```

Любой клиентский вызов в библиотечной функции должен принимать `ctx context.Context` и передавать его в `NewRequestWithContext`. Это даёт отмену при таймауте/отмене запроса вызывающего.

### Парсинг JSON-ответа

```go
type GitHubUser struct {
    Login string `json:"login"`
    Name  string `json:"name"`
    Bio   string `json:"bio"`
}

resp, err := client.Get("https://api.github.com/users/jtprogru")
// ...
var u GitHubUser
if err := json.NewDecoder(resp.Body).Decode(&u); err != nil {
    return err
}
```

`json.NewDecoder(resp.Body).Decode` лучше, чем `ReadAll` + `Unmarshal`: не нужно держать всё тело в памяти. Подробно про JSON — следующая лекция.

## HTTP-сервер

### Минимальный сервер

```go
package main

import (
    "fmt"
    "net/http"
)

func main() {
    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintln(w, "Привет!")
    })
    http.ListenAndServe(":8080", nil)
}
```

Запустить: `go run main.go` → `curl localhost:8080`. Это работает, но `nil` означает «использовать `DefaultServeMux`» — глобальный мультиплексор, антипаттерн в продакшене.

### Production-style сервер с явным мультиплексором

```go
func main() {
    mux := http.NewServeMux()
    mux.HandleFunc("GET /users/{id}", handleGetUser)
    mux.HandleFunc("POST /users", handleCreateUser)
    mux.HandleFunc("GET /health", handleHealth)

    srv := &http.Server{
        Addr:         ":8080",
        Handler:      mux,
        ReadTimeout:  5 * time.Second,
        WriteTimeout: 10 * time.Second,
        IdleTimeout:  120 * time.Second,
    }
    log.Fatal(srv.ListenAndServe())
}
```

### Маршрутизация на Go 1.22+

В Go 1.22 (февраль 2024) стандартный `http.ServeMux` научился двум важным вещам:

1. **Сопоставление по HTTP-методу:**

```go
mux.HandleFunc("GET /users/{id}", handleGetUser)
mux.HandleFunc("DELETE /users/{id}", handleDeleteUser)
```

2. **Параметры пути:**

```go
mux.HandleFunc("GET /users/{id}", func(w http.ResponseWriter, r *http.Request) {
    id := r.PathValue("id")
    fmt.Fprintln(w, "user id:", id)
})
```

До этого приходилось ставить сторонние роутеры (`gorilla/mux`, `chi`, `gin`). Сейчас для большинства задач хватает стандартного `ServeMux`. Но для middleware-цепочек удобнее всё-таки [chi](https://github.com/go-chi/chi).

### Обработчик: интерфейс или функция

```go
// Стиль 1: функция
func handler(w http.ResponseWriter, r *http.Request) { ... }
mux.HandleFunc("/path", handler)

// Стиль 2: объект, реализующий http.Handler
type Server struct {
    db *sql.DB
}

func (s *Server) ServeHTTP(w http.ResponseWriter, r *http.Request) { ... }
mux.Handle("/path", server)
```

Когда обработчику нужны зависимости (БД, конфиг, логгер) — удобно сделать его методом структуры:

```go
type API struct {
    db     *sql.DB
    logger *slog.Logger
}

func (a *API) handleUser(w http.ResponseWriter, r *http.Request) {
    id := r.PathValue("id")
    var u User
    err := a.db.QueryRowContext(r.Context(), "SELECT ... WHERE id=$1", id).
        Scan(&u.ID, &u.Name)
    if err != nil {
        http.Error(w, "not found", 404)
        return
    }
    json.NewEncoder(w).Encode(u)
}

api := &API{db: db, logger: logger}
mux.HandleFunc("GET /users/{id}", api.handleUser)
```

Это идиоматичный способ DI в Go — без рефлексии и фреймворков.

### Чтение тела запроса

```go
func handleCreate(w http.ResponseWriter, r *http.Request) {
    var req CreateUserRequest
    // ограничиваем размер тела на случай злонамеренного клиента
    r.Body = http.MaxBytesReader(w, r.Body, 1<<20)  // 1 MiB
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "bad json", 400)
        return
    }
    // ... обработка req ...
    w.WriteHeader(201)
    json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}
```

`http.MaxBytesReader` — обязательно для публичных API. Без него один клиент может прислать многогигабайтное тело и съесть память.

### Чтение query-параметров

```go
q := r.URL.Query()
limit := q.Get("limit")        // строка
search := q.Get("search")
tags := q["tag"]               // []string — для повторяющихся параметров (?tag=a&tag=b)
```

## Middleware

Middleware — функция, которая принимает `http.Handler` и возвращает новый `http.Handler`, добавляющий поведение «вокруг» исходного.

```go
func loggingMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        next.ServeHTTP(w, r)
        log.Printf("%s %s %v", r.Method, r.URL.Path, time.Since(start))
    })
}

func authMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        token := r.Header.Get("Authorization")
        if !validToken(token) {
            http.Error(w, "unauthorized", 401)
            return
        }
        ctx := context.WithValue(r.Context(), userIDKey{}, userIDFromToken(token))
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

handler := loggingMiddleware(authMiddleware(mux))
srv := &http.Server{Addr: ":8080", Handler: handler}
```

В стандартной библиотеке нет helper'а для цепочек, но они тривиально пишутся вручную. Или возьмите `chi` — там удобный `r.Use(...)`.

## Graceful shutdown

В продакшене сервер должен:

1. Принять `SIGINT`/`SIGTERM`.
2. Перестать принимать новые запросы.
3. Дать активным запросам завершиться (с разумным таймаутом).
4. Закрыть БД, отправить буферы логов, выйти.

```go
func main() {
    mux := http.NewServeMux()
    // ... регистрация handler'ов ...

    srv := &http.Server{Addr: ":8080", Handler: mux}

    // Запускаем сервер в горутине
    go func() {
        if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Fatalf("server: %v", err)
        }
    }()
    log.Println("listening on :8080")

    // Ждём сигнал
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit
    log.Println("shutting down...")

    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()
    if err := srv.Shutdown(ctx); err != nil {
        log.Fatalf("forced shutdown: %v", err)
    }
    log.Println("server stopped")
}
```

`srv.Shutdown(ctx)` — корректная остановка: закроется listener, активные соединения дождутся, либо принудительно оборвутся по истечении `ctx`.

## TLS

Простейший HTTPS:

```go
srv := &http.Server{
    Addr:    ":443",
    Handler: mux,
}
log.Fatal(srv.ListenAndServeTLS("cert.pem", "key.pem"))
```

В реальной жизни TLS-терминацию обычно делают на уровне reverse proxy (nginx, Caddy, Traefik) или балансировщика, а Go-приложение слушает HTTP внутри сети. Но если нужно «прямо так» — стандартная библиотека всё умеет, включая автоматический Let's Encrypt через `golang.org/x/crypto/acme/autocert`.

## Тестирование HTTP

Стандартный пакет `net/http/httptest` — для запуска тестового сервера без поднятия настоящего сокета:

```go
import "net/http/httptest"

func TestHandler(t *testing.T) {
    req := httptest.NewRequest("GET", "/hello", nil)
    w := httptest.NewRecorder()

    handler(w, req)

    if w.Code != 200 {
        t.Errorf("got %d, want 200", w.Code)
    }
    if !strings.Contains(w.Body.String(), "Привет") {
        t.Errorf("unexpected body: %s", w.Body.String())
    }
}
```

Или полноценный тестовый сервер с реальным портом:

```go
ts := httptest.NewServer(handler)
defer ts.Close()

resp, _ := http.Get(ts.URL + "/path")
```

## Параллель с Python

| Python                                            | Go                                              |
|---------------------------------------------------|--------------------------------------------------|
| `requests.get(url, timeout=5)`                    | `http.Client{Timeout: 5*time.Second}.Get(url)`  |
| `requests.Session()`                              | `http.Client` (переиспользуется автоматически)   |
| `aiohttp` (async)                                 | `net/http` (горутины — встроенная конкурентность) |
| Flask `@app.route("/users/<id>")`                 | `mux.HandleFunc("GET /users/{id}", ...)`        |
| FastAPI с зависимостями                           | методы на структуре + явная DI                  |
| WSGI / ASGI                                       | `http.Handler` интерфейс                         |
| `app.before_request`, middleware Flask            | функция-обёртка над `http.Handler`               |
| `gunicorn`/`uvicorn`                              | один бинарник — `srv.ListenAndServe()`           |
| graceful shutdown через `signal`                  | `srv.Shutdown(ctx)`                              |

## Итог

Стандартный `net/http` — production-ready: HTTP-клиент с таймаутами, сервер с роутингом и параметрами пути (Go 1.22+), middleware как функции-обёртки, graceful shutdown через `srv.Shutdown(ctx)`. Для большинства проектов сторонние фреймворки не нужны. В следующей лекции — файлы, JSON и работа с базами данных через `database/sql`.
