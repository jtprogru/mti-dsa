# Лекция 2. Шаблоны проектирования (Design Patterns)

**Шаблоны проектирования** — это руководства по решению повторяющихся проблем. Это не классы, пакеты или библиотеки, которые можно подключить и сидеть в ожидании чуда. Они скорее являются *методиками* решения определённых проблем в определённых ситуациях.

Википедия: «Шаблон проектирования, или паттерн, в разработке программного обеспечения — повторяемая архитектурная конструкция, представляющая собой решение проблемы проектирования, в рамках некоторого часто возникающего контекста».

> **Будьте осторожны:**
>
> - шаблоны не являются решением всех ваших проблем;
> - не пытайтесь использовать их в обязательном порядке — это может привести к негативным последствиям;
> - шаблоны — это подходы к решению проблем, а не решения для поиска проблем;
> - если их правильно использовать в нужных местах, они могут стать спасением, иначе — могут привести к беспорядку.

## Типы шаблонов

Классические шаблоны делятся на три группы:

- **Порождающие** (creational) — отвечают за создание объектов.
- **Структурные** (structural) — связаны с композицией объектов.
- **Поведенческие** (behavioral) — связаны с распределением обязанностей и взаимодействием объектов.

Многие шаблоны проектирования встроены в Python и Go «из коробки» или легко реализуются базовыми возможностями языка.

## Порождающие шаблоны

### Simple Factory (Простая фабрика)

**Простая фабрика** генерирует экземпляр для клиента, не раскрывая логики создания. Используется, когда создание объекта — не просто несколько присвоений, а какая-то логика.

=== "Python"

    ```python
    from abc import ABC, abstractmethod

    class Door(ABC):
        @abstractmethod
        def width(self) -> float: ...
        @abstractmethod
        def height(self) -> float: ...

    class WoodenDoor(Door):
        def __init__(self, w: float, h: float):
            self._w, self._h = w, h
        def width(self) -> float: return self._w
        def height(self) -> float: return self._h

    class DoorFactory:
        @staticmethod
        def make_door(w: float, h: float) -> Door:
            return WoodenDoor(w, h)

    d = DoorFactory.make_door(100, 200)
    print(d.width(), d.height())  # 100 200
    ```

=== "Go"

    ```go
    type Door interface {
        Width() float64
        Height() float64
    }

    type WoodenDoor struct {
        w, h float64
    }

    func (d WoodenDoor) Width() float64  { return d.w }
    func (d WoodenDoor) Height() float64 { return d.h }

    func MakeDoor(w, h float64) Door {
        return WoodenDoor{w: w, h: h}
    }

    func main() {
        d := MakeDoor(100, 200)
        fmt.Println(d.Width(), d.Height())
    }
    ```

### Factory Method (Фабричный метод)

**Фабричный метод** делегирует создание объектов наследникам родительского класса. Это позволяет манипулировать абстрактными объектами на более высоком уровне.

=== "Python"

    ```python
    class Interviewer(ABC):
        @abstractmethod
        def ask_question(self) -> str: ...

    class Developer(Interviewer):
        def ask_question(self) -> str: return "Спросить о шаблонах проектирования"

    class DBA(Interviewer):
        def ask_question(self) -> str: return "Спросить о MySQL"

    class HiringManager(ABC):
        @abstractmethod
        def make_interviewer(self) -> Interviewer: ...

        def get_response(self) -> str:
            return self.make_interviewer().ask_question()

    class DevHiringManager(HiringManager):
        def make_interviewer(self) -> Interviewer:
            return Developer()

    class DBAHiringManager(HiringManager):
        def make_interviewer(self) -> Interviewer:
            return DBA()

    print(DevHiringManager().get_response())   # Спросить о шаблонах
    print(DBAHiringManager().get_response())   # Спросить о MySQL
    ```

=== "Go"

    ```go
    type Interviewer interface {
        AskQuestion() string
    }

    type Developer struct{}
    func (Developer) AskQuestion() string { return "Спросить о шаблонах проектирования" }

    type DBA struct{}
    func (DBA) AskQuestion() string { return "Спросить о MySQL" }

    type HiringManager interface {
        MakeInterviewer() Interviewer
    }

    // GetResponse — общая функция, использующая factory method.
    func GetResponse(m HiringManager) string {
        return m.MakeInterviewer().AskQuestion()
    }

    type DevManager struct{}
    func (DevManager) MakeInterviewer() Interviewer { return Developer{} }

    type DBAManager struct{}
    func (DBAManager) MakeInterviewer() Interviewer { return DBA{} }
    ```

