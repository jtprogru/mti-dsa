# Примеры к теме 14 — Продвинутый Go

| Директория | Лекция |
|-----------|--------|
| `l01-concurrency/` | [Конкурентность](../../../docs/topics/14-golang-advanced/lecture-01-concurrency.md) |
| `l02-context/` | [Context](../../../docs/topics/14-golang-advanced/lecture-02-context.md) |
| `l03-http/server/`, `l03-http/client/` | [HTTP-клиент и HTTP-сервер](../../../docs/topics/14-golang-advanced/lecture-03-http.md) |
| `l04-json/` | [Файлы, JSON, БД](../../../docs/topics/14-golang-advanced/lecture-04-files-json-db.md) |
| `l05-bench/` | [Бенчмарки, профилирование](../../../docs/topics/14-golang-advanced/lecture-05-benchmarks-pprof.md) |

## Запуск

```bash
go run ./l01-concurrency

# в первом терминале
go run ./l03-http/server

# во втором
go run ./l03-http/client
```

## Тесты и бенчмарки

```bash
go test ./...
go test -race ./...
go test -bench=. -benchmem ./l05-bench
```
