# Лекция 3. Web-обёртка как UI: pywebview, CEF Python, Wails

PyQt — мощный фреймворк, но человека, умеющего рисовать формы в Qt Designer, ещё нужно найти. А **web-разработчиков** — и фронтенд-, и фуллстек — на рынке гораздо больше. К тому же современный web-стек (HTML/CSS/JS, React, Vue, Svelte) даёт несравнимо больше свободы в визуальной части, чем десктопные виджеты.

Отсюда популярный подход: **взять встроенный браузер и сделать его «окном» приложения**. Дизайн интерфейса делается на HTML/CSS/JS, часть логики уходит в JavaScript, а Python (или Go) обслуживает «бэкенд» — работу с файлами, БД, сетью.

Применений масса:

- информационный киоск (контент можно даже подгружать из интернета);
- внутренний инструмент с богатым UI;
- админка / монитор / дашборд;
- кросс-платформенное приложение без Qt.

## Какие решения существуют

| Решение | Язык | Движок | Особенности |
|---------|------|--------|-------------|
| **pywebview** | Python | Системный WebView (WebKit/Edge/GTK) | Самый простой способ для Python. Маленький, без Chromium. |
| **CEF Python** | Python | Chromium Embedded Framework | Полный Chromium, тяжелее, но больше возможностей. Зрелый, но менее активно развивается. |
| **Eel** | Python | Chrome/Edge | Поднимает локальный сервер + браузер. Хорош для прототипов. |
| **Flet** | Python | Flutter | Не «браузер в окне», но идея похожа: UI на декларативных компонентах, общих с Web/Mobile. |
| **Wails** | Go | Системный WebView (с Go-бэкендом) | «Electron на Go», но без Node.js. |
| **Electron** | Node.js | Chromium | Стандарт индустрии (VS Code, Slack, Discord). С Python работает плохо. |
| **Tauri** | Rust + любой фронт | Системный WebView | Лёгкая альтернатива Electron. Бэкенд — Rust. |

В Python-мире на 2025 год **`pywebview`** — самый удобный стартовый выбор; **CEF Python** — когда нужен именно Chromium с полной поддержкой современных API. В Go-мире — **Wails**.

Рассмотрим обе экосистемы.

## Python: `pywebview`

`pywebview` — лёгкая обёртка над системным движком:

- macOS — WebKit;
- Windows — WebView2 (Chromium);
- Linux — WebKit2GTK или Qt WebEngine.

Установка:

```bash
uv add pywebview
```

Минимальный пример:

```python
import webview

webview.create_window("Привет", html="<h1>Привет, мир!</h1>")
webview.start()
```

Можно открыть локальный HTML-файл или удалённый URL:

```python
webview.create_window("Документация", "https://docs.python.org/3/")
webview.start()
```

### Вызов Python из JavaScript

```python
import webview


class API:
    def greet(self, name: str) -> str:
        return f"Привет, {name}!"


html = """
<!doctype html>
<html>
<body>
  <input id="name" value="мир">
  <button id="say">Сказать</button>
  <p id="out"></p>
  <script>
    document.getElementById("say").addEventListener("click", async () => {
      const name = document.getElementById("name").value;
      const text = await window.pywebview.api.greet(name);
      document.getElementById("out").innerText = text;
    });
  </script>
</body>
</html>
"""

webview.create_window("Hello", html=html, js_api=API())
webview.start()
```

В JS у вас появляется глобальный объект `window.pywebview.api`, все методы Python-класса доступны асинхронно (Promises).

### Вызов JavaScript из Python

```python
window = webview.create_window("App", html=html)

def on_loaded() -> None:
    window.evaluate_js("document.title = 'Изменили из Python'")

window.events.loaded += on_loaded
webview.start()
```

## Python: CEF Python (Chromium Embedded Framework)

CEF Python встраивает в приложение настоящий Chromium со всеми его возможностями: современный JS, HTML5, CSS3, WebGL, видео/аудио. Цена — приложение «тяжёлое» (десятки мегабайт), и проект развивается медленнее, чем хотелось бы.

```bash
uv add cefpython3
```

Минимальный пример:

