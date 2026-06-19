package lab04

import (
	"reflect"
	"sort"
	"testing"
)

func TestLinearSearch(t *testing.T) {
	arr := []int{4, 8, 15, 8, 16, 23, 8}
	tests := []struct {
		name       string
		target     int
		contains   bool
		firstIndex int
		allIndices []int
		count      int
	}{
		{"несколько вхождений", 8, true, 1, []int{1, 3, 6}, 3},
		{"одно вхождение", 16, true, 4, []int{4}, 1},
		{"нет вхождений", 42, false, -1, []int{}, 0},
		{"первый элемент", 4, true, 0, []int{0}, 1},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := LinearContains(arr, tt.target); got != tt.contains {
				t.Errorf("LinearContains = %v, want %v", got, tt.contains)
			}
			if got := LinearFirstIndex(arr, tt.target); got != tt.firstIndex {
				t.Errorf("LinearFirstIndex = %d, want %d", got, tt.firstIndex)
			}
			if got := LinearAllIndices(arr, tt.target); !reflect.DeepEqual(got, tt.allIndices) {
				t.Errorf("LinearAllIndices = %v, want %v", got, tt.allIndices)
			}
			if got := LinearCount(arr, tt.target); got != tt.count {
				t.Errorf("LinearCount = %d, want %d", got, tt.count)
			}
		})
	}
}

func TestBinarySearch(t *testing.T) {
	arr := []int{1, 3, 5, 7, 9, 11}
	tests := []struct {
		target int
		found  bool
	}{
		{1, true}, {11, true}, {7, true}, {0, false}, {6, false}, {12, false},
	}
	for _, tt := range tests {
		idx := BinarySearch(arr, tt.target)
		if tt.found {
			if idx < 0 || arr[idx] != tt.target {
				t.Errorf("BinarySearch(%d) = %d, ожидали найти", tt.target, idx)
			}
		} else if idx != -1 {
			t.Errorf("BinarySearch(%d) = %d, ожидали -1", tt.target, idx)
		}
	}
}

func TestBinarySearchEmpty(t *testing.T) {
	if idx := BinarySearch([]int{}, 5); idx != -1 {
		t.Errorf("BinarySearch([], 5) = %d, want -1", idx)
	}
}

func TestBinarySearchSorted(t *testing.T) {
	in := []int{5, 2, 9, 1, 7}
	idx, sorted := BinarySearchSorted(in, 9)
	want := []int{1, 2, 5, 7, 9}
	if !reflect.DeepEqual(sorted, want) {
		t.Errorf("отсортированный = %v, want %v", sorted, want)
	}
	if idx < 0 || sorted[idx] != 9 {
		t.Errorf("индекс = %d, ожидали указывающий на 9", idx)
	}
	// Вход не должен мутироваться.
	if !reflect.DeepEqual(in, []int{5, 2, 9, 1, 7}) {
		t.Errorf("вход мутирован: %v", in)
	}
	if missing, _ := BinarySearchSorted(in, 100); missing != -1 {
		t.Errorf("поиск отсутствующего = %d, want -1", missing)
	}
}

func TestInsertSorted(t *testing.T) {
	tests := []struct {
		name   string
		sorted []int
		value  int
		want   []int
	}{
		{"в середину", []int{1, 3, 5}, 4, []int{1, 3, 4, 5}},
		{"в начало", []int{2, 4, 6}, 1, []int{1, 2, 4, 6}},
		{"в конец", []int{2, 4, 6}, 9, []int{2, 4, 6, 9}},
		{"в пустой", []int{}, 7, []int{7}},
		{"дубликат", []int{1, 2, 2, 3}, 2, []int{1, 2, 2, 2, 3}},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := InsertSorted(tt.sorted, tt.value); !reflect.DeepEqual(got, tt.want) {
				t.Errorf("InsertSorted(%v, %d) = %v, want %v", tt.sorted, tt.value, got, tt.want)
			}
		})
	}
}

func TestBuildSortedSequence(t *testing.T) {
	in := []int{5, 1, 4, 2, 8, 2}
	got := BuildSortedSequence(in)
	want := append([]int(nil), in...)
	sort.Ints(want)
	if !reflect.DeepEqual(got, want) {
		t.Errorf("BuildSortedSequence(%v) = %v, want %v", in, got, want)
	}
}
