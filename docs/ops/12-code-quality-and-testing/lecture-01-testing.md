# Лекция 1. Качество кода и тестирование (Code Quality and Testing)

Трудно представить современный программный проект без тестирования. Тестирование осуществляется практически на всех этапах разработки: от unit-тестов (а иногда и раньше — при TDD) до функционального и нагрузочного тестирования готового продукта.

В этой лекции остановимся на *автономном тестировании* (unit-тестировании).

## Автономное тестирование. Основные понятия

> **Автономный тест** — автоматизированная часть кода, которая вызывает тестируемую единицу работы и затем проверяет некоторые предположения о её конечном результате.
> — Рой Ошероув, «Искусство автономного тестирования»

В качестве *тестируемой единицы* может выступать как отдельная функция/метод, так и совокупность классов. Идея — единица представляет логически законченную сущность программы.

Автономное тестирование называют также *модульным* или *unit-тестированием*. Далее «тест» = unit-тест.

> **Важная характеристика unit-теста — повторяемость.** Результат не должен зависеть от окружения. Если приходится обращаться к внешнему миру (БД, сеть, файловая система), нужно подменять «мир» заглушкой (mock/fake/stub).

## Фреймворки для unit-тестирования в Python

Самые распространённые:

- **`unittest`** — стандартный, входит в библиотеку Python. Архитектура в стиле xUnit (JUnit, NUnit).
- **`pytest`** — мощный сторонний фреймворк, ближе к «духу» Python. Тесты — обычные функции с `assert`, нет необходимости создавать классы.
- **`nose2`** — продолжение `nose`. Расширяет `unittest`.

В современной индустрии де-факто стандарт — `pytest`.

## Без фреймворка — наивный подход

Простой модуль для калькулятора:

```python
# calc.py

def add(a, b): return a + b
def sub(a, b): return a - b
def mul(a, b): return a * b
def div(a, b): return a / b
```

Тесты «вручную»:

```python
# test_calc.py
import calc

def test_add():
    if calc.add(1, 2) == 3:
        print("test_add OK")
    else:
        print("test_add FAIL")

def test_sub():
    if calc.sub(4, 2) == 2:
        print("test_sub OK")
    else:
        print("test_sub FAIL")

test_add()
test_sub()
```

Проблемы такого подхода:

- неунифицированная выходная информация;
- громоздкий код;
- нужно думать про архитектуру тестов;
- нет инструментов фильтрации, пропуска, сборки в группы.

Это приводит к мысли о том, что нужен фреймворк.

## `unittest` — стандартный фреймворк

```python
# tests/test_calc.py
import unittest
import calc

class CalcTest(unittest.TestCase):
    def test_add(self):
        self.assertEqual(calc.add(1, 2), 3)

    def test_sub(self):
        self.assertEqual(calc.sub(4, 2), 2)

    def test_mul(self):
        self.assertEqual(calc.mul(2, 5), 10)

    def test_div(self):
        self.assertEqual(calc.div(8, 4), 2)

    def test_div_zero(self):
        with self.assertRaises(ZeroDivisionError):
            calc.div(1, 0)

if __name__ == "__main__":
    unittest.main()
```

Запуск:

```bash
python -m unittest tests/test_calc.py        # минимум информации
python -m unittest -v tests/test_calc.py     # подробно
python -m unittest                            # test discovery — найдёт все test_*.py
```

### Структурные элементы unittest

- **Test fixture** — подготовка окружения для тестов и очистка после (`setUp`, `tearDown`).
- **Test case** — элементарная единица тестирования. Класс-наследник `TestCase`.
- **Test suite** — коллекция тестов или других suite.
- **Test runner** — компонент, оркестрирующий запуск и предоставляющий результат.

### Методы при запуске тестов

| Метод | Когда вызывается | Декоратор |
|-------|------------------|-----------|
| `setUp()` | Перед каждым тестом | — |
| `tearDown()` | После каждого теста | — |
| `setUpClass(cls)` | Один раз перед всеми тестами класса | `@classmethod` |
| `tearDownClass(cls)` | Один раз после всех тестов класса | `@classmethod` |
| `setUpModule()` / `tearDownModule()` | На уровне модуля | — |

```python
class CalcTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("setUpClass — один раз")

    @classmethod
    def tearDownClass(cls):
        print("tearDownClass — один раз")

    def setUp(self):
        print(f"Set up for [{self.shortDescription()}]")

    def tearDown(self):
        print(f"Tear down for [{self.shortDescription()}]")

    def test_add(self):
        """Add operation test"""
        self.assertEqual(calc.add(1, 2), 3)
```

### Основные assert-методы

| Метод                       | Эквивалент              |
|-----------------------------|-------------------------|
| `assertEqual(a, b)`         | `a == b`                |
| `assertNotEqual(a, b)`      | `a != b`                |
| `assertTrue(x)`             | `bool(x) is True`       |
| `assertFalse(x)`            | `bool(x) is False`      |
| `assertIs(a, b)`            | `a is b`                |
| `assertIsNone(x)`           | `x is None`             |
| `assertIn(a, b)`            | `a in b`                |
| `assertIsInstance(a, cls)`  | `isinstance(a, cls)`    |
| `assertRaises(exc)`         | контекстный менеджер для проверки исключения |
| `assertAlmostEqual(a, b)`   | `round(a-b, 7) == 0` (для float) |
| `assertGreater(a, b)`       | `a > b`                 |
| `assertRegex(s, r)`         | регулярка `r` находит в строке `s` |