### Abstract Factory (Абстрактная фабрика)

**Абстрактная фабрика** предоставляет интерфейс для создания *семейств* взаимосвязанных объектов, не специфицируя их конкретных классов. «Фабрика фабрик».

=== "Python"

    ```python
    class Door(ABC):
        @abstractmethod
        def describe(self) -> str: ...

    class WoodenDoor(Door):
        def describe(self) -> str: return "Я деревянная дверь"

    class IronDoor(Door):
        def describe(self) -> str: return "Я железная дверь"

    class DoorFitter(ABC):
        @abstractmethod
        def describe(self) -> str: ...

    class Carpenter(DoorFitter):
        def describe(self) -> str: return "Работаю с деревянными дверьми"

    class Welder(DoorFitter):
        def describe(self) -> str: return "Работаю с железными дверьми"

    class DoorFactory(ABC):
        @abstractmethod
        def make_door(self) -> Door: ...
        @abstractmethod
        def make_fitter(self) -> DoorFitter: ...

    class WoodenDoorFactory(DoorFactory):
        def make_door(self) -> Door: return WoodenDoor()
        def make_fitter(self) -> DoorFitter: return Carpenter()

    class IronDoorFactory(DoorFactory):
        def make_door(self) -> Door: return IronDoor()
        def make_fitter(self) -> DoorFitter: return Welder()

    f = WoodenDoorFactory()
    print(f.make_door().describe())    # Я деревянная дверь
    print(f.make_fitter().describe())  # Работаю с деревянными дверьми
    ```

=== "Go"

    ```go
    type Door interface{ Describe() string }
    type DoorFitter interface{ Describe() string }

    type WoodenDoor struct{}
    func (WoodenDoor) Describe() string { return "Я деревянная дверь" }

    type IronDoor struct{}
    func (IronDoor) Describe() string { return "Я железная дверь" }

    type Carpenter struct{}
    func (Carpenter) Describe() string { return "Работаю с деревянными дверьми" }

    type Welder struct{}
    func (Welder) Describe() string { return "Работаю с железными дверьми" }

    type DoorFactory interface {
        MakeDoor() Door
        MakeFitter() DoorFitter
    }

    type WoodenDoorFactory struct{}
    func (WoodenDoorFactory) MakeDoor() Door         { return WoodenDoor{} }
    func (WoodenDoorFactory) MakeFitter() DoorFitter { return Carpenter{} }

    type IronDoorFactory struct{}
    func (IronDoorFactory) MakeDoor() Door         { return IronDoor{} }
    func (IronDoorFactory) MakeFitter() DoorFitter { return Welder{} }
    ```

### Builder (Строитель)

**Строитель** решает проблему *телескопического конструктора* — когда у конструктора слишком много параметров, и не всегда понятно, что они значат.

=== "Python"

    ```python
    class Burger:
        def __init__(self, size: int, cheese: bool, pepperoni: bool, lettuce: bool):
            self.size, self.cheese, self.pepperoni, self.lettuce = size, cheese, pepperoni, lettuce

        def __str__(self):
            parts = [f"размер {self.size}"]
            if self.cheese: parts.append("сыр")
            if self.pepperoni: parts.append("пепперони")
            if self.lettuce: parts.append("салат")
            return ", ".join(parts)

    class BurgerBuilder:
        def __init__(self, size: int):
            self.size = size
            self.cheese = False
            self.pepperoni = False
            self.lettuce = False

        def add_cheese(self):     self.cheese = True; return self
        def add_pepperoni(self):  self.pepperoni = True; return self
        def add_lettuce(self):    self.lettuce = True; return self

        def build(self) -> Burger:
            return Burger(self.size, self.cheese, self.pepperoni, self.lettuce)

    burger = (
        BurgerBuilder(14)
        .add_pepperoni()
        .add_lettuce()
        .build()
    )
    print(burger)  # размер 14, пепперони, салат
    ```