```python
import sys
from cefpython3 import cefpython as cef

HTML = """
<!doctype html>
<html>
<head><meta charset="utf-8"></head>
<body>
  <h1>CEF Tutorial</h1>
  <div id="console"></div>
</body>
</html>
"""


def main() -> None:
    sys.excepthook = cef.ExceptHook
    cef.Initialize()
    cef.CreateBrowserSync(url=html_to_data_uri(HTML), window_title="CEF Tutorial")
    cef.MessageLoop()
    cef.Shutdown()


def html_to_data_uri(html: str) -> str:
    import base64
    b64 = base64.b64encode(html.encode("utf-8")).decode("ascii")
    return f"data:text/html;base64,{b64}"


if __name__ == "__main__":
    main()
```

### Структура CEF-приложения

Основные шаги:

1. Установить глобальный обработчик исключений (`sys.excepthook = cef.ExceptHook`) — CEF использует свой контракт для исключений в дочерних процессах.
2. `cef.Initialize(settings=...)` — инициализация (до создания окон).
3. `cef.CreateBrowserSync(url=..., window_title=...)` — создание окна-браузера. URL может быть и обычным `https://...`, и data-URI с HTML-кодом.
4. Зарегистрировать обработчики (`browser.SetClientHandler(...)`) и привязки JS (`browser.SetJavascriptBindings(...)`).
5. `cef.MessageLoop()` — главный цикл сообщений (аналог `mainloop` в Tkinter).
6. `cef.Shutdown()` — финализация (имеет смысл обернуть `try/finally`).

### Привязка Python ↔ JavaScript

```python
class External:
    def __init__(self, browser) -> None:
        self.browser = browser

    def test_callbacks(self, js_callback) -> None:
        # JavaScript передал нам колбэк — можем вызвать его обратно
        js_callback.Call("Строка из Python")


def set_bindings(browser) -> None:
    bindings = cef.JavascriptBindings(bindToFrames=False, bindToPopups=False)
    bindings.SetProperty("python_property", "это свойство задано в Python")
    bindings.SetFunction("html_to_data_uri", html_to_data_uri)
    bindings.SetObject("external", External(browser))
    browser.SetJavascriptBindings(bindings)
```

В браузере:

```js
window.onload = function () {
    console.log(python_property);          // обычное свойство
    external.test_callbacks(function (s) {  // вызов метода + колбэк
        console.log("из Python пришло:", s);
    });
};
```

Со стороны Python можно дёрнуть JS:

- `browser.ExecuteJavascript("alert('hi')")` — выполнить произвольный JS-код;
- `browser.ExecuteFunction("name", arg1, arg2)` — вызвать функцию по имени.

Межпроцессный обмен с рендерером **асинхронный**, поэтому возврат значений из JS обычно делают через колбэки.

### Когда выбрать CEF, а не pywebview

- Нужен именно Chromium (например, ради WebGL, Service Workers, WebRTC).
- Нужны кастомные настройки браузера (DevTools, перехват ресурсов, кастомные схемы URL).
- Нужно одинаковое поведение на всех ОС независимо от системного движка.

В остальных случаях `pywebview` проще, легче и менее проблемен в установке.

## Go: Wails

