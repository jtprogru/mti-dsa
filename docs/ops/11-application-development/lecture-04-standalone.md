# Лекция 4. Компиляция в standalone

«Standalone» — самостоятельный исполняемый файл, который запускается на машине пользователя без отдельной установки интерпретатора и зависимостей. В Python это особенно ценно: пользователь не должен знать про `python --version`, `pip install` или виртуальные окружения. В Go это вообще «бесплатно» — компилятор по умолчанию выдаёт статический бинарник.

## Зачем

1. **Дистрибуция конечным пользователям.** Desktop-программа на PyQt должна работать на машине без Python и без интернета.
2. **Скрипты для коллег.** Бухгалтер не хочет ставить Python — даёте `.exe`, и он работает.
3. **CLI-утилиты в инфраструктуру.** На сервере не должно быть никаких зависимостей кроме самого бинарника.
4. **Закрытие исходников.** Скомпилированный код труднее читать (но не невозможно — это не настоящая защита).

## Python: PyInstaller

[PyInstaller](https://pyinstaller.org/) — самый популярный инструмент. Анализирует импорты, собирает интерпретатор, библиотеки и ваш код в один бинарник или директорию.

### Установка и базовый запуск

```bash
uv add --dev pyinstaller
uv run pyinstaller app.py
```

Результат:

- `build/` — промежуточные файлы;
- `dist/app/` — готовое приложение (директория с бинарником + библиотеки);
- `app.spec` — конфиг сборки (создаётся при первом запуске).

Запуск собранного:

```bash
./dist/app/app
```

### Один файл

```bash
uv run pyinstaller --onefile app.py
```

Получается один `dist/app` (или `app.exe`). Внутри — упакованный интерпретатор и все библиотеки. При запуске распаковывается во временную директорию (медленнее старт, но удобно для дистрибуции).

### Без консольного окна (GUI на Windows/macOS)

```bash
uv run pyinstaller --onefile --windowed app.py
```

`--windowed` (или `-w`) — не открывать чёрное окно консоли. На macOS дополнительно создаётся `.app`-бандл.

### Иконка и другие ресурсы

```bash
uv run pyinstaller --onefile --windowed --icon=app.ico --add-data "templates:templates" app.py
```

- `--icon=app.ico` — иконка приложения.
- `--add-data "src:dst"` — положить файлы из `src` в `dst` внутри бандла. Разделитель `:` на Unix, `;` на Windows.

В коде доступ к таким файлам — через `sys._MEIPASS` (директория распаковки):

```python
import sys
from pathlib import Path

def resource_path(rel: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return base / rel

icon = resource_path("assets/logo.png")
```

### `.spec`-файл для сложных сборок

При первой сборке создаётся `app.spec` — Python-скрипт, описывающий, что упаковать. Дальше можно собирать через него:

```bash
uv run pyinstaller app.spec
```

В нём настраиваются hidden imports (модули, которые PyInstaller не нашёл сам), исключения, дополнительные бинарники.

### Проблемы PyInstaller

1. **Размер.** Один Python + Tkinter + PIL — это ~30-50 МБ. PyQt — все 80-150 МБ. Сжимать через UPX (`--upx-dir=...`) — иногда помогает, иногда нет.
2. **Антивирусы ругаются.** Heuristic-детекторы Microsoft Defender любят флагать неподписанные `.exe` как «подозрительные». Решение — подписать сертификатом (платно) или использовать Nuitka (см. ниже).
3. **Hidden imports.** Динамические импорты (`importlib.import_module`, плагины) надо перечислять руками через `--hidden-import` или в `.spec`.
4. **Платформа-специфичен.** Собрать `.exe` под Windows можно **только из-под Windows**. Кросс-компиляции нет. Используйте CI с матрицей OS.

## Python: Nuitka

[Nuitka](https://nuitka.net/) — альтернатива PyInstaller с принципиально другим подходом: переводит Python-код в C и компилирует. Результат — быстрее и сложнее ревёрсить, но сборка медленнее.

```bash
uv add --dev nuitka
uv run python -m nuitka --standalone --onefile --enable-plugin=pyqt6 --windows-console-mode=disable app.py
```

Плюсы Nuitka vs PyInstaller:

- быстрее старт и работа (компилированный код вместо байт-кода);
- лучше с антивирусами;
- меньше размер для простых программ.

Минусы:

- долгая сборка (десятки минут на большом проекте);
- нужен C-компилятор (на Windows — MSVC или MinGW);
- иногда падает на экзотических библиотеках.

Если PyInstaller сработал и устраивает — берите его. Nuitka — когда есть конкретная причина (производительность, антивирусы, защита).

## Python: BeeWare Briefcase

[BeeWare](https://beeware.org/) — пакет инструментов для нативных приложений. `briefcase` собирает приложение в формат конкретной платформы:

- Windows: `.msi`-инсталлятор;
- macOS: `.app`-бандл и `.dmg`;
- Linux: `.deb`, `.rpm`, AppImage, Flatpak;
- iOS, Android, web (экспериментально).

```bash
uv add --dev briefcase
uv run briefcase new
uv run briefcase create
uv run briefcase build
uv run briefcase package
```

`briefcase new` — интерактивный мастер: имя приложения, GUI-фреймворк (PyQt, Tk, Toga). Дальше получаете готовый шаблон. Главное преимущество — настоящий инсталлятор для пользователя, а не «вот тебе папка с exe».

Для CLI-утилит избыточно; для GUI — отличный выбор, особенно если нужны мобильные платформы.

## Go: всё проще

```bash
go build -o app
```

Всё. Получили статически слинкованный бинарник. Размер — ~5-15 МБ для нормального приложения, никаких внешних зависимостей.

### Кросс-компиляция

В Go встроена прямо в `go build`:

```bash
# Сборка под Linux на macOS
GOOS=linux GOARCH=amd64 go build -o app-linux

# Под Windows
GOOS=windows GOARCH=amd64 go build -o app.exe

# Под Apple Silicon
GOOS=darwin GOARCH=arm64 go build -o app-mac-arm

# Под Raspberry Pi
GOOS=linux GOARCH=arm64 go build -o app-pi
```

Для большинства комбинаций ничего не нужно ставить — `go` уже включает всё. Ограничения возникают, только если используете `cgo` (FFI к C-библиотекам) — там нужен соответствующий toolchain.

### Уменьшение размера

```bash
go build -ldflags="-s -w" -o app
```

- `-s` — убрать символы;
- `-w` — убрать DWARF-таблицу отладки.

Размер падает на 20–30%. Дальше можно сжать через UPX, но это уже редко нужно.

### Версии в бинарнике

```bash
go build -ldflags="-X main.Version=$(git describe --tags --always)" -o app
```

```go
package main

var Version = "dev"

func main() {
    fmt.Println("version:", Version)
}
```

Так попадает git-тег в скомпилированный бинарник.

### Embed файлов

С Go 1.16 в бинарник можно встраивать ресурсы (шаблоны, статика, миграции):

```go
import "embed"

//go:embed templates/*.html static/*
var assets embed.FS
```

После `go build` всё это лежит внутри бинарника. Никаких «положи рядом папку templates».

Подробнее про embed — в [теме 14, лекция 4](../../go/14-golang-advanced/lecture-04-files-json-db.md).

## Docker — другой способ дистрибуции

Альтернатива standalone-бинарнику — контейнер. Особенно для серверного кода.

### Python-проект

```dockerfile
FROM python:3.14-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

FROM python:3.14-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY . .
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

Multi-stage сборка: первый этап ставит зависимости, второй — финальный образ без `uv` и кэша. Размер — ~120-200 МБ для типового Django-приложения.

### Go-проект

```dockerfile
FROM golang:1.23 AS builder
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -ldflags="-s -w" -o /app

FROM gcr.io/distroless/static-debian12
COPY --from=builder /app /app
ENTRYPOINT ["/app"]
```

Финальный образ — на distroless: только бинарник + минимальные сертификаты CA. Размер: 10-20 МБ. Никакого shell-доступа, никаких уязвимостей в пакетах OS — атаковать почти нечего.

`CGO_ENABLED=0` — выключаем cgo, чтобы получился полностью статичный бинарник (тогда distroless `static` подойдёт).

### Когда что

- **Standalone (PyInstaller/`go build`)** — если конечный пользователь запускает на своей машине двойным кликом.
- **Docker-образ** — если разворачиваете на сервере, в Kubernetes, в CI.

Можно и совмещать: собрать standalone-бинарник, потом завернуть его в минимальный контейнер.

## Подпись и нотаризация

Для distribution на десктопе одного бинарника мало.

- **macOS** требует подписи сертификатом разработчика ($99/год Apple Developer Program) и **нотаризации** через Apple (отправляете .app через `notarytool`, Apple сканирует, возвращает «штамп»). Без этого — Gatekeeper при запуске покажет «приложение от неустановленного разработчика».
- **Windows** не требует подписи строго, но без неё SmartScreen покажет угрожающее предупреждение. EV Code Signing — $200-400/год.
- **Linux** — обычно distribution через `.deb`/`.rpm`-пакеты в репозиторий или AppImage/Flatpak. Подписи через GPG.

Учебные проекты обычно обходятся без подписей; для коммерческого — обязательно.

## CI: автоматизация сборки

GitHub Actions с матрицей OS — стандарт:

```yaml
name: build
on:
  push:
    tags: ["v*"]
jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync
      - run: uv run pyinstaller --onefile app.py
      - uses: actions/upload-artifact@v4
        with:
          name: app-${{ matrix.os }}
          path: dist/*
```

Для Go ещё проще — кросс-компиляция через `GOOS`/`GOARCH` собирает все варианты одной командой на одном runner'е, без матрицы.

Релизы оформляйте через `gh release create` или [`goreleaser`](https://goreleaser.com/) (для Go — умеет собирать матрицу, генерировать changelog, пушить в Docker Hub, GitHub Releases, Homebrew).

## Параллель

| Задача                              | Python                               | Go                                          |
|-------------------------------------|--------------------------------------|----------------------------------------------|
| Локальный «один файл»               | `pyinstaller --onefile`              | `go build`                                   |
| Кросс-сборка                        | Через CI с разными OS                | `GOOS=... GOARCH=... go build`               |
| Уменьшение размера                  | `--upx-dir=...`                      | `-ldflags="-s -w"` + UPX                     |
| Встраивание ресурсов                | `--add-data` или `importlib.resources`| `//go:embed`                                  |
| Native installers (`.msi`, `.app`)  | `briefcase`                          | сторонние тулзы (`fyne package`, NSIS)       |
| Серверный deploy                    | Docker (multi-stage с `uv`)          | Docker (distroless, multi-stage)             |
| Подпись                             | Cert + `signtool`/`codesign`/`notarytool` | то же самое                              |

## Итог

В Python — `pyinstaller` для большинства случаев, `nuitka` если нужна производительность или защита от антивирусов, `briefcase` для нативных инсталляторов. В Go — `go build` плюс `GOOS`/`GOARCH` для кросс-компиляции и `//go:embed` для ресурсов. Для серверного кода обычно проще Docker-образ. Подпись и нотаризация — отдельная история, обязательная для распространения на macOS/Windows.

На этом тема 11 завершена. Дальше — тема 12 (качество кода и тестирование) и Go (темы 13-14), которые вы уже прошли.