=== "Go"

    ```go
    type Burger struct {
        size                       int
        cheese, pepperoni, lettuce bool
    }

    func (b Burger) String() string {
        parts := []string{fmt.Sprintf("размер %d", b.size)}
        if b.cheese    { parts = append(parts, "сыр") }
        if b.pepperoni { parts = append(parts, "пепперони") }
        if b.lettuce   { parts = append(parts, "салат") }
        return strings.Join(parts, ", ")
    }

    type BurgerBuilder struct {
        size                       int
        cheese, pepperoni, lettuce bool
    }

    func NewBurger(size int) *BurgerBuilder { return &BurgerBuilder{size: size} }
    func (b *BurgerBuilder) AddCheese() *BurgerBuilder    { b.cheese = true; return b }
    func (b *BurgerBuilder) AddPepperoni() *BurgerBuilder { b.pepperoni = true; return b }
    func (b *BurgerBuilder) AddLettuce() *BurgerBuilder   { b.lettuce = true; return b }
    func (b *BurgerBuilder) Build() Burger {
        return Burger{b.size, b.cheese, b.pepperoni, b.lettuce}
    }

    burger := NewBurger(14).AddPepperoni().AddLettuce().Build()
    fmt.Println(burger)
    ```

> **Идиоматичная альтернатива в Python** — параметры по умолчанию + именованные аргументы.
> **Идиоматичная альтернатива в Go** — *functional options*: `NewBurger(14, WithCheese(), WithLettuce())`.

### Prototype (Прототип)

**Прототип** создаёт объект на основе существующего путём клонирования. Уход от реализации, программирование через интерфейсы.

=== "Python"

    ```python
    import copy

    class Sheep:
        def __init__(self, name: str, color: str):
            self.name, self.color = name, color

    dolly = Sheep("Dolly", "white")
    dolly_clone = copy.deepcopy(dolly)
    dolly_clone.name = "Polly"

    print(dolly.name, dolly.color)             # Dolly white
    print(dolly_clone.name, dolly_clone.color) # Polly white
    ```

=== "Go"

    ```go
    type Sheep struct {
        Name, Color string
    }

    func (s Sheep) Clone() Sheep {
        return Sheep{Name: s.Name, Color: s.Color}
    }

    dolly := Sheep{"Dolly", "white"}
    polly := dolly.Clone()
    polly.Name = "Polly"
    ```

> В Go нет встроенного `deepcopy` — глубокое копирование делают явно. Для сложных структур существуют сторонние библиотеки.

### Singleton (Одиночка)

**Одиночка** гарантирует, что в приложении будет *единственный* экземпляр некоторого класса. *Считается антипаттерном* — вводит глобальное состояние, усложняет тестирование. Использовать с осторожностью.

=== "Python"

    ```python
    class Singleton:
        _instance = None

        def __new__(cls, *args, **kwargs):
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    a = Singleton()
    b = Singleton()
    print(a is b)  # True
    ```

=== "Go"

    ```go
    import "sync"

    type config struct{ data string }

    var (
        instance *config
        once     sync.Once
    )

    func GetConfig() *config {
        once.Do(func() {
            instance = &config{data: "loaded"}
        })
        return instance
    }
    ```

> В Go идиоматичен `sync.Once` — гарантирует инициализацию ровно один раз, потокобезопасно.

## Структурные шаблоны

### Adapter (Адаптер)

**Адаптер** позволяет обернуть несовместимые объекты в адаптер, чтобы сделать их совместимыми с другим классом. Карт-ридер, переходник для розетки, переводчик.

=== "Python"

    ```python
    class EuropeanSocket:
        def voltage(self) -> int: return 230

    class USDevice:
        def __init__(self, source):
            self.source = source

        def power(self):
            v = self.source.voltage()
            if v != 110:
                raise ValueError(f"Ожидалось 110V, получено {v}V")
            print("Работает")

    class VoltageAdapter:
        def __init__(self, socket):
            self.socket = socket
        def voltage(self) -> int:
            return self.socket.voltage() // 2  # упрощённо

    # device = USDevice(EuropeanSocket())  # ValueError
    device = USDevice(VoltageAdapter(EuropeanSocket()))
    device.power()  # Работает
    ```

