# Лекция 5. Бенчмарки, профилирование, race detector

## Бенчмарки

Бенчмарки в Go — часть встроенного `testing`. Файл всё тот же `*_test.go`, функция начинается с `Benchmark`:

```go
// mathx_test.go
package mathx

import "testing"

func BenchmarkSum(b *testing.B) {
    for i := 0; i < b.N; i++ {
        _ = Sum(1, 2)
    }
}
```

Запуск:

```bash
go test -bench=. -benchmem
```

- `-bench=.` — запустить все бенчмарки (regex по имени). `-bench=Sum` — только конкретные.
- `-benchmem` — показать аллокации.

Пример вывода:

```text
goos: darwin
goarch: arm64
pkg: example/mathx
BenchmarkSum-10    1000000000    0.3145 ns/op    0 B/op    0 allocs/op
PASS
```

Что значит:

- `-10` — `GOMAXPROCS`;
- `1000000000` — сколько итераций успело выполниться (`b.N`);
- `0.3145 ns/op` — наносекунд на одну итерацию;
- `0 B/op` — байт аллоцировано на итерацию;
- `0 allocs/op` — сколько отдельных аллокаций.

Раннер сам подбирает `b.N`, увеличивая его, пока бенчмарк не отработает достаточно долго (по умолчанию 1 секунду). Ваша задача — написать тело цикла.

### `b.ResetTimer`, `b.StopTimer`, `b.StartTimer`

Если перед измерением нужна дорогая подготовка:

```go
func BenchmarkParse(b *testing.B) {
    data := loadBigFile()   // подготовка
    b.ResetTimer()           // обнулить таймер — не учитывать подготовку
    for i := 0; i < b.N; i++ {
        _ = parse(data)
    }
}
```

### Под-бенчмарки и сравнение версий

```go
func BenchmarkAlgo(b *testing.B) {
    sizes := []int{10, 100, 1000, 10000}
    for _, n := range sizes {
        b.Run(fmt.Sprintf("n=%d", n), func(b *testing.B) {
            data := randomSlice(n)
            b.ResetTimer()
            for i := 0; i < b.N; i++ {
                _ = sort(data)
            }
        })
    }
}
```

### `benchstat` — статистическая сравнение