[Wails](https://wails.io/) — фреймворк для десктопных приложений на Go с фронтендом на HTML/JS. Архитектурно близок к Electron, но **не использует Chromium**: вместо него системный WebView (WebView2 на Windows, WebKit на macOS, WebKitGTK на Linux). Поэтому Wails-приложения весят несколько мегабайт, а не сотни.

```bash
# Установка CLI
go install github.com/wailsapp/wails/v2/cmd/wails@latest

# Создание проекта
wails init -n my-app -t vue   # шаблоны: vanilla, vue, react, svelte, preact, lit
cd my-app
wails dev                     # горячая перезагрузка
wails build                   # сборка артефакта
```

### Архитектура Wails

Структура типичного проекта:

```
my-app/
├── frontend/        # JS/TS-фронтенд (Vite + Vue/React/…)
├── app.go           # Go-структура с экспортируемыми методами
├── main.go          # точка входа
└── wails.json
```

`app.go` — обычная Go-структура, которая «биндится» во фронтенд:

```go
package main

import "context"

type App struct {
    ctx context.Context
}

func NewApp() *App {
    return &App{}
}

func (a *App) startup(ctx context.Context) {
    a.ctx = ctx
}

func (a *App) Greet(name string) string {
    return "Привет, " + name + "!"
}
```

В `main.go` структура регистрируется:

```go
package main

import (
    "embed"

    "github.com/wailsapp/wails/v2"
    "github.com/wailsapp/wails/v2/pkg/options"
    "github.com/wailsapp/wails/v2/pkg/options/assetserver"
)

//go:embed all:frontend/dist
var assets embed.FS

func main() {
    app := NewApp()

    _ = wails.Run(&options.App{
        Title:  "my-app",
        Width:  800,
        Height: 600,
        AssetServer: &assetserver.Options{
            Assets: assets,
        },
        OnStartup: app.startup,
        Bind:      []any{app},
    })
}
```

В JS-фронтенде сгенерированный `wailsjs/go/main/App.js` даёт прямой доступ:

```js
import { Greet } from "../wailsjs/go/main/App";

const text = await Greet("мир");
console.log(text); // "Привет, мир!"
```

### Когда выбрать Wails

- Хочется писать backend на Go с настоящими горутинами/каналами.
- Нужно действительно лёгкое распространение (один бинарник несколько МБ).
- Команда комфортно работает с TypeScript/Vue/React.
- Нужны системные API: файлы, БД, сеть, GPU — всё через Go.

Когда **не лучший** выбор:

- Команда — чистые Python-разработчики (выбирайте `pywebview` или `flet`).
- Нужна максимальная совместимость рендера между ОС (нужен Chromium → берите Electron или CEF).

## Сравнение Python ↔ Go

| Аспект | pywebview / CEF Python | Wails |
|--------|------------------------|-------|
| Backend язык | Python | Go |
| Движок (по умолчанию) | Системный (pywebview) / Chromium (CEF) | Системный |
| Биндинги Python/Go ↔ JS | `js_api`, `pywebview.api`, `JavascriptBindings` | Авто-генерируемый `wailsjs/go/...` |
| Многопоточность бэкенда | `threading`, `asyncio` | Горутины и каналы (нативно) |
| Распространение | Питон + dependencies (PyInstaller / Nuitka) | Один бинарник + ассеты |
| Размер артефакта | Десятки МБ (CEF — больше) | Несколько МБ |
| Hot reload фронта | Зависит от настройки | `wails dev` из коробки |

## Дилемма выбора подхода к UI

Подведём итог всех трёх лекций темы 8. Какой подход к UI выбрать?

| Что важно | Tkinter | PyQt6 / PySide6 | pywebview / Wails |
|-----------|---------|-----------------|-------------------|
| Начать прямо сейчас, без зависимостей | ✅ | ❌ | ❌ |
| Современный внешний вид | ⚠️ (через `ttk`) | ✅ | ✅ |
| Сложные виджеты (таблицы, графики) | ⚠️ | ✅ | ✅ (через JS-библиотеки) |
| Визуальный редактор | ❌ | ✅ (Qt Designer) | ⚠️ (через CSS-фреймворки) |
| Web-разработчики в команде | ❌ | ❌ | ✅ |
| Лёгкое распространение | ✅ | ⚠️ | ⚠️/✅ (Wails) |
| Сообщество и live-проект | ⚠️ | ✅ | ✅ |

Хорошее правило для учебных и небольших задач: **Tkinter → PyQt → web-UI** — двигайтесь вверх по сложности по мере того, как требований к интерфейсу становится больше.

---

## Контрольные вопросы

- В чём разница между «встроенным WebView» и «полным Chromium»?
- Почему `pywebview` весит мало, а CEF Python — много?
- Как Python-объект становится доступен JavaScript-у в `pywebview`? В CEF?
- Что такое межпроцессный обмен в CEF и почему результат возвращается через колбэки?
- Чем Wails концептуально отличается от Electron?
- В каких случаях стоит выбрать PyQt, а в каких — web-UI?
- Где живёт «бизнес-логика» в Wails-приложении и как она «биндится» во фронтенд?
- Можно ли в pywebview / CEF / Wails показать удалённый URL, и какие у этого риски?
