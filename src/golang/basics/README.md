# Примеры к теме 13 — Основы Go

Каждая поддиректория — отдельная мини-программа, иллюстрирующая материал лекции.

| Директория | Лекция |
|-----------|--------|
| `l01-intro/` | [Знакомство с Go](../../../docs/topics/13-golang-basics/lecture-01-intro.md) |
| `l02-types/` | [Переменные, типы и управляющие конструкции](../../../docs/topics/13-golang-basics/lecture-02-types-control-flow.md) |
| `l03-functions/` | [Функции, ошибки и `panic`/`recover`](../../../docs/topics/13-golang-basics/lecture-03-functions-errors.md) |
| `l04-composite/` | [Композитные типы](../../../docs/topics/13-golang-basics/lecture-04-composite-types.md) |
| `l05-interfaces/` | [Методы и интерфейсы](../../../docs/topics/13-golang-basics/lecture-05-methods-interfaces.md) |
| `l06-packages/` | [Пакеты и тестирование](../../../docs/topics/13-golang-basics/lecture-06-packages-testing.md) |

## Запуск

```bash
cd l01-intro
go run .
```

Или собрать:

```bash
go build -o bin/intro ./l01-intro
./bin/intro
```

Тесты:

```bash
go test ./...
```
