#!/usr/bin/env bash
# Скаффолд новой лабораторной: создаёт парные файлы
#   src/python/labs/labNN.py  + tests/test_labNN.py  + docs/labNN.md
# Номер NN вычисляется автоматически как «максимальный существующий + 1»
# (приём позаимствован из соседнего проекта interview-task, цель `make newtask`).
#
# Использование:
#   scripts/new-lab.sh            # следующий по порядку номер (labNN)
#   scripts/new-lab.sh lab15      # явный идентификатор лабораторной
set -euo pipefail

cd "$(dirname "$0")/.."

LABS_DIR="src/python/labs"
TESTS_DIR="tests"
DOCS_DIR="docs"

if [ "${1:-}" != "" ]; then
	lab="$1"
	case "$lab" in
		lab[0-9][0-9]) ;;
		*) echo "Ошибка: идентификатор должен иметь вид labNN (например, lab15), получено '$lab'." >&2; exit 1 ;;
	esac
else
	last=$(ls "$LABS_DIR"/lab[0-9][0-9].py 2>/dev/null | sed -E 's#.*/lab([0-9]+)\.py#\1#' | sort -n | tail -1 || true)
	# 10# — форсируем десятичную систему, чтобы 08/09 не трактовались как восьмеричные.
	next=$(( 10#${last:-"-1"} + 1 ))
	lab=$(printf 'lab%02d' "$next")
fi

lab_file="$LABS_DIR/$lab.py"
test_file="$TESTS_DIR/test_$lab.py"
docs_file="$DOCS_DIR/$lab.md"

for f in "$lab_file" "$test_file" "$docs_file"; do
	if [ -e "$f" ]; then
		echo "Ошибка: файл уже существует — $f. Скаффолд отменён." >&2
		exit 1
	fi
done

cat > "$lab_file" <<EOF
"""
Задания:

1. TODO: описать задание лабораторной $lab.
"""


def example(value: int) -> int:
    """Заготовка решения. Замените на реализацию задания."""
    return value


def main() -> None:
    print(example(0))


if __name__ == "__main__":
    main()
EOF

cat > "$test_file" <<EOF
import pytest

from labs.$lab import example, main


@pytest.mark.parametrize(
    "value, expected",
    [
        (0, 0),
        (1, 1),
        (-5, -5),
    ],
)
def test_example(value, expected):
    assert example(value) == expected


def test_main(capsys):
    main()
    assert capsys.readouterr().out.strip() == "0"
EOF

cat > "$docs_file" <<EOF
# $lab — TODO заголовок

TODO: краткое описание лабораторной.

## Содержание

- TODO

---
EOF

echo "Создано:"
echo "  $lab_file"
echo "  $test_file"
echo "  $docs_file"
echo
echo "Дальше:"
echo "  1. Реализуйте задание в $lab_file и тесты в $test_file."
echo "  2. Пропишите страницу $docs_file в nav секции mkdocs.yml."
echo "  3. Прогоните: make fmt && make lint && make py-test"