Бенчмарки шумят. Сравнивать «было 10ns/op, стало 9ns/op» бессмысленно — это в пределах шума. Утилита `benchstat` ([golang.org/x/perf/cmd/benchstat](https://pkg.go.dev/golang.org/x/perf/cmd/benchstat)) запускает несколько прогонов и считает статистически значимое отличие:

```bash
go install golang.org/x/perf/cmd/benchstat@latest

go test -bench=. -benchmem -count=10 > old.txt
# ... вносим изменения ...
go test -bench=. -benchmem -count=10 > new.txt

benchstat old.txt new.txt
```

В выводе будет что-то вроде:

```text
                  │   old.txt   │              new.txt              │
                  │   sec/op    │   sec/op     vs base              │
Sum-10              0.315n ± 2%   0.207n ± 1%  -34.29% (p=0.000)
```

`p=0.000` — статистически достоверная разница.

## Профилирование с `pprof`

`pprof` — стандартный профилировщик Go. Собирает CPU и memory профили, строит call graphs и flame graphs.

### Профиль через бенчмарки

```bash
go test -bench=. -cpuprofile=cpu.prof -memprofile=mem.prof
go tool pprof cpu.prof
```

В интерактивном режиме:

```text
(pprof) top                # топ функций по времени
(pprof) top -cum           # с накопительным временем
(pprof) list FunctionName  # построчно
(pprof) web                # SVG call graph (нужен Graphviz)
```

Или сразу веб-интерфейс с flame graph:

```bash
go tool pprof -http=:8081 cpu.prof
```

### Профилирование живого сервера

Подключите `net/http/pprof` — он зарегистрирует обработчики `/debug/pprof/*` на `DefaultServeMux`:

```go
import _ "net/http/pprof"

go func() {
    log.Println(http.ListenAndServe("localhost:6060", nil))
}()
```

Снять профиль:

```bash
# 30 секунд CPU-профиля
go tool pprof -http=:8081 http://localhost:6060/debug/pprof/profile?seconds=30

# текущая хип-память
go tool pprof http://localhost:6060/debug/pprof/heap

# горутины
curl http://localhost:6060/debug/pprof/goroutine?debug=1
```

В продакшене pprof-эндпоинт не выставляйте наружу — слушайте только на `localhost` или за внутренней авторизацией.

### Что искать в профиле

- **CPU**: какая функция съедает большую часть времени? Часто ответ — неожиданный (regex, JSON-парсинг, форматирование строк, лишний `time.Now()` в горячем цикле).
- **Heap**: где аллокации? Каждая аллокация → нагрузка на GC. Часто можно переиспользовать буферы (`sync.Pool`, `bytes.Buffer.Reset()`).
- **Goroutines**: их растущее количество — признак утечки.

## Race detector

В прошлой теме обсуждали гонки. Включается флагом `-race`:

```bash
go test -race ./...
go run -race main.go
go build -race -o app
```

Что внутри: компилятор инструментирует обращения к памяти, рантайм отслеживает порядок доступа. Если две горутины обращаются к одной переменной без явного happens-before — печатает диагностику:

```text
WARNING: DATA RACE
Read at 0x00c0000180a0 by goroutine 7:
  main.read()
      /tmp/race/main.go:18 +0x39
Previous write at 0x00c0000180a0 by goroutine 6:
  main.write()
      /tmp/race/main.go:13 +0x46
```

Цена: программа замедляется в 2–10 раз и съедает больше памяти. Поэтому `-race` обычно не включают в продакшен-сборку, но **обязательно гоняйте тесты с `-race` в CI**. Хотя бы критические пакеты.

## Escape analysis

Компилятор Go решает, где жить переменной — на стеке или в куче. Стек — дешёво (просто инкремент SP, освобождение бесплатное при return). Куча — нагрузка на GC. Если переменная «утекает» — берёт на себя ссылка, которая живёт дольше функции — её перемещают в кучу.

Посмотреть решения компилятора:

```bash
go build -gcflags="-m" ./...
```

```text
./main.go:5:6: can inline foo
./main.go:6:11: x escapes to heap
```

Типичные причины утечки в кучу:

- возврат указателя на локальную переменную;
- передача значения в `interface{}` (приходится «упаковывать»);
- захват переменной в long-lived замыкании или горутине;
- слайс/мапа неизвестного на этапе компиляции размера.

Зная эти причины, можно переписать горячий код так, чтобы аллокаций было меньше. Но **не оптимизируйте заранее** — сначала измерьте.

## `sync.Pool` — переиспользование объектов

Если аллокации в горячем пути неизбежны (например, парсинг сообщений), используйте `sync.Pool`:

```go
var bufPool = sync.Pool{
    New: func() any {
        return new(bytes.Buffer)
    },
}

func handle(data []byte) string {
    buf := bufPool.Get().(*bytes.Buffer)
    defer func() {
        buf.Reset()
        bufPool.Put(buf)
    }()
    buf.Write(data)
    // ... обработка ...
    return buf.String()
}
```

`Pool` — это «кеш с возможностью внезапной очистки между GC-циклами». Поэтому **не храните там объекты, у которых должно быть гарантированное состояние** — только то, что можно пересоздать.

## Continuous profiling

В большом продакшене статические `pprof`-снимки заменяют непрерывным профилированием — Pyroscope, Polar Signals, или встроенный Datadog Profiler. Они собирают профили 24/7 и позволяют сравнивать «до релиза / после релиза», находить регрессии без воспроизведения.

## Параллель с Python

| Python                                       | Go                                                |
|----------------------------------------------|----------------------------------------------------|
| `timeit.timeit(...)`                         | `go test -bench`                                  |
| `pytest-benchmark`                           | `Benchmark*` функции в `*_test.go`                 |
| `cProfile`, `py-spy`, `scalene`              | `pprof` (`net/http/pprof`, `go tool pprof`)        |
| flame graph через `py-spy --output`          | `go tool pprof -http`                              |
| `tracemalloc`                                | mem profile из `pprof`                             |
| детектор гонок отсутствует                   | `go test -race`, `go run -race`                    |
| Pyroscope для непрерывного                   | Pyroscope тоже (поддерживает Go)                    |

## Итог

`go test -bench` + `benchstat` — нормальный workflow для измерения. `pprof` — встроенный профилировщик, доступен и из тестов, и через `net/http/pprof` в живом сервере. `-race` обязателен в CI для конкурентного кода. `escape analysis` (`-gcflags="-m"`) объясняет, что попало в кучу. `sync.Pool` — для переиспользования объектов в горячих путях. На этом курс по Go завершается; реальные проекты — лучшая практика.