=== "Go"

    ```go
    type Socket interface{ Voltage() int }

    type EuropeanSocket struct{}
    func (EuropeanSocket) Voltage() int { return 230 }

    type VoltageAdapter struct{ s Socket }
    func (a VoltageAdapter) Voltage() int { return a.s.Voltage() / 2 }
    ```

### Bridge (Мост)

**Мост** разделяет абстракцию и реализацию так, чтобы они могли изменяться независимо. Композиция вместо наследования.

=== "Python"

    ```python
    class Theme(ABC):
        @abstractmethod
        def color(self) -> str: ...

    class DarkTheme(Theme):
        def color(self) -> str: return "тёмный"

    class LightTheme(Theme):
        def color(self) -> str: return "светлый"

    class WebPage(ABC):
        def __init__(self, theme: Theme): self.theme = theme
        @abstractmethod
        def render(self) -> str: ...

    class About(WebPage):
        def render(self) -> str:
            return f"Страница 'О нас' в {self.theme.color()} цвете"

    class News(WebPage):
        def render(self) -> str:
            return f"Страница 'Новости' в {self.theme.color()} цвете"

    print(About(DarkTheme()).render())
    print(News(LightTheme()).render())
    ```

### Composite (Компоновщик)

**Компоновщик** объединяет объекты в древовидную структуру для представления иерархии «часть-целое». Позволяет работать с группой объектов так же, как с одиночным.

=== "Python"

    ```python
    class Executor(ABC):
        @abstractmethod
        def can_do(self, task: str) -> bool: ...
        @abstractmethod
        def assign(self, task: str): ...

    class Worker(Executor):
        def __init__(self, name: str):
            self.name = name
        def can_do(self, task: str) -> bool: return True
        def assign(self, task: str):
            print(f"{self.name} получил задачу: {task}")

    class Team(Executor):
        def __init__(self):
            self.members: list[Executor] = []
        def add(self, e: Executor):
            self.members.append(e); return self
        def can_do(self, task: str) -> bool:
            return any(m.can_do(task) for m in self.members)
        def assign(self, task: str):
            if self.members:
                self.members.pop(0).assign(task)

    team = Team().add(Worker("трус")).add(Worker("балбес"))
    team.assign("вскопать грядку")  # трус получил задачу: вскопать грядку
    team.assign("наколоть дров")    # балбес получил задачу: наколоть дров
    ```

### Decorator (Декоратор)

**Декоратор** динамически подключает к объекту дополнительное поведение. В Python — встроенный синтаксис `@decorator`.

=== "Python"

    ```python
    def errors_to_exceptions(fn):
        """Превращает коды ошибок в исключения."""
        errors = {1: "ошибка 1", 2: "ошибка 2"}

        def wrapper(*args, **kwargs):
            code = fn(*args, **kwargs)
            if code == 0:
                return 0
            raise RuntimeError(errors.get(code, f"неизвестный код {code}"))

        return wrapper

    @errors_to_exceptions
    def windows_api_call() -> int:
        return 1  # код ошибки

    try:
        windows_api_call()
    except RuntimeError as e:
        print(e)  # ошибка 1
    ```

=== "Go"

    ```go
    // В Go нет синтаксических декораторов — пишем middleware-функции.
    type APIFunc func() int

    func ErrorsToExceptions(fn APIFunc) func() error {
        errs := map[int]string{1: "ошибка 1", 2: "ошибка 2"}
        return func() error {
            code := fn()
            if code == 0 {
                return nil
            }
            if msg, ok := errs[code]; ok {
                return errors.New(msg)
            }
            return fmt.Errorf("неизвестный код %d", code)
        }
    }
    ```

### Facade (Фасад)

**Фасад** предоставляет упрощённый интерфейс для сложной системы. Кнопка включения компьютера — фасад для подсистем питания, BIOS, ОС.

=== "Python"

    ```python
    class Computer:
        def power_on(self):    print("включение 220V")
        def post(self):         print("POST: бип!")
        def boot_screen(self):  print("Загрузка...")
        def ready(self):        print("Готов к работе")
        def shutdown_apps(self): print("Закрытие приложений")
        def shutdown_os(self):  print("Завершение работы ОС")

    class PowerButton:
        def __init__(self, pc: Computer):
            self.pc = pc

        def on(self):
            self.pc.power_on()
            self.pc.post()
            self.pc.boot_screen()
            self.pc.ready()

        def off(self):
            self.pc.shutdown_apps()
            self.pc.shutdown_os()

    btn = PowerButton(Computer())
    btn.on()
    btn.off()
    ```

