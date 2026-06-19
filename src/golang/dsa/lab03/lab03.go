// Package lab03 — сортировки выбором, вставками, пузырьковая и быстрая со
// счётчиком перестановок.
//
// Go-версия labs/lab03.py. Каждая сортировка возвращает новый отсортированный
// срез и число перестановок; входной срез не мутируется. Семантика подсчёта
// перестановок повторяет Python.
package lab03

import "errors"

// ErrEmpty возвращается поиском минимума на пустом срезе.
var ErrEmpty = errors.New("массив пуст")

// clone возвращает копию среза, чтобы не мутировать вход.
func clone(arr []int) []int {
	return append([]int(nil), arr...)
}

// GetMinElement возвращает минимальное значение. Для пустого — ErrEmpty.
func GetMinElement(arr []int) (int, error) {
	if len(arr) == 0 {
		return 0, ErrEmpty
	}
	m := arr[0]
	for x := 1; x < len(arr); x++ {
		if arr[x] < m {
			m = arr[x]
		}
	}
	return m, nil
}

// GetIndexMinElement возвращает индекс минимума, начиная с позиции start.
//
// Параметр start позволяет переиспользовать функцию в сортировке выбором: на
// каждом шаге ищется минимум в ещё не отсортированном хвосте.
func GetIndexMinElement(arr []int, start int) (int, error) {
	if len(arr) == 0 {
		return 0, ErrEmpty
	}
	idx := start
	for x := start + 1; x < len(arr); x++ {
		if arr[x] < arr[idx] {
			idx = x
		}
	}
	return idx, nil
}

// SelectionSort — сортировка выбором. Возвращает (отсортированный срез, число перестановок).
func SelectionSort(arr []int) ([]int, int) {
	result := clone(arr)
	swaps := 0
	n := len(result)
	for i := 0; i < n-1; i++ {
		minIdx := i
		for j := i + 1; j < n; j++ {
			if result[j] < result[minIdx] {
				minIdx = j
			}
		}
		if minIdx != i {
			result[i], result[minIdx] = result[minIdx], result[i]
			swaps++
		}
	}
	return result, swaps
}

// SelectionSortWithMin — сортировка выбором через GetIndexMinElement (задание 3).
func SelectionSortWithMin(arr []int) ([]int, int) {
	result := clone(arr)
	swaps := 0
	n := len(result)
	for i := 0; i < n-1; i++ {
		minIdx, _ := GetIndexMinElement(result, i)
		if minIdx != i {
			result[i], result[minIdx] = result[minIdx], result[i]
			swaps++
		}
	}
	return result, swaps
}

// InsertionSort — сортировка вставками. Перестановка — каждый сдвиг элемента вправо.
func InsertionSort(arr []int) ([]int, int) {
	result := clone(arr)
	swaps := 0
	n := len(result)
	for i := 1; i < n; i++ {
		key := result[i]
		j := i - 1
		for j >= 0 && result[j] > key {
			result[j+1] = result[j]
			swaps++
			j--
		}
		result[j+1] = key
	}
	return result, swaps
}

// BubbleSort — пузырьковая сортировка с ранним выходом, если за проход не было обменов.
func BubbleSort(arr []int) ([]int, int) {
	result := clone(arr)
	swaps := 0
	n := len(result)
	for i := 0; i < n-1; i++ {
		swapped := false
		for j := 0; j < n-i-1; j++ {
			if result[j] > result[j+1] {
				result[j], result[j+1] = result[j+1], result[j]
				swaps++
				swapped = true
			}
		}
		if !swapped {
			break
		}
	}
	return result, swaps
}

// QuickSort — быстрая сортировка (схема Ломуто). Перестановка — обмен внутри разбиения.
func QuickSort(arr []int) ([]int, int) {
	result := clone(arr)

	var partition func(low, high int) (int, int)
	partition = func(low, high int) (int, int) {
		pivot := result[high]
		swaps := 0
		i := low - 1
		for j := low; j < high; j++ {
			if result[j] <= pivot {
				i++
				if i != j {
					result[i], result[j] = result[j], result[i]
					swaps++
				}
			}
		}
		if i+1 != high {
			result[i+1], result[high] = result[high], result[i+1]
			swaps++
		}
		return i + 1, swaps
	}

	var sort func(low, high int) int
	sort = func(low, high int) int {
		if low >= high {
			return 0
		}
		pivotIdx, swaps := partition(low, high)
		swaps += sort(low, pivotIdx-1)
		swaps += sort(pivotIdx+1, high)
		return swaps
	}

	total := sort(0, len(result)-1)
	return result, total
}

// CompareSwaps считает число перестановок для всех алгоритмов на одном массиве.
func CompareSwaps(arr []int) map[string]int {
	_, sel := SelectionSort(arr)
	_, ins := InsertionSort(arr)
	_, bub := BubbleSort(arr)
	_, qck := QuickSort(arr)
	return map[string]int{
		"Сортировка выбором":     sel,
		"Сортировка вставками":   ins,
		"Пузырьковая сортировка": bub,
		"Быстрая сортировка":     qck,
	}
}
