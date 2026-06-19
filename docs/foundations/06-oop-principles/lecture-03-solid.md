# Лекция 3. SOLID-принципы (SOLID Principles)

В [лекции 1](lecture-01-oop-basics.md) вы познакомились с базовыми понятиями ООП — классы, объекты, инкапсуляция, наследование, полиморфизм. В [теме 9, лекция 2](../09-class-hierarchies/lecture-02-patterns.md) разобраны 23 шаблона проектирования GoF — конкретные рецепты «как делать». **SOLID** — это пять принципов, которые подсказывают, **почему один дизайн лучше другого**: критерии оценки, а не готовые рецепты.

Аббревиатура SOLID предложена Робертом Мартином («Дядя Боб») в начале 2000-х, на основе работ Бертрана Мейера и Барбары Лисков:

| Буква | Принцип | Идея в одной фразе |
|-------|---------|--------------------|
| **S** | Single Responsibility | У класса должна быть одна причина измениться. |
| **O** | Open/Closed | Открыт для расширения, закрыт для изменения. |
| **L** | Liskov Substitution | Наследник должен быть полноценной заменой родителя. |
| **I** | Interface Segregation | Много мелких интерфейсов лучше одного большого. |
| **D** | Dependency Inversion | Завись от абстракций, не от деталей. |

Принципы универсальны: они работают и в классическом ООП (Python, Java), и в Go с его структурным набором типов и неявными интерфейсами. Где идиоматика отличается — мы покажем это на параллельных примерах.

## S — Single Responsibility Principle (SRP)

> «Класс должен иметь одну и только одну причину для изменения.»

«Причина измениться» — не «делает одну вещь», а **обслуживает одного заказчика**. У отчёта три причины измениться: бухгалтерия меняет формулы, дизайнер — формат, devops — место хранения. Если все три ответственности живут в одном классе, любое изменение одного заказчика рискует сломать остальных.

### Антипример

=== "Python"

    ```python
    class Report:
        def __init__(self, rows: list[dict]) -> None:
            self.rows = rows

        def calculate_totals(self) -> float:
            return sum(r["amount"] for r in self.rows)

        def render_html(self) -> str:
            html = "<table>"
            for r in self.rows:
                html += f"<tr><td>{r['name']}</td><td>{r['amount']}</td></tr>"
            html += "</table>"
            return html

        def save_to_disk(self, path: str) -> None:
            with open(path, "w") as f:
                f.write(self.render_html())
    ```

=== "Go"

    ```go
    type Report struct {
        Rows []Row
    }

    func (r *Report) CalculateTotals() float64 {
        var total float64
        for _, row := range r.Rows {
            total += row.Amount
        }
        return total
    }

    func (r *Report) RenderHTML() string {
        var b strings.Builder
        b.WriteString("<table>")
        for _, row := range r.Rows {
            fmt.Fprintf(&b, "<tr><td>%s</td><td>%.2f</td></tr>", row.Name, row.Amount)
        }
        b.WriteString("</table>")
        return b.String()
    }

    func (r *Report) SaveToDisk(path string) error {
        return os.WriteFile(path, []byte(r.RenderHTML()), 0o644)
    }
    ```

Класс совмещает **бизнес-логику** (`calculate_totals`), **представление** (`render_html`) и **инфраструктуру** (`save_to_disk`). Любое из трёх требований («считать с НДС», «вместо HTML — PDF», «класть в S3 вместо диска») заставит лезть в один и тот же файл, плодить флаги и условные ветки.

### Рефакторинг

=== "Python"

    ```python
    from typing import Protocol


    class Calculator:
        def totals(self, rows: list[dict]) -> float:
            return sum(r["amount"] for r in rows)


    class HtmlRenderer:
        def render(self, rows: list[dict]) -> str:
            html = "<table>"
            for r in rows:
                html += f"<tr><td>{r['name']}</td><td>{r['amount']}</td></tr>"
            return html + "</table>"


    class Storage(Protocol):
        def save(self, name: str, content: str) -> None: ...


    class FileStorage:
        def save(self, name: str, content: str) -> None:
            with open(name, "w") as f:
                f.write(content)
    ```

