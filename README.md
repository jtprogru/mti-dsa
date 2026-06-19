# dsa-for-ops

[![tests](https://github.com/jtprogru/dsa-for-ops/actions/workflows/tests.yml/badge.svg)](https://github.com/jtprogru/dsa-for-ops/actions/workflows/tests.yml)
[![go](https://github.com/jtprogru/dsa-for-ops/actions/workflows/go.yml/badge.svg)](https://github.com/jtprogru/dsa-for-ops/actions/workflows/go.yml)
[![docs](https://github.com/jtprogru/dsa-for-ops/actions/workflows/docs.yml/badge.svg)](https://github.com/jtprogru/dsa-for-ops/actions/workflows/docs.yml)
[![Сайт курса](https://img.shields.io/badge/site-jtprogru.github.io%2Fdsa--for--ops-2ea44f?logo=github)](https://jtprogru.github.io/dsa-for-ops/)
[![MkDocs Material](https://img.shields.io/badge/MkDocs-Material-526CFE?logo=materialformkdocs)](https://squidfunk.github.io/mkdocs-material/)
[![Python 3.14](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Go 1.23](https://img.shields.io/badge/Go-1.23-00ADD8?logo=go&logoColor=white)](https://go.dev/)

База для будущих **SRE / DevOps / Ops**, которые хотят вырасти из bash-скриптов в инженеров-программистов. Репозиторий объединяет три направления: структуры данных и алгоритмы «с нуля» (Python и Go), теоретический курс «Основы алгоритмизации и программирования» и полноценный трек Go.

📖 Документация опубликована на GitHub Pages: **<https://jtprogru.github.io/dsa-for-ops/>**

## Что внутри

- **DSA** — лабораторные на Python (`lab01`–`lab05`) и их зеркальные реализации на Go, плюс прикладные расширения под эксплуатацию (`lab00`, `lab06`–`lab11`): графы, куча, LRU-кэш, rate limiting, разбор логов, consistent hashing.
- **Основы программирования** — теоретический курс (темы 01–09): алгоритмизация, Python, процедуры и файлы, ООП, IDE, этапы разработки, иерархия классов.
- **Эксплуатация** — темы 10–12: стандартные модули (HTTP, regex, SQLite, конкурентность), разработка приложений (логирование, Django, standalone), качество кода и тестирование.
- **Go** — темы 13–14 и самостоятельные модули в `src/golang/`: основы Go и продвинутый трек (конкурентность, `context`, `net/http`, бенчмарки и pprof).

## Требования

- Python >= 3.14 и [uv](https://docs.astral.sh/uv/) для управления зависимостями.
- Go >= 1.23 для Go-трека и Go-версий лабораторных.

## Установка

```bash
make sync
```

## Запуск лабораторных

```bash
make run                 # список доступных лабораторных
make run lab01           # запустить конкретную лабораторную
make run lab06
```

## Тесты

```bash
make test                # pytest + coverage
make go-test             # go test по всем модулям в src/golang
make go-build            # go build по всем модулям
make go-vet              # go vet по всем модулям
```

## Документация

Сайт собирается из каталога [docs/](docs/) через [MkDocs](https://www.mkdocs.org/) с темой [Material](https://squidfunk.github.io/mkdocs-material/) (mermaid-диаграммы, формулы MathJax, даты ревизий) и автоматически публикуется на GitHub Pages при пуше в `main` (workflow [.github/workflows/docs.yml](.github/workflows/docs.yml)).

```bash
make docs                # локальный сервер на http://127.0.0.1:8000
make docs-build          # собрать статический сайт в site/ (mkdocs build --strict)
```

## Прочие команды

```bash
make help                # список всех команд
make clean               # удалить кэш и временные файлы
```

## Структура

```
labs/                 # DSA-лабы на Python
  common/             # переиспользуемые утилиты (array_length, generate_array, custom_range)
  lab01.py … lab05.py # академические лабы (массив/стек, список/очередь/дерево, сортировки, поиск, hash map)
  lab00.py            # Python для эксплуатации (файлы, argparse, исключения, генераторы)
  lab06.py … lab11.py # прикладные: графы, куча, LRU, rate limiting, разбор логов, consistent hashing
tests/                # pytest к каждой лабораторной
tasks/loops/          # разминочные упражнения на циклы
src/golang/
  basics/             # Go — основы (тема 13)
  advanced/           # Go — продвинутый трек (тема 14)
  dsa/                # Go-версии lab01–lab05 + table-driven тесты
docs/                 # сайт MkDocs (DSA, foundations, ops, go, practice, tickets)
mkdocs.yml            # конфигурация сайта документации
```

## Лабораторные (DSA)

Лабораторные сделаны «с нуля», без сторонних библиотек, чтобы было видно внутреннее устройство структур:

- **Академические (`lab01`–`lab05`)** — массив и стек, связный список / очередь / дерево, сортировки, поиск, hash map.
- **Прикладные под эксплуатацию (`lab00`, `lab06`–`lab11`)** — Python для эксплуатации, графы и топосортировка, куча и top-K, LRU-кэш, rate limiting, разбор логов, consistent hashing и bloom filter.

Подробный разбор каждой структуры (что это, зачем, сложность операций, блок «где это в проде») — в конспекте: <https://jtprogru.github.io/dsa-for-ops/notes/>. Go-версии `lab01`–`lab05` лежат в [`src/golang/dsa/`](src/golang/dsa) с table-driven тестами; конспекты в [docs/](docs/) приводят примеры на Python и Go во вкладках.

## Развитие

Направление развития курса — для кого он, какой стиль выдерживаем и что ещё хочется углубить — в [docs/roadmap.md](docs/roadmap.md).
