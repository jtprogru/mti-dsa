# Тема 13. Основы Go (Golang Basics)

Курс параллельно даёт Python и Go. В темах 1–12 Go встречался эпизодически — как параллель к Python (срезы vs списки, struct vs dataclass, error vs exception). В этой теме разбираемся в Go системно: установка, типы, функции, ошибки, композитные структуры, методы и интерфейсы, пакеты и тестирование.

Лекции рассчитаны на студента, который уже изучил Python (темы 1–12) и теперь хочет понять, как те же задачи решаются в статически типизированном компилируемом языке.

## Лекции

1. [Знакомство с Go](lecture-01-intro.md) — история, установка, `go mod`, первая программа, инструментарий (`gofmt`, `golangci-lint`, VS Code).
2. [Переменные, типы и управляющие конструкции](lecture-02-types-control-flow.md) — `var`/`const`/`iota`, числовые типы, `if`/`for`/`switch`, `defer`, указатели.
3. [Функции, ошибки и `panic`/`recover`](lecture-03-functions-errors.md) — multiple return, variadic, замыкания, functional options; `error` как значение, `errors.Is`/`errors.As`, оборачивание через `%w`.
4. [Композитные типы](lecture-04-composite-types.md) — массивы, срезы (slice header), карты, структуры, теги, embedding.
5. [Методы и интерфейсы](lecture-05-methods-interfaces.md) — value vs pointer receiver, structural typing, `any`, type assertion и type switch, канонические интерфейсы stdlib, дженерики.
6. [Пакеты и тестирование](lecture-06-packages-testing.md) — пакеты и видимость, `internal/`, `go mod`, `go.sum`, `testing`, table-driven tests, бенчмарки, fuzz.

## Что дальше

Тема 14 — продвинутые темы Go: конкурентность (горутины, каналы, `select`), контексты, HTTP, работа с БД через `database/sql`, профилирование и race detector.
