// Package lab01 — массив без встроенных функций и стек (LIFO) на его основе.
//
// Go-версия labs/lab01.py: длина массива, максимум по значению и по индексу,
// сумма элементов реализованы вручную (без полагания на len в качестве учебного
// приёма), а Stack — обобщённый стек поверх среза.
package lab01

import (
	"errors"
	"math/rand"
)

// ErrEmpty возвращается операциями, которым нужен непустой массив или стек.
var ErrEmpty = errors.New("структура пуста")

// ArrayLength считает длину среза вручную, не используя len (учебное задание).
func ArrayLength[T any](arr []T) int {
	count := 0
	for range arr {
		count++
	}
	return count
}

// GenerateArray возвращает срез из size случайных чисел в диапазоне [1, 100].
func GenerateArray(size int) []int {
	result := make([]int, 0, size)
	for i := 0; i < size; i++ {
		result = append(result, rand.Intn(100)+1)
	}
	return result
}

// Max возвращает максимальное значение массива. Для пустого — ErrEmpty.
func Max(arr []int) (int, error) {
	if ArrayLength(arr) == 0 {
		return 0, ErrEmpty
	}
	m := arr[0]
	for _, x := range arr[1:] {
		if x > m {
			m = x
		}
	}
	return m, nil
}

// MaxIndex возвращает индекс максимального элемента. Для пустого — ErrEmpty.
func MaxIndex(arr []int) (int, error) {
	if ArrayLength(arr) == 0 {
		return 0, ErrEmpty
	}
	m := arr[0]
	idx := 0
	for x := 1; x < ArrayLength(arr); x++ {
		if arr[x] > m {
			m = arr[x]
			idx = x
		}
	}
	return idx, nil
}

// Sum возвращает сумму элементов массива.
func Sum(arr []int) int {
	total := 0
	for _, x := range arr {
		total += x
	}
	return total
}

// Stack — обобщённый стек (LIFO) на основе среза.
type Stack[T any] struct {
	data []T
}

// IsEmpty сообщает, пуст ли стек.
func (s *Stack[T]) IsEmpty() bool {
	return ArrayLength(s.data) == 0
}

// Push кладёт значение на вершину.
func (s *Stack[T]) Push(value T) {
	s.data = append(s.data, value)
}

// Pop снимает и возвращает вершину. Для пустого стека — ErrEmpty.
func (s *Stack[T]) Pop() (T, error) {
	var zero T
	if s.IsEmpty() {
		return zero, ErrEmpty
	}
	last := ArrayLength(s.data) - 1
	value := s.data[last]
	s.data = s.data[:last]
	return value, nil
}

// Peek возвращает вершину, не снимая её. Для пустого стека — ErrEmpty.
func (s *Stack[T]) Peek() (T, error) {
	var zero T
	if s.IsEmpty() {
		return zero, ErrEmpty
	}
	return s.data[ArrayLength(s.data)-1], nil
}

// Values возвращает элементы стека от вершины к началу (как печатает print_stack).
func (s *Stack[T]) Values() []T {
	result := make([]T, 0, ArrayLength(s.data))
	for i := ArrayLength(s.data) - 1; i >= 0; i-- {
		result = append(result, s.data[i])
	}
	return result
}
