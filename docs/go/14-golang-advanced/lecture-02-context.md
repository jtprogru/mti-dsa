# Лекция 2. Context: отмена, таймауты, передача метаданных

## Зачем нужен `context.Context`

В прошлой лекции мы видели, что горутину нельзя «убить» снаружи. Её можно только попросить остановиться. Если у нас сервер обрабатывает запрос и порождает 5 горутин на параллельные подзадачи (запросы к БД, к внешним API), а клиент отвалился — как сказать всем 5 горутинам прекратить работу?

Раньше это решали через личные «stop-каналы» в каждой функции. Получался зоопарк сигналов. С Go 1.7 появился стандартный пакет `context`, и сейчас это **обязательная конвенция**: любая функция, которая делает что-то длительное (сетевой вызов, запрос к БД, операцию с диском), принимает `ctx context.Context` первым параметром.

```go
func FetchUser(ctx context.Context, id int) (*User, error) {
    // если ctx отменён — прекратить работу
}
```

## Что внутри Context

`Context` — это интерфейс:

```go
type Context interface {
    Deadline() (deadline time.Time, ok bool)  // дедлайн, если есть
    Done() <-chan struct{}                     // канал, закрытый при отмене
    Err() error                                 // причина отмены (после Done)
    Value(key any) any                          // user-defined метаданные
}
```

В реальной работе вы редко вызываете эти методы напрямую — обычно передаёте `ctx` дальше или используете `select { case <-ctx.Done(): ... }`.

## Корневые контексты

```go
ctx := context.Background()   // корневой пустой контекст
ctx := context.TODO()         // то же, но сигнализирует "ещё не решил"
```

- `Background()` — корень дерева контекстов. Используйте в `main`, в инициализации, в тестах.
- `TODO()` — заглушка: «здесь должен быть контекст, но я ещё не знаю откуда». Технически идентичен `Background()`, но `go vet` и линтеры различают их.

В библиотечном коде **никогда не вызывайте `Background()`** — всегда принимайте контекст от вызывающего.

## Производные контексты

Из корневого делают производные с дополнительным поведением:

### `WithCancel` — ручная отмена

```go
ctx, cancel := context.WithCancel(parent)
defer cancel()   // ОБЯЗАТЕЛЬНО — иначе утечка ресурсов

go doWork(ctx)
// ... позже
cancel()   // все потомки ctx получают сигнал
```

`cancel` идемпотентен (можно звать несколько раз). `defer cancel()` — обязательная идиома: даже если отменили вручную, вызов в defer не повредит, но защитит от утечки в случае ошибки на ранних путях.

### `WithTimeout` — отмена по таймауту

```go
ctx, cancel := context.WithTimeout(parent, 5*time.Second)
defer cancel()

result, err := slowOperation(ctx)
```

Если за 5 секунд `slowOperation` не вернулась — `ctx.Done()` закрывается, `ctx.Err()` возвращает `context.DeadlineExceeded`.

### `WithDeadline` — отмена в конкретный момент

```go
deadline := time.Now().Add(10 * time.Second)
ctx, cancel := context.WithDeadline(parent, deadline)
defer cancel()
```

`WithTimeout(p, d)` — это просто `WithDeadline(p, time.Now().Add(d))`.

### `WithValue` — метаданные

```go
ctx := context.WithValue(parent, userIDKey, 42)

// в потомке
id, ok := ctx.Value(userIDKey).(int)
```

**Важно:** `WithValue` нужен только для **метаданных запроса**, которые проходят через много слоёв: request-ID для логов, trace-ID для трейсинга, пользовательский ID для авторизации. **Не используйте `WithValue` для передачи обычных параметров функции** — для этого есть обычные аргументы.

Конвенции для ключей:

1. Ключи никогда не должны быть `string`. Используйте свой приватный тип:

```go
type userIDKey struct{}

ctx := context.WithValue(parent, userIDKey{}, 42)
v := ctx.Value(userIDKey{})
```

Так гарантированно не будет коллизии с ключом из другого пакета.

2. Делайте type-safe врапперы:

```go
type contextKey int
const userIDKeyV contextKey = 1

func WithUserID(ctx context.Context, id int) context.Context {
    return context.WithValue(ctx, userIDKeyV, id)
}

func UserID(ctx context.Context) (int, bool) {
    v, ok := ctx.Value(userIDKeyV).(int)
    return v, ok
}
```

## Как «слушать» отмену в своей функции

Базовый паттерн:

```go
func work(ctx context.Context) error {
    for {
        select {
        case <-ctx.Done():
            return ctx.Err()   // context.Canceled или DeadlineExceeded
        default:
            // полезная работа
        }
    }
}
```

Если внутри функции вы делаете долгий вызов — передавайте `ctx` дальше:

```go
func fetch(ctx context.Context, url string) ([]byte, error) {
    req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
    if err != nil {
        return nil, err
    }
    resp, err := http.DefaultClient.Do(req)
    // ...
}
```

`http.NewRequestWithContext` и `db.QueryContext` — стандартные методы стандартной библиотеки, которые умеют отменять операцию по контексту. Если функция называется без `Context` — обычно есть её версия с контекстом. Используйте её.

### Когда `ctx` не передаётся «вниз»

Бывают редкие случаи: фоновая задача, которая должна жить **дольше**, чем входной запрос. Тогда не передавайте дальше входной `ctx` — он отменится с запросом. Заведите свой:

```go
func handle(ctx context.Context, msg Message) {
    process(ctx, msg)
    go func() {
        bgCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
        defer cancel()
        sendMetrics(bgCtx, msg)  // не зависит от ctx запроса
    }()
}
```

Это исключение — большинству функций нужен входной `ctx`.

## Пример: запрос в БД с таймаутом

```go
func getUser(ctx context.Context, db *sql.DB, id int) (*User, error) {
    ctx, cancel := context.WithTimeout(ctx, 2*time.Second)
    defer cancel()

    var u User
    err := db.QueryRowContext(ctx, "SELECT id, name FROM users WHERE id=$1", id).
        Scan(&u.ID, &u.Name)
    if err != nil {
        return nil, fmt.Errorf("get user %d: %w", id, err)
    }
    return &u, nil
}
```

Если внешний `ctx` отменится раньше 2 секунд (например, клиент отвалился) — драйвер БД получит сигнал и закроет соединение, освободив ресурс.

## Пример: HTTP-handler с отменой

```go
func handleSlow(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()  // контекст, привязанный к жизни HTTP-запроса

    select {
    case <-time.After(10 * time.Second):
        fmt.Fprintln(w, "готово")
    case <-ctx.Done():
        // клиент отвалился раньше времени
        log.Printf("request canceled: %v", ctx.Err())
        return
    }
}
```

В net/http каждый входящий запрос имеет свой `r.Context()`, который отменяется, когда клиент закрывает соединение.

## Что часто делают неправильно

1. **Хранят `ctx` в полях структур.** Не делайте: контекст — это «параметр запроса», он должен путешествовать вниз по стеку, а не лежать в объекте. Исключение — короткоживущие worker-структуры, явно созданные «под запрос».

2. **Передают `nil` вместо `ctx`.** Никогда: получатель упадёт на `<-ctx.Done()`. Если нужен пустой контекст — `context.Background()` или `context.TODO()`.

3. **Используют `WithValue` для обычных параметров.** Контекст — не словарь для всего; кладите туда только сквозные метаданные запроса.

4. **Забывают `defer cancel()`.** `go vet` и `staticcheck` обычно ругаются.

5. **Замораживают горутину «навечно».** Если функция стартует горутину — она должна слушать `ctx.Done()` и уметь завершиться. Иначе при сбое получите утечку горутин.

## Параллель с Python

В Python `asyncio` есть похожие концепции:

| Python                                                   | Go                                              |
|----------------------------------------------------------|--------------------------------------------------|
| `asyncio.wait_for(coro, timeout=5)`                      | `context.WithTimeout` + передача `ctx` внутрь   |
| `asyncio.Task.cancel()`                                  | `cancel()` функции, полученной из `WithCancel`  |
| `CancelledError`                                          | `ctx.Err() == context.Canceled`                  |
| `contextvars.ContextVar`                                  | `context.WithValue` (метаданные запроса)         |
| таймауты через `signal.SIGALRM` (синхронный код)         | `context.WithTimeout` (универсально)            |
| `asyncio.shield(coro)`                                   | запустить с новым `Background()`-контекстом      |

## Итог

`context.Context` — обязательный первый параметр любой долгоиграющей функции. `WithCancel` — ручная отмена; `WithTimeout`/`WithDeadline` — автоматическая по времени; `WithValue` — только для метаданных запроса. Не забывайте `defer cancel()`. Слушайте `<-ctx.Done()` в долгих циклах и передавайте `ctx` дальше во все вложенные вызовы. В следующей лекции — HTTP-клиент и HTTP-сервер.
