# Лекция 4. Многопоточность и конкурентность (Concurrency)

С появлением многоядерных процессоров стала общеупотребительной практика распределять нагрузку на все доступные ядра. Существует два основных подхода:

- **Процессы** — независимые программы, не разделяют память. Обмен — через каналы (pipes), сокеты, файлы.
- **Потоки** — единицы выполнения внутри одного процесса, разделяют память. Обмен данными проще, но усложняется управление синхронизацией.

В Python и Go подходы к конкурентности заметно различаются — рассмотрим оба.

## Процессы в Python

Модуль `subprocess` позволяет запускать внешние программы:

```python
import subprocess

# Простой запуск
result = subprocess.run(
    ["ls", "-la"],
    capture_output=True, text=True, check=True,
)
print(result.stdout)

# Запуск с передачей stdin и контролем процесса
pipe = subprocess.Popen(
    [sys.executable, "child.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
)
out, err = pipe.communicate(input=b"word\nfile.txt\n")
```

Для параллельного выполнения CPU-bound задач — `multiprocessing` (обходит GIL за счёт отдельных процессов):

```python
from multiprocessing import Pool

def square(n: int) -> int:
    return n * n

with Pool(processes=4) as pool:
    results = pool.map(square, range(10))
    print(results)  # [0, 1, 4, 9, ...]
```

## Потоки в Python (`threading`)

Модуль `threading` предоставляет класс `Thread`. Можно унаследоваться или передать целевую функцию:

```python
import threading

# Способ 1: через целевую функцию
def worker(name: str):
    print(f"Привет от {name}")

t = threading.Thread(target=worker, args=("Bob",))
t.start()
t.join()  # ждём завершения

# Способ 2: через наследование
class MyThread(threading.Thread):
    def run(self):
        print("Я запускаюсь в отдельном потоке")

MyThread().start()
```

Основные методы класса `Thread`:

| Метод | Назначение |
|-------|-----------|
| `start()` | Запускает поток (вызывает `run()` в отдельном потоке) |
| `run()` | Действия потока — переопределяется в подклассе |
| `join([timeout])` | Ждать завершения потока (опционально с таймаутом) |
| `is_alive()` | Возвращает True, если поток работает |
| `daemon` (свойство) | Признак «демона» — фоновый поток, не мешает выходу из программы |

## GIL — глобальная блокировка интерпретатора

> Python слывёт дружелюбным и простым, но есть у него причуды: нельзя просто взять и воспользоваться всеми преимуществами многопоточности. Дорогу преградит **GIL** (Global Interpreter Lock) — глобальный шлюз, ограничивающий многопоточность на уровне интерпретатора.

GIL — это один на всех мьютекс, гарантирующий, что в каждый момент только один поток исполняет байт-код Python. Технически это сделано для безопасности встроенных типов и упрощения интеграции с C-расширениями.

**Последствия:**

- CPU-bound задачи *не ускоряются* от потоков — даже на N ядер скорость остаётся как на одном.
- I/O-bound задачи (сеть, диск) *выигрывают*: GIL отпускается на время блокирующих операций.

Пример из *Understanding Python GIL* (Chetan Giridhar):

```python
from datetime import datetime
import threading

def factorial(number):
    fact = 1
    for n in range(1, number + 1):
        fact *= n
    return fact

start = datetime.now()
t1 = threading.Thread(target=factorial, args=(100_000,))
t2 = threading.Thread(target=factorial, args=(100_000,))
t1.start(); t2.start()
t1.join();  t2.join()
print("Время:", datetime.now() - start)
```

На двух «параллельных» потоках расчёт идёт *дольше*, чем на одном — расходы на переключение контекстов GIL.

> **Тенденция: PEP 703 и free-threading.** Начиная с Python 3.13 в экспериментальном режиме доступна сборка интерпретатора без GIL. Подробнее: <https://peps.python.org/pep-0703/>.

### Когда что использовать в Python

- **I/O-bound** (сеть, диск): `threading` или `asyncio`.
- **CPU-bound** (вычисления): `multiprocessing` или внешние библиотеки на C/Rust (NumPy, Polars).
- **Большие параллельные I/O** (тысячи соединений): `asyncio`.

## Очереди и пул потоков

При создании большого числа потоков приложение замедляется — каждый поток требует ресурсов ОС. Решение — *пул потоков* (thread pool) с фиксированным числом потоков, переиспользующих ресурсы.

Стандартный модуль `concurrent.futures` даёт высокоуровневый интерфейс:

```python
from concurrent.futures import ThreadPoolExecutor
import requests

def fetch(url: str) -> int:
    r = requests.get(url, timeout=5)
    return r.status_code

urls = [
    "https://httpbin.org/get",
    "https://github.com",
    "https://python.org",
]

with ThreadPoolExecutor(max_workers=3) as pool:
    for url, status in zip(urls, pool.map(fetch, urls)):
        print(url, status)
```

Для CPU-bound задач — `ProcessPoolExecutor` (тот же API, но процессы):

```python
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(factorial, [10000, 20000, 30000]))
```

## Блокировки (`Lock`)

Когда несколько потоков обращаются к *общему изменяемому состоянию*, нужны блокировки.

```python
import threading

counter = 0
lock = threading.Lock()

def increment(n: int):
    global counter
    for _ in range(n):
        with lock:
            counter += 1  # атомарный инкремент

threads = [threading.Thread(target=increment, args=(100_000,)) for _ in range(4)]
for t in threads: t.start()
for t in threads: t.join()
print(counter)  # 400000 — без lock могло бы быть меньше
```

**Дедлок** возникает, если два потока удерживают по одному ресурсу и ждут друг друга:

- Поток 1: `lock_A.acquire()`, потом `lock_B.acquire()`.
- Поток 2: `lock_B.acquire()`, потом `lock_A.acquire()`.

→ Бесконечное ожидание.

**Правило:** если поток должен взять несколько блокировок — *всегда брать их в одном и том же порядке*.

## Конкурентность в Go: горутины и каналы

Go был спроектирован вокруг конкурентности с самого начала. Модель — *CSP* (Communicating Sequential Processes): «не разделяйте память для коммуникации — коммуницируйте, чтобы разделить память».

### Горутины

**Горутина** — лёгкая функция, исполняемая конкурентно. Размер стека — стартует с 2 KB (vs 1–8 MB у потока ОС). Рантайм Go мультиплексирует тысячи горутин на N потоков ОС.

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

func say(msg string) {
    for i := 0; i < 3; i++ {
        fmt.Println(msg, i)
        time.Sleep(100 * time.Millisecond)
    }
}

func main() {
    go say("hello")  // в отдельной горутине
    go say("world")  // в отдельной горутине
    time.Sleep(time.Second)
}
```

### `sync.WaitGroup` — ожидание группы горутин

Аналог `Thread.join()`:

```go
var wg sync.WaitGroup
for _, url := range urls {
    wg.Add(1)
    go func(u string) {
        defer wg.Done()
        fetch(u)
    }(url)
}
wg.Wait()
```

### Каналы

**Каналы** — типизированные конвейеры для обмена значениями между горутинами:

```go
ch := make(chan int)        // небуферизированный
ch := make(chan int, 100)   // буфер на 100 элементов

ch <- 42        // отправить
v := <-ch       // получить
close(ch)       // закрыть

// перебор канала до его закрытия
for v := range ch {
    fmt.Println(v)
}
```

Каналы — *первоклассные* объекты Go; их передают как параметры, возвращают из функций.

### `select` — мультиплексирование каналов

```go
select {
case msg := <-ch1:
    fmt.Println("из ch1:", msg)
case msg := <-ch2:
    fmt.Println("из ch2:", msg)
case <-time.After(time.Second):
    fmt.Println("таймаут")
}
```

### Пример: worker pool на горутинах

```go
package main

import (
    "fmt"
    "sync"
)

func worker(id int, jobs <-chan int, results chan<- int, wg *sync.WaitGroup) {
    defer wg.Done()
    for j := range jobs {
        results <- j * 2
        fmt.Printf("worker %d обработал %d\n", id, j)
    }
}

func main() {
    jobs := make(chan int, 100)
    results := make(chan int, 100)

    var wg sync.WaitGroup
    for w := 1; w <= 3; w++ {
        wg.Add(1)
        go worker(w, jobs, results, &wg)
    }

    for j := 1; j <= 5; j++ {
        jobs <- j
    }
    close(jobs)

    go func() {
        wg.Wait()
        close(results)
    }()

    for r := range results {
        fmt.Println("результат:", r)
    }
}
```

### `sync.Mutex` — блокировки в Go

Когда без shared memory не обойтись — есть классические мьютексы:

```go
var (
    counter int
    mu      sync.Mutex
)

func increment(n int, wg *sync.WaitGroup) {
    defer wg.Done()
    for i := 0; i < n; i++ {
        mu.Lock()
        counter++
        mu.Unlock()
    }
}
```

Также есть `sync.RWMutex` (отдельный режим для читателей), `sync.Once` (однократная инициализация), `sync/atomic` (атомарные операции).

## `context.Context` — отмена и таймауты

В Go для управления жизненным циклом долгих операций используют `context.Context`:

```go
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
resp, err := http.DefaultClient.Do(req)
// если запрос займёт больше 5 секунд — будет ошибка context.DeadlineExceeded
```

В Python аналог — `asyncio.wait_for(coro, timeout=5.0)`.

## Сравнение моделей конкурентности

| Аспект | Python (threading) | Python (asyncio) | Go (goroutines) |
|--------|---------------------|------------------|------------------|
| Единица | поток ОС | задача (coroutine) | горутина |
| Размер | ~1 MB стек | ~2 KB | ~2 KB |
| Сколько можно | сотни | сотни тысяч | миллионы |
| Параллелизм CPU | ограничен GIL | нет | да (N ядер) |
| Параллелизм I/O | да | да | да |
| Синтаксис | обычные функции | `async def` / `await` | `go func()` |
| Коммуникация | shared memory + `Lock`/`Queue` | shared memory + `asyncio.Queue` | каналы + опционально mutex |

## Заключение

- Параллельное программирование стало необходимостью из-за роста многоядерных процессоров.
- В Python: для I/O-bound — `threading` или `asyncio`; для CPU-bound — `multiprocessing` или вынос в C/Rust.
- В Go: горутины и каналы — *идиоматичный* и *эффективный* способ конкурентности по умолчанию.
- В обоих языках критично избегать состояний гонки (race conditions) и дедлоков. Полезные инструменты — race detector (`go test -race`) и `threading`-аналитика (`py-spy`).

## Контрольные вопросы

- Что такое GIL? Какие задачи он *не* ускоряет в потоках?
- Какие альтернативы threading есть в Python для CPU-bound и I/O-bound задач?
- Что такое горутина? Чем она отличается от потока ОС?
- Что такое канал в Go? Чем буферизированный канал отличается от небуферизированного?
- Что такое дедлок? Как его избежать?
- Зачем нужен `context.Context` в Go?
- Сравните `concurrent.futures.ThreadPoolExecutor` в Python и worker pool на горутинах в Go.
