# Тема 14. Продвинутый Go (Golang Advanced)

После основ Go (тема 13) рассматриваем «взрослые» темы: конкурентность, контексты, сетевой стек, работу с БД и инструменты профилирования. Это то, ради чего Go и был придуман.

## Лекции

1. [Конкурентность: горутины, каналы, `select`](lecture-01-concurrency.md) — горутины и их жизненный цикл, каналы (buffered/unbuffered), `select`, `sync.WaitGroup`/`Mutex`/`RWMutex`/`Once`, `sync/atomic`, паттерны (worker pool, fan-in/fan-out, pipeline).
2. [Context: отмена, таймауты, метаданные](lecture-02-context.md) — `context.Context`, `WithCancel`/`WithTimeout`/`WithDeadline`/`WithValue`, идиомы распространения и слушания отмены.
3. [HTTP-клиент и HTTP-сервер](lecture-03-http.md) — `net/http`, production-ready клиент с `Timeout`, маршрутизация Go 1.22+, middleware, graceful shutdown, `httptest`.
4. [Файлы, JSON и БД (`database/sql`)](lecture-04-files-json-db.md) — `os`/`io`/`bufio`, `path/filepath`, `embed.FS`, `encoding/json` с тегами и кастомизацией, `database/sql` + драйверы, транзакции, защита от SQL-инъекций.
5. [Бенчмарки, профилирование, race detector](lecture-05-benchmarks-pprof.md) — `Benchmark*`, `benchstat`, `pprof` (CPU/heap/goroutine), `net/http/pprof`, `-race`, escape analysis, `sync.Pool`.

## Что дальше

Курс по Go завершён. Применяйте полученное в практическом задании (большой проект — см. [Практика](../../practice/practice.md)) и в собственных проектах. Дальнейшие шаги:

- **gRPC и Protocol Buffers** — продвинутый межсервисный обмен;
- **OpenTelemetry** — трейсинг, метрики, логи в одном стеке;
- **Wire** или **fx** — DI для больших проектов;
- **Cobra** + **Viper** — CLI с конфигурацией;
- **Темporal** или **Asynq** — оркестрация long-running задач.

Лучший способ освоить Go в реальности — читать чужой код (Kubernetes, Docker, Terraform) и писать собственные сервисы.