### Flyweight (Приспособленец)

**Приспособленец** уменьшает затраты при работе с *большим количеством мелких объектов* за счёт переиспользования. Например, при наряжании ёлки разноцветных лампочек на все ветки можно хранить по одной лампочке каждого цвета.

=== "Python"

    ```python
    class Bulb:
        def __init__(self, color: str):
            self.color = color

    class BulbFactory:
        _bulbs: dict[str, Bulb] = {}

        @classmethod
        def get(cls, color: str) -> Bulb:
            if color not in cls._bulbs:
                cls._bulbs[color] = Bulb(color)
            return cls._bulbs[color]

    a = BulbFactory.get("red")
    b = BulbFactory.get("red")
    print(a is b)  # True — один объект на всё приложение
    ```

### Proxy (Заместитель)

**Заместитель** контролирует доступ к другому объекту, перехватывая все вызовы. Применяется для контроля доступа, ленивой загрузки, кеширования, логирования.

=== "Python"

    ```python
    class Door(ABC):
        @abstractmethod
        def open(self): ...
        @abstractmethod
        def close(self): ...

    class LabDoor(Door):
        def open(self):  print("Открытие двери лаборатории")
        def close(self): print("Закрытие двери лаборатории")

    class Security:
        def __init__(self, door: Door, password: str):
            self._door = door
            self._password = password

        def open(self, password: str):
            if password == self._password:
                self._door.open()
            else:
                print("Доступ запрещён")

        def close(self): self._door.close()

    d = Security(LabDoor(), "$ecr@t")
    d.open("wrong")     # Доступ запрещён
    d.open("$ecr@t")    # Открытие двери лаборатории
    ```

## Поведенческие шаблоны

### Chain of Responsibility (Цепочка обязанностей)

**Цепочка обязанностей** строит цепочки объектов. Запрос проходит через каждый, пока не найдёт подходящий обработчик. Пример — список платёжных методов с разным балансом.

=== "Python"

    ```python
    class Account(ABC):
        def __init__(self, balance: float):
            self._balance = balance
            self._next: Account | None = None

        def set_next(self, account: "Account") -> "Account":
            self._next = account
            return account

        def pay(self, amount: float):
            if self._balance >= amount:
                print(f"Оплата {amount} с {type(self).__name__}")
            elif self._next:
                print(f"Недостаточно средств на {type(self).__name__}, передаём дальше...")
                self._next.pay(amount)
            else:
                raise RuntimeError("Нигде нет средств")

    class Bank(Account): pass
    class Paypal(Account): pass
    class Bitcoin(Account): pass

    bank = Bank(100)
    paypal = Paypal(200)
    bitcoin = Bitcoin(300)
    bank.set_next(paypal).set_next(bitcoin)
    bank.pay(259)
    # Недостаточно средств на Bank, передаём дальше...
    # Недостаточно средств на Paypal, передаём дальше...
    # Оплата 259 с Bitcoin
    ```

### Command (Команда)

**Команда** инкапсулирует действия в объекты — позволяет отделить клиента от получателя, реализовать undo/redo, очереди и историю.

=== "Python"

    ```python
    class Bulb:
        def turn_on(self):  print("Лампочка горит")
        def turn_off(self): print("Темнота")

    class Command(ABC):
        @abstractmethod
        def execute(self): ...
        @abstractmethod
        def undo(self): ...

    class TurnOn(Command):
        def __init__(self, bulb: Bulb): self.bulb = bulb
        def execute(self): self.bulb.turn_on()
        def undo(self):    self.bulb.turn_off()

    class TurnOff(Command):
        def __init__(self, bulb: Bulb): self.bulb = bulb
        def execute(self): self.bulb.turn_off()
        def undo(self):    self.bulb.turn_on()

    class Remote:
        def submit(self, cmd: Command):
            cmd.execute()

    r = Remote()
    bulb = Bulb()
    r.submit(TurnOn(bulb))   # Лампочка горит
    r.submit(TurnOff(bulb))  # Темнота
    ```

