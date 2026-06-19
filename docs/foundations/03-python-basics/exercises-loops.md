# Разминочные упражнения: циклы и коллекции

Короткие задачи для отработки базового синтаксиса перед лабораторными и DSA-лабами. Цель — набить руку на `for`/`while`, индексации, накоплении результата и работе со списками и словарями.

Заготовки лежат в репозитории: [`src/python/tasks/loops/`](https://github.com/jtprogru/dsa-for-ops/tree/main/src/python/tasks/loops) (`task1.py`–`task7.py`). В каждом файле — условие в докстринге и пустой шаблон с `TODO`. Решение пишется самостоятельно.

## Задачи

1. **Пара соседних элементов с минимальной суммой** ([`task1.py`](https://github.com/jtprogru/dsa-for-ops/blob/main/src/python/tasks/loops/task1.py)) — дан список из шести случайных чисел; найдите пару соседних элементов с минимальной суммой, выведите их индексы и сумму.
2. **`range` → `list`** ([`task2.py`](https://github.com/jtprogru/dsa-for-ops/blob/main/src/python/tasks/loops/task2.py)) — создайте список с элементами от 0 до 100 с шагом 17 через `list(range(...))`.
3. **Подсчёт отрицательных элементов** ([`task3.py`](https://github.com/jtprogru/dsa-for-ops/blob/main/src/python/tasks/loops/task3.py)) — посчитайте количество отрицательных чисел в списке.
4. **Длины слов** ([`task4.py`](https://github.com/jtprogru/dsa-for-ops/blob/main/src/python/tasks/loops/task4.py)) — соберите пять слов с клавиатуры и сформируйте второй список с их длинами.
5. **Проценты по вкладу** ([`task5.py`](https://github.com/jtprogru/dsa-for-ops/blob/main/src/python/tasks/loops/task5.py)) — рассчитайте сумму вклада с капитализацией процентов по годам в цикле.
6. **Модуль шифрации/дешифрации** ([`task6.py`](https://github.com/jtprogru/dsa-for-ops/blob/main/src/python/tasks/loops/task6.py)) — реализуйте `encrypt`/`decrypt` так, чтобы `decrypt(encrypt(s)) == s`.
7. **Методы словаря `setdefault` и `update`** ([`task7.py`](https://github.com/jtprogru/dsa-for-ops/blob/main/src/python/tasks/loops/task7.py)) — разберитесь и покажите на примерах поведение этих методов.

## Как решать

```bash
git clone https://github.com/jtprogru/dsa-for-ops.git
cd dsa-for-ops/src/python/tasks/loops
python task1.py
```

Открывайте файл, читайте условие в докстринге, заменяйте `TODO` своим кодом. Эти задачи относятся к [Лекции 3. Коллекции](lecture-03-collections.md) и циклам из [Лекции 2](lecture-02-control-flow-io.md).