=== "Go"

    ```go
    type Calculator struct{}

    func (Calculator) Totals(rows []Row) float64 { /* ... */ }

    type HtmlRenderer struct{}

    func (HtmlRenderer) Render(rows []Row) string { /* ... */ }

    type Storage interface {
        Save(name string, content []byte) error
    }

    type FileStorage struct{}

    func (FileStorage) Save(name string, content []byte) error {
        return os.WriteFile(name, content, 0o644)
    }
    ```

Каждый класс отвечает за одну роль. Поменять формат отчёта — поправить `HtmlRenderer`. Положить файл в S3 — добавить `S3Storage`, реализующий тот же интерфейс. Логика подсчёта остаётся в покое.

> **Не путайте SRP с «один метод на класс».** Класс может иметь десяток методов — лишь бы все они служили одной ответственности. Класс `User` с методами `set_email`, `validate_email`, `change_password` — это нормальная ответственность «модель пользователя».

## O — Open/Closed Principle (OCP)

> «Программные сущности должны быть открыты для расширения, но закрыты для изменения.»

Сформулирован Бертраном Мейером в 1988. Идея: добавление новой функциональности не должно требовать переписывания работающего кода. Достигается через **полиморфизм** — клиентский код опирается на абстракцию, а конкретные реализации добавляются «сбоку».

### Антипример

=== "Python"

    ```python
    class PaymentProcessor:
        def pay(self, method: str, amount: float) -> None:
            if method == "card":
                # ... обращение к платёжному шлюзу
                pass
            elif method == "sbp":
                # ... СБП
                pass
            elif method == "wallet":
                # ... криптокошелёк
                pass
            else:
                raise ValueError(f"unknown method: {method}")
    ```

=== "Go"

    ```go
    type PaymentProcessor struct{}

    func (p *PaymentProcessor) Pay(method string, amount float64) error {
        switch method {
        case "card":
            // ...
        case "sbp":
            // ...
        case "wallet":
            // ...
        default:
            return fmt.Errorf("unknown method: %s", method)
        }
        return nil
    }
    ```

Добавление нового способа оплаты — это новая ветка `elif`/`case`. Класс **закрыт от расширения**: каждый раз меняется существующий код, растёт риск задеть работающие методы.

### Рефакторинг

=== "Python"

    ```python
    from typing import Protocol


    class PaymentMethod(Protocol):
        def pay(self, amount: float) -> None: ...


    class CardPayment:
        def pay(self, amount: float) -> None:
            # ... шлюз ...
            pass


    class SbpPayment:
        def pay(self, amount: float) -> None:
            # ... СБП ...
            pass


    class PaymentProcessor:
        def __init__(self, method: PaymentMethod) -> None:
            self.method = method

        def charge(self, amount: float) -> None:
            self.method.pay(amount)
    ```

=== "Go"

    ```go
    type PaymentMethod interface {
        Pay(amount float64) error
    }

    type CardPayment struct{}
    func (CardPayment) Pay(amount float64) error { /* ... */ return nil }

    type SbpPayment struct{}
    func (SbpPayment) Pay(amount float64) error { /* ... */ return nil }

    type PaymentProcessor struct {
        Method PaymentMethod
    }

    func (p *PaymentProcessor) Charge(amount float64) error {
        return p.Method.Pay(amount)
    }
    ```

Новый способ оплаты — новый тип, реализующий интерфейс. `PaymentProcessor` остаётся **закрыт от изменения** и **открыт для расширения**.

> **OCP не означает «никогда не править существующий код».** Если требования изменились существенно — рефакторите. OCP про другое: типовые добавления (новый платёжный метод, новый формат отчёта) должны быть **аддитивными**.

## L — Liskov Substitution Principle (LSP)

> «Если `S` — подтип `T`, то объекты типа `T` могут быть заменены объектами типа `S` без изменения корректности программы.» (Барбара Лисков, 1987)

Наследник должен быть **полноценной заменой** базового типа. Если код, написанный против `Bird`, ломается при подстановке `Penguin` — наследование выбрано неправильно.

### Классический антипример: квадрат-прямоугольник

