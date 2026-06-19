package lab03

import (
	"errors"
	"reflect"
	"sort"
	"testing"
)

var sorters = map[string]func([]int) ([]int, int){
	"SelectionSort":        SelectionSort,
	"SelectionSortWithMin": SelectionSortWithMin,
	"InsertionSort":        InsertionSort,
	"BubbleSort":           BubbleSort,
	"QuickSort":            QuickSort,
}

// equalInts сравнивает срезы по содержимому, считая nil и пустой срез равными.
func equalInts(a, b []int) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if a[i] != b[i] {
			return false
		}
	}
	return true
}

func TestSortersProduceSortedOutput(t *testing.T) {
	cases := [][]int{
		{},
		{1},
		{2, 1},
		{5, 2, 4, 1, 3},
		{5, 4, 3, 2, 1},
		{1, 2, 3, 4, 5},
		{3, 3, 1, 2, 3, 1},
		{9, 7, 5, 11, 12, 2, 14, 3, 10, 6},
	}
	for name, fn := range sorters {
		for _, in := range cases {
			input := append([]int(nil), in...)
			got, _ := fn(input)
			want := append([]int(nil), in...)
			sort.Ints(want)
			if !equalInts(got, want) {
				t.Errorf("%s(%v) = %v, want %v", name, in, got, want)
			}
			if !equalInts(input, in) {
				t.Errorf("%s мутировал вход: %v != %v", name, input, in)
			}
		}
	}
}

func TestSwapCountsSortedInput(t *testing.T) {
	in := []int{1, 2, 3, 4, 5}
	for name, fn := range sorters {
		if _, swaps := fn(in); swaps != 0 {
			t.Errorf("%s на отсортированном входе дал %d перестановок, want 0", name, swaps)
		}
	}
}

func TestSwapCountsReversedInput(t *testing.T) {
	in := []int{5, 4, 3, 2, 1}
	tests := []struct {
		name  string
		fn    func([]int) ([]int, int)
		swaps int
	}{
		{"SelectionSort", SelectionSort, 2},
		{"SelectionSortWithMin", SelectionSortWithMin, 2},
		{"InsertionSort", InsertionSort, 10},
		{"BubbleSort", BubbleSort, 10},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if _, swaps := tt.fn(in); swaps != tt.swaps {
				t.Errorf("%s(%v) перестановок = %d, want %d", tt.name, in, swaps, tt.swaps)
			}
		})
	}
}

func TestGetMinElement(t *testing.T) {
	if _, err := GetMinElement([]int{}); !errors.Is(err, ErrEmpty) {
		t.Errorf("GetMinElement([]) ожидали ErrEmpty, получили %v", err)
	}
	tests := []struct {
		arr  []int
		want int
	}{
		{[]int{3, 1, 2}, 1},
		{[]int{5}, 5},
		{[]int{4, 4, 9}, 4},
	}
	for _, tt := range tests {
		got, err := GetMinElement(tt.arr)
		if err != nil || got != tt.want {
			t.Errorf("GetMinElement(%v) = (%d, %v), want (%d, nil)", tt.arr, got, err, tt.want)
		}
	}
}

func TestGetIndexMinElement(t *testing.T) {
	arr := []int{5, 3, 8, 1, 9}
	tests := []struct {
		start int
		want  int
	}{
		{0, 3},
		{1, 3},
		{4, 4},
	}
	for _, tt := range tests {
		got, err := GetIndexMinElement(arr, tt.start)
		if err != nil || got != tt.want {
			t.Errorf("GetIndexMinElement(%v, %d) = (%d, %v), want (%d, nil)", arr, tt.start, got, err, tt.want)
		}
	}
}

func TestCompareSwaps(t *testing.T) {
	got := CompareSwaps([]int{5, 4, 3, 2, 1})
	want := map[string]int{
		"Сортировка выбором":     2,
		"Сортировка вставками":   10,
		"Пузырьковая сортировка": 10,
		"Быстрая сортировка":     got["Быстрая сортировка"], // не фиксируем точное число для quicksort
	}
	if !reflect.DeepEqual(got, want) {
		t.Errorf("CompareSwaps = %v, want %v", got, want)
	}
}
