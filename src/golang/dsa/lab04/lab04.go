// Package lab04 — линейный и бинарный поиск.
//
// Go-версия labs/lab04.py. Бинарный поиск работает по отсортированному срезу;
// BinarySearchSorted сортирует вход сортировкой вставками из пакета lab03 и
// затем ищет — ровно как Python импортирует insertion_sort из lab03.
package lab04

import "github.com/jtprogru/dsa-for-ops/src/golang/dsa/lab03"

// LinearContains сообщает, есть ли target в срезе (простой перебор).
func LinearContains(arr []int, target int) bool {
	for i := 0; i < len(arr); i++ {
		if arr[i] == target {
			return true
		}
	}
	return false
}

// LinearFirstIndex возвращает индекс первого вхождения target или -1.
func LinearFirstIndex(arr []int, target int) int {
	for i := 0; i < len(arr); i++ {
		if arr[i] == target {
			return i
		}
	}
	return -1
}

// LinearAllIndices возвращает индексы всех вхождений target.
//
// Если вхождений нет — пустой срез (в Python здесь -1; в Go идиоматичнее
// проверять длину результата).
func LinearAllIndices(arr []int, target int) []int {
	indices := []int{}
	for i := 0; i < len(arr); i++ {
		if arr[i] == target {
			indices = append(indices, i)
		}
	}
	return indices
}

// LinearCount возвращает количество вхождений target (0, если нет).
func LinearCount(arr []int, target int) int {
	count := 0
	for i := 0; i < len(arr); i++ {
		if arr[i] == target {
			count++
		}
	}
	return count
}

// BinarySearch ищет target в отсортированном срезе. Возвращает индекс или -1.
func BinarySearch(arr []int, target int) int {
	low := 0
	high := len(arr) - 1
	for low <= high {
		mid := (low + high) / 2
		switch {
		case arr[mid] == target:
			return mid
		case arr[mid] < target:
			low = mid + 1
		default:
			high = mid - 1
		}
	}
	return -1
}

// BinarySearchSorted сортирует копию входа вставками и выполняет бинарный поиск.
// Возвращает (индекс в отсортированном срезе или -1, отсортированный срез).
func BinarySearchSorted(arr []int, target int) (int, []int) {
	sorted, _ := lab03.InsertionSort(arr)
	return BinarySearch(sorted, target), sorted
}

// InsertSorted вставляет value в уже отсортированный срез, сохраняя порядок
// (один шаг сортировки вставками). Возвращает новый срез.
func InsertSorted(sortedArr []int, value int) []int {
	result := append([]int(nil), sortedArr...)
	result = append(result, value)
	for j := len(result) - 2; j >= 0 && result[j] > value; j-- {
		result[j+1] = result[j]
		result[j] = value
	}
	return result
}

// BuildSortedSequence строит отсортированную последовательность, добавляя
// элементы по одному (сортировка вставками «на лету»).
func BuildSortedSequence(values []int) []int {
	result := []int{}
	for i := 0; i < len(values); i++ {
		result = InsertSorted(result, values[i])
	}
	return result
}