=== "Python"

    ```python
    class Rectangle:
        def __init__(self, width: int, height: int) -> None:
            self.width = width
            self.height = height

        def set_width(self, w: int) -> None:
            self.width = w

        def set_height(self, h: int) -> None:
            self.height = h

        def area(self) -> int:
            return self.width * self.height


    class Square(Rectangle):
        def set_width(self, w: int) -> None:
            self.width = w
            self.height = w  # ломаем контракт: меняем больше, чем просили

        def set_height(self, h: int) -> None:
            self.width = h
            self.height = h


    def grow(r: Rectangle) -> None:
        r.set_width(10)
        r.set_height(20)
        assert r.area() == 200  # на Square — провал: area == 400
    ```

=== "Go"

    Go не имеет наследования — этот антипример просто не возникает на уровне типов. Аналог через встраивание:

    ```go
    type Rectangle struct {
        Width, Height int
    }

    func (r *Rectangle) SetWidth(w int)  { r.Width = w }
    func (r *Rectangle) SetHeight(h int) { r.Height = h }
    func (r *Rectangle) Area() int       { return r.Width * r.Height }

    type Square struct {
        Rectangle // встраивание не значит «is-a»: это просто переиспользование полей
    }

    // Если переопределим SetWidth — получим ту же проблему, что в Python.
    func (s *Square) SetWidth(w int) {
        s.Width = w
        s.Height = w
    }
    ```

Geometrically `Square is-a Rectangle` — кажется логичным. Но **поведенчески** прямоугольник позволяет независимо менять ширину и высоту, а квадрат нет. Лисков ломается. Решение — **композиция вместо наследования** или другой иерархический корень (`Shape` + `area()`).

### Признаки нарушения LSP

- Наследник выбрасывает исключение там, где родитель работал штатно.
- Наследник «усиливает» предусловия (требует больше, чем обещал родитель).
- Наследник «ослабляет» постусловия (возвращает меньше гарантий).
- В клиентском коде появляются `isinstance` / type switch — «если это Penguin, то не пытайся летать».

> **В Go LSP естественнее.** Интерфейсы — структурный тип; подмены через iif не нужны. Но и в Go LSP можно нарушить — например, реализация `io.Reader`, возвращающая `EOF` слишком рано или паникующая при пустом буфере.

## I — Interface Segregation Principle (ISP)

> «Клиенты не должны зависеть от методов, которые они не используют.»

Большой «толстый» интерфейс заставляет реализаторов знать о методах, которые им не нужны. Это плодит фейковые реализации (`raise NotImplementedError`, `panic("not implemented")`) и связывает несвязанные стороны.

### Антипример

=== "Python"

    ```python
    from typing import Protocol


    class Worker(Protocol):
        def code(self) -> None: ...
        def test(self) -> None: ...
        def deploy(self) -> None: ...
        def manage_team(self) -> None: ...
        def attend_standup(self) -> None: ...


    class Intern:
        def code(self) -> None: pass
        def test(self) -> None: pass
        def deploy(self) -> None:
            raise NotImplementedError("стажёру нельзя в прод")
        def manage_team(self) -> None:
            raise NotImplementedError
        def attend_standup(self) -> None: pass
    ```

=== "Go"

    ```go
    type Worker interface {
        Code()
        Test()
        Deploy()
        ManageTeam()
        AttendStandup()
    }

    type Intern struct{}
    func (Intern) Code()          {}
    func (Intern) Test()          {}
    func (Intern) Deploy()        { panic("стажёру нельзя в прод") }
    func (Intern) ManageTeam()    { panic("not implemented") }
    func (Intern) AttendStandup() {}
    ```

### Рефакторинг

=== "Python"

    ```python
    class Coder(Protocol):
        def code(self) -> None: ...
        def test(self) -> None: ...


    class Deployer(Protocol):
        def deploy(self) -> None: ...


    class Manager(Protocol):
        def manage_team(self) -> None: ...


    class Attendee(Protocol):
        def attend_standup(self) -> None: ...


    class Intern:
        def code(self) -> None: pass
        def test(self) -> None: pass
        def attend_standup(self) -> None: pass
    ```

=== "Go"

    ```go
    type Coder interface {
        Code()
        Test()
    }

    type Deployer interface{ Deploy() }
    type Manager interface{ ManageTeam() }
    type Attendee interface{ AttendStandup() }

    type Intern struct{}
    func (Intern) Code()          {}
    func (Intern) Test()          {}
    func (Intern) AttendStandup() {}
    // Не реализует Deployer и Manager — и это нормально.
    ```