### Пропуск тестов

```python
import sys

class CalcTest(unittest.TestCase):
    @unittest.skip("причина пропуска")
    def test_skip(self):
        self.fail("не должен выполниться")

    @unittest.skipIf(sys.platform == "win32", "только не Windows")
    def test_unix(self):
        ...

    @unittest.expectedFailure
    def test_known_bug(self):
        self.assertEqual(1, 2)
```

## `pytest` — рекомендуемая альтернатива

```python
# tests/test_calc.py
import pytest
import calc

def test_add():
    assert calc.add(1, 2) == 3

def test_div_zero():
    with pytest.raises(ZeroDivisionError):
        calc.div(1, 0)

@pytest.mark.parametrize("a, b, expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
    (100, 200, 300),
])
def test_add_param(a, b, expected):
    assert calc.add(a, b) == expected
```

Запуск:

```bash
pip install pytest
pytest                # найдёт и запустит все test_*.py
pytest -v             # подробно
pytest -k "div"       # только тесты, содержащие "div" в имени
pytest --lf           # повторить только упавшие
```

Преимущества `pytest`:

- обычный `assert` (без `self.assertEqual(...)`);
- *параметризация* (`@pytest.mark.parametrize`) — один тест на N наборов данных;
- *fixtures* — мощная замена `setUp/tearDown`;
- богатая экосистема плагинов (`pytest-cov` для покрытия, `pytest-asyncio`, `pytest-mock`).

### Pytest fixtures

```python
import pytest

@pytest.fixture
def sample_data():
    """Подготовка данных для теста — переиспользуется в нескольких тестах."""
    return [1, 2, 3, 4, 5]

def test_sum(sample_data):
    assert sum(sample_data) == 15

def test_max(sample_data):
    assert max(sample_data) == 5
```

## Тестирование в Go (`testing`)

Встроенный пакет — никаких сторонних фреймворков не нужно (хотя есть `testify` для удобных assert).

```go
// calc.go
package calc

func Add(a, b int) int { return a + b }
func Sub(a, b int) int { return a - b }
func Mul(a, b int) int { return a * b }
func Div(a, b int) int { return a / b }
```

```go
// calc_test.go
package calc

import "testing"

func TestAdd(t *testing.T) {
    got := Add(1, 2)
    if got != 3 {
        t.Errorf("Add(1, 2) = %d; want 3", got)
    }
}

func TestSub(t *testing.T) {
    got := Sub(4, 2)
    if got != 2 {
        t.Errorf("Sub(4, 2) = %d; want 2", got)
    }
}
```

Запуск:

```bash
go test                    # тесты в текущем пакете
go test -v                 # подробно
go test ./...              # все пакеты рекурсивно
go test -run TestAdd       # только тесты с именем, содержащим TestAdd
go test -race              # с обнаружением гонок
go test -cover             # с покрытием
```

### Табличные тесты (table-driven tests) — идиома Go

Аналог `parametrize`:

```go
func TestAddTable(t *testing.T) {
    tests := []struct {
        name     string
        a, b     int
        expected int
    }{
        {"simple", 1, 2, 3},
        {"zero", 0, 0, 0},
        {"negative", -1, 1, 0},
        {"large", 100, 200, 300},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := Add(tt.a, tt.b)
            if got != tt.expected {
                t.Errorf("Add(%d, %d) = %d; want %d", tt.a, tt.b, got, tt.expected)
            }
        })
    }
}
```

### Бенчмарки в Go

```go
func BenchmarkAdd(b *testing.B) {
    for i := 0; i < b.N; i++ {
        Add(123, 456)
    }
}
```

Запуск: `go test -bench=.` — `b.N` подбирается автоматически.

## Покрытие кода (coverage)

```bash
# Python с pytest
pytest --cov=calc --cov-report=term-missing

# Go
go test -cover ./...
go test -coverprofile=cover.out && go tool cover -html=cover.out
```

> Высокое покрытие — *не* гарантия качества. Покрытие 80%+ ≠ нет багов. Качество тестов важнее количества.

## Что должен тестировать unit-тест

- ✅ **Логику** одной функции / метода / класса.
- ✅ **Граничные случаи** (пустой ввод, нули, максимумы, отрицательные числа).
- ✅ **Ожидаемые исключения** на некорректных входных данных.
- ❌ **Не** должен ходить в сеть, БД, файловую систему без моков.
- ❌ **Не** должен зависеть от порядка запуска других тестов.

## Что использовать в больших проектах

- **Python:** `pytest` + `pytest-cov` + `pytest-mock` + `tox` (для матрицы версий) + линтеры (`ruff`, `mypy`).
- **Go:** встроенный `testing` + `testify` (опционально) + race detector (`-race`) + `golangci-lint`.

## Контрольные вопросы

- Что такое unit-тест? Почему важна *повторяемость*?
- В чём ключевые отличия `unittest` и `pytest`?
- Что такое test fixture? Какие методы есть в `unittest.TestCase` для подготовки и очистки?
- Что такое параметризованный тест? Покажите пример.
- Что такое табличные тесты в Go? В чём их преимущество?
- Что такое покрытие кода? Гарантирует ли 100 %-ное покрытие отсутствие багов?
- Какие данные *не* должны быть в unit-тестах (что нужно мокать)?