### Iterator (Итератор)

**Итератор** даёт последовательный доступ к элементам коллекции без раскрытия её внутреннего устройства. Встроен в Python (`__iter__` / `__next__`) и в Go (`for range`).

```python
class Range:
    def __init__(self, n: int):
        self.n = n
    def __iter__(self):
        i = 0
        while i < self.n:
            yield i
            i += 1

for x in Range(3):
    print(x)  # 0 1 2
```

### Mediator (Посредник)

**Посредник** добавляет стороннего объекта для управления взаимодействием между двумя объектами (коллегами). Уменьшает связанность.

=== "Python"

    ```python
    from datetime import datetime

    class ChatRoom:
        def show(self, user: "User", message: str):
            print(f"[{datetime.now():%H:%M}] {user.name}: {message}")

    class User:
        def __init__(self, name: str, room: ChatRoom):
            self.name, self.room = name, room
        def send(self, message: str):
            self.room.show(self, message)

    room = ChatRoom()
    User("John", room).send("Привет")
    User("Jane", room).send("Привет")
    ```

### Memento (Хранитель)

**Хранитель** фиксирует и сохраняет внутреннее состояние объекта, чтобы позднее восстановить его. Реализация undo в текстовом редакторе.

=== "Python"

    ```python
    class EditorMemento:
        def __init__(self, content: str):
            self._content = content
        @property
        def content(self) -> str:
            return self._content

    class Editor:
        def __init__(self):
            self.content = ""

        def type(self, words: str):
            self.content += (" " if self.content else "") + words

        def save(self) -> EditorMemento:
            return EditorMemento(self.content)

        def restore(self, m: EditorMemento):
            self.content = m.content

    e = Editor()
    e.type("Первое.")
    e.type("Второе.")
    snapshot = e.save()
    e.type("Третье.")
    print(e.content)   # Первое. Второе. Третье.
    e.restore(snapshot)
    print(e.content)   # Первое. Второе.
    ```

### Observer (Наблюдатель)

**Наблюдатель** определяет зависимость между объектами — при изменении состояния одного зависимые от него узнают об этом. Подписчики/издатели.

=== "Python"

    ```python
    class JobPost:
        def __init__(self, title: str): self.title = title

    class JobSeeker:
        def __init__(self, name: str): self.name = name
        def on_job_posted(self, job: JobPost):
            print(f"Привет, {self.name}! Появилась вакансия: {job.title}")

    class JobBoard:
        def __init__(self):
            self._subs: list[JobSeeker] = []
        def subscribe(self, s: JobSeeker):
            self._subs.append(s)
        def post(self, job: JobPost):
            for s in self._subs:
                s.on_job_posted(job)

    board = JobBoard()
    board.subscribe(JobSeeker("John"))
    board.subscribe(JobSeeker("Jane"))
    board.post(JobPost("Software Engineer"))
    ```

### Strategy (Стратегия)

**Стратегия** позволяет переключаться между алгоритмами в зависимости от ситуации (например, разные алгоритмы сортировки для разных объёмов данных).

=== "Python"

    ```python
    class SortStrategy(ABC):
        @abstractmethod
        def sort(self, data: list) -> list: ...

    class BubbleSort(SortStrategy):
        def sort(self, data):
            print("пузырьковая сортировка")
            return sorted(data)  # для краткости

    class QuickSort(SortStrategy):
        def sort(self, data):
            print("быстрая сортировка")
            return sorted(data)

    class Sorter:
        def __init__(self, strategy: SortStrategy):
            self.strategy = strategy
        def sort(self, data: list) -> list:
            return self.strategy.sort(data)

    data = [5, 1, 4, 3, 2]
    Sorter(BubbleSort()).sort(data)
    Sorter(QuickSort()).sort(data)
    ```

=== "Go"

    ```go
    type SortStrategy interface {
        Sort([]int) []int
    }

    type BubbleSort struct{}
    func (BubbleSort) Sort(d []int) []int { fmt.Println("пузырьковая"); return d }

    type QuickSort struct{}
    func (QuickSort) Sort(d []int) []int { fmt.Println("быстрая"); return d }

    type Sorter struct{ s SortStrategy }
    func (s Sorter) Sort(d []int) []int { return s.s.Sort(d) }
    ```