Стандартная библиотека Go — образцовый пример ISP. `io.Reader` и `io.Writer` — по одному методу; составные интерфейсы (`io.ReadWriter`, `io.ReadWriteCloser`) собираются композицией только там, где это нужно.

> **Правило:** интерфейс должен описывать **роль клиента**, а не возможности реализации. «Что нужно функции» важнее, чем «что умеет тип».

## D — Dependency Inversion Principle (DIP)

> «Высокоуровневые модули не должны зависеть от низкоуровневых. И те, и другие должны зависеть от абстракций. Абстракции не должны зависеть от деталей; детали должны зависеть от абстракций.»

Самый «архитектурный» из принципов. Обычно реализуется через **внедрение зависимостей** (Dependency Injection) — конкретные реализации передаются извне, а не создаются внутри класса.

### Антипример

=== "Python"

    ```python
    import sqlite3


    class OrderService:
        def __init__(self) -> None:
            # Жёсткая зависимость от sqlite — нельзя протестировать без БД.
            self.conn = sqlite3.connect("orders.db")

        def create(self, user_id: int, total: float) -> int:
            cur = self.conn.execute(
                "INSERT INTO orders (user_id, total) VALUES (?, ?)",
                (user_id, total),
            )
            self.conn.commit()
            return cur.lastrowid
    ```

=== "Go"

    ```go
    type OrderService struct {
        db *sql.DB
    }

    func NewOrderService() *OrderService {
        db, _ := sql.Open("sqlite3", "orders.db") // зашиваем тип и путь
        return &OrderService{db: db}
    }

    func (s *OrderService) Create(userID int, total float64) (int64, error) {
        res, err := s.db.Exec(
            "INSERT INTO orders (user_id, total) VALUES (?, ?)",
            userID, total,
        )
        if err != nil { return 0, err }
        return res.LastInsertId()
    }
    ```

Бизнес-логика «знает» про SQLite. Замена БД на Postgres — переписывать `OrderService`. Тест без живой БД — невозможен.

### Рефакторинг

=== "Python"

    ```python
    from typing import Protocol


    class OrderRepository(Protocol):
        def save(self, user_id: int, total: float) -> int: ...


    class SqliteOrderRepository:
        def __init__(self, conn) -> None:
            self.conn = conn

        def save(self, user_id: int, total: float) -> int:
            cur = self.conn.execute(
                "INSERT INTO orders (user_id, total) VALUES (?, ?)",
                (user_id, total),
            )
            self.conn.commit()
            return cur.lastrowid


    class OrderService:
        def __init__(self, repo: OrderRepository) -> None:
            self.repo = repo

        def create(self, user_id: int, total: float) -> int:
            return self.repo.save(user_id, total)
    ```

=== "Go"

    ```go
    type OrderRepository interface {
        Save(userID int, total float64) (int64, error)
    }

    type SqliteOrderRepository struct {
        DB *sql.DB
    }

    func (r *SqliteOrderRepository) Save(userID int, total float64) (int64, error) {
        res, err := r.DB.Exec(
            "INSERT INTO orders (user_id, total) VALUES (?, ?)",
            userID, total,
        )
        if err != nil { return 0, err }
        return res.LastInsertId()
    }

    type OrderService struct {
        Repo OrderRepository
    }

    func (s *OrderService) Create(userID int, total float64) (int64, error) {
        return s.Repo.Save(userID, total)
    }
    ```

Теперь `OrderService` зависит от **абстракции** `OrderRepository`. В тестах подсовываем `InMemoryOrderRepository` или мок (см. [тему 12, лекция 2](../../ops/12-code-quality-and-testing/lecture-02-advanced-testing.md)). Прод-конфигурация — `SqliteOrderRepository` или `PostgresOrderRepository` — собирается в `main`/composition root, где известны все детали.

> **DIP и DI — не одно и то же.** DIP — принцип («завись от абстракций»). DI — техника передачи зависимостей (через конструктор, сеттер, контейнер). Можно делать DI без DIP («внедряем конкретный SqliteRepository») — но это лишь полдела.

## SOLID и Go: важные оговорки

Go не задумывался как язык под классическое ООП. Это влияет на применение SOLID:

- **Нет наследования** — LSP применяется к интерфейсам, а не к иерархиям типов. Поведенческие ловушки реже, но и встраивание (`embedding`) бывает обманчивым.
- **Интерфейсы декларируются клиентом, а не реализатором.** «I» в SOLID становится естественной — большие интерфейсы в Go считаются код-смелом.
- **Композиция доминирует над наследованием по умолчанию.** Многие SOLID-проблемы Java/C# просто не возникают.
- **Сильная типизация без generics до 1.18** делала DIP местами громоздким. С generics (Go 1.18+) — стало проще, но интерфейсы остаются основным средством.

Боб Мартин писал SOLID про Smalltalk и Java, но принципы применимы шире — как универсальный язык обсуждения **связности** (cohesion) и **сцепления** (coupling) в любом языке с подтипами.

## Связь SOLID с шаблонами проектирования

Многие шаблоны GoF — это **конкретные техники реализации SOLID**:

| Шаблон | Какой принцип реализует |
|--------|------------------------|
| Strategy | OCP, DIP — поведение задаётся снаружи через интерфейс. |
| Factory Method, Abstract Factory | DIP, OCP — клиент работает с интерфейсами создаваемых продуктов. |
| Adapter | DIP — встраивает существующий API в нужный нам интерфейс. |
| Decorator | OCP — добавляет поведение, не меняя класс-обёртку. |
| Observer | DIP — субъект знает про абстракцию слушателя, не про конкретные классы. |
| Composite | LSP — узлы дерева и листья ведут себя одинаково с точки зрения клиента. |

Когда вы видите «применил `Strategy`», по сути это «удовлетворил OCP в этом конкретном месте».

## Антипринцип: STUPID

Симметрично SOLID есть аббревиатура **STUPID** — характеристики плохого кода:

- **S**ingleton — глобальное состояние, скрытые зависимости.
- **T**ight Coupling — жёсткая связанность.
- **U**ntestability — невозможность написать модульный тест.
- **P**remature Optimization — оптимизация до измерений.
- **I**ndescriptive Naming — `a`, `tmp`, `data2`.
- **D**uplication — копипаста вместо переиспользования.

Каждая из этих проблем — обратная сторона нарушения какого-то принципа SOLID.

## Здравый смысл важнее буквы

SOLID — это **набор эвристик**, а не закон. Бездумное следование приводит к противоположным проблемам:

- **«Над-SRP»** — десятки классов с одной функцией, скрывающие простую логику за фасадом из абстракций.
- **«Над-OCP»** — каждое возможное изменение завёрнуто в интерфейс «на всякий случай». YAGNI (You Aren't Gonna Need It) с этим не согласен.
- **«Над-DIP»** — каждая зависимость абстрагирована, реальные типы прячутся за тремя слоями интерфейсов. Читать невозможно.

Эмпирическое правило: **рефакторите к SOLID, когда чувствуете боль** — что-то трудно тестировать, изменение одного места ломает другое, классы стали слишком большими. Преждевременная абстракция — такой же грех, как преждевременная оптимизация.

> Цитата Кента Бека: «Сначала заставь работать. Потом сделай правильно. Потом сделай быстро.» SOLID — это про «сделай правильно».

## Что почитать дальше

- Robert C. Martin. *Clean Architecture* — главы 7-11 о SOLID.
- Robert C. Martin. *Agile Software Development, Principles, Patterns, and Practices* — исходный источник SOLID.
- Tim Ottinger, Jeff Langr. *Agile in a Flash* (карточки SOLID).
- [Go Code Review Comments](https://go.dev/wiki/CodeReviewComments) — практический SOLID для Go без названия.

## Контрольные вопросы

- В чём отличие SRP от «одна функция на класс»? Приведите пример класса с многими методами, не нарушающего SRP.
- Что такое «причина измениться» в SRP? Сколько таких причин может быть у одной сущности?
- Что значит «открыт для расширения, закрыт для изменения»? Как это реализуется на практике?
- В чём смысл квадрата-прямоугольника как нарушения LSP? Почему «is-a» не равно «может быть подставлен»?
- Почему интерфейсы в Go обычно маленькие? Как это связано с ISP?
- В чём разница между Dependency Inversion Principle и Dependency Injection?
- Почему SOLID не применим буквально? Приведите пример «над-абстракции».
- Какие из шаблонов GoF являются реализациями OCP? DIP?
