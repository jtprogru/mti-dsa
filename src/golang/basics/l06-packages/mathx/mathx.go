// Package mathx — учебный пакет для лекции 6.
package mathx

// Sum возвращает сумму двух целых чисел.
func Sum(a, b int) int { return a + b }

// Max возвращает большее из двух значений.
func Max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

// приватная функция — не экспортируется
func sign(n int) int {
	switch {
	case n > 0:
		return 1
	case n < 0:
		return -1
	default:
		return 0
	}
}