### State (Состояние)

**Состояние** позволяет менять поведение класса при изменении его состояния — например, текстовый редактор с режимами `UPPER`, `lower`, `default`.

=== "Python"

    ```python
    class WritingState(ABC):
        @abstractmethod
        def write(self, words: str): ...

    class UpperCase(WritingState):
        def write(self, words: str): print(words.upper())

    class LowerCase(WritingState):
        def write(self, words: str): print(words.lower())

    class Default(WritingState):
        def write(self, words: str): print(words)

    class TextEditor:
        def __init__(self, state: WritingState):
            self.state = state
        def set_state(self, state: WritingState):
            self.state = state
        def type(self, words: str):
            self.state.write(words)

    e = TextEditor(Default())
    e.type("Первая строка")
    e.set_state(UpperCase())
    e.type("Вторая строка")
    e.set_state(LowerCase())
    e.type("Третья СТРОКА")
    ```

### Template Method (Шаблонный метод)

**Шаблонный метод** определяет каркас выполнения определённого алгоритма, но реализацию самих этапов делегирует дочерним классам.

=== "Python"

    ```python
    class Builder(ABC):
        def build(self):  # шаблонный метод — алгоритм фиксирован
            self.test()
            self.lint()
            self.assemble()
            self.deploy()

        @abstractmethod
        def test(self): ...
        @abstractmethod
        def lint(self): ...
        @abstractmethod
        def assemble(self): ...
        @abstractmethod
        def deploy(self): ...

    class AndroidBuilder(Builder):
        def test(self):     print("Android тесты")
        def lint(self):     print("Android lint")
        def assemble(self): print("Android сборка")
        def deploy(self):   print("Развёртывание Android")

    AndroidBuilder().build()
    ```

### Visitor (Посетитель)

**Посетитель** позволяет добавлять операции для объектов *без модификации самих объектов* — операция вынесена в отдельный класс-посетитель. Полезен, когда количество операций растёт, а иерархия типов стабильна.

=== "Python"

    ```python
    class Animal(ABC):
        @abstractmethod
        def accept(self, op: "AnimalOperation"): ...

    class AnimalOperation(ABC):
        @abstractmethod
        def visit_monkey(self, m: "Monkey"): ...
        @abstractmethod
        def visit_lion(self, l: "Lion"): ...

    class Monkey(Animal):
        def shout(self): print("У-у-а-а!")
        def accept(self, op): op.visit_monkey(self)

    class Lion(Animal):
        def roar(self): print("Рррр!")
        def accept(self, op): op.visit_lion(self)

    class Speak(AnimalOperation):
        def visit_monkey(self, m): m.shout()
        def visit_lion(self, l):   l.roar()

    class Jump(AnimalOperation):
        def visit_monkey(self, m): print("Прыгает на 20 футов!")
        def visit_lion(self, l):   print("Прыгает на 7 футов!")

    monkey, lion = Monkey(), Lion()
    monkey.accept(Speak())   # У-у-а-а!
    lion.accept(Jump())      # Прыгает на 7 футов!
    ```

---

## Что делать с шаблонами на практике

- **Не зубрите имена ради имён.** Главное — *проблема*, которую решает шаблон, и *контекст*, в котором его применять.
- **Не натягивайте.** Сначала появляется проблема — потом шаблон. Не наоборот.
- **Учитывайте идиомы языка.** В Python многое уже реализовано (`@decorator`, `@property`, `with`, итераторы, `dataclasses`); в Go идиоматичны интерфейсы, functional options, embedding. Не нужно копировать Java-фасоны там, где есть более прямой путь.
- **Самое полезное в обиходной разработке:** Factory Method / Abstract Factory, Strategy, Observer, Adapter, Decorator, Singleton (с осторожностью), Iterator (встроен в обоих языках).

## Контрольные вопросы

- На какие три группы делятся шаблоны проектирования?
- В чём разница между Simple Factory и Factory Method?
- Когда применять Abstract Factory вместо обычной фабрики?
- Что такое «телескопический конструктор» и как его решает Builder?
- Чем отличается Decorator от Proxy?
- Что такое антипаттерн? Почему Singleton часто относят к антипаттернам?
- Какие шаблоны естественно «встроены» в Python и Go?
