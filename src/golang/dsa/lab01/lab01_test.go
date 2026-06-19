package lab01

import (
	"errors"
	"reflect"
	"testing"
)

func TestArrayLength(t *testing.T) {
	tests := []struct {
		name string
		arr  []int
		want int
	}{
		{"пустой", []int{}, 0},
		{"один", []int{42}, 1},
		{"несколько", []int{1, 2, 3, 4, 5}, 5},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := ArrayLength(tt.arr); got != tt.want {
				t.Errorf("ArrayLength(%v) = %d, want %d", tt.arr, got, tt.want)
			}
		})
	}
}

func TestMax(t *testing.T) {
	tests := []struct {
		name    string
		arr     []int
		want    int
		wantErr bool
	}{
		{"максимум в середине", []int{3, 9, 5}, 9, false},
		{"максимум в конце", []int{1, 2, 3}, 3, false},
		{"один элемент", []int{7}, 7, false},
		{"повтор максимума", []int{5, 5, 1}, 5, false},
		{"пустой — ошибка", []int{}, 0, true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := Max(tt.arr)
			if tt.wantErr {
				if !errors.Is(err, ErrEmpty) {
					t.Fatalf("Max(%v) ожидали ErrEmpty, получили %v", tt.arr, err)
				}
				return
			}
			if err != nil {
				t.Fatalf("Max(%v) неожиданная ошибка: %v", tt.arr, err)
			}
			if got != tt.want {
				t.Errorf("Max(%v) = %d, want %d", tt.arr, got, tt.want)
			}
		})
	}
}

func TestMaxIndex(t *testing.T) {
	tests := []struct {
		name    string
		arr     []int
		want    int
		wantErr bool
	}{
		{"первый максимум при повторе", []int{5, 9, 9, 1}, 1, false},
		{"максимум в начале", []int{10, 2, 3}, 0, false},
		{"максимум в конце", []int{1, 2, 30}, 2, false},
		{"пустой — ошибка", []int{}, 0, true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := MaxIndex(tt.arr)
			if tt.wantErr {
				if !errors.Is(err, ErrEmpty) {
					t.Fatalf("MaxIndex(%v) ожидали ErrEmpty, получили %v", tt.arr, err)
				}
				return
			}
			if err != nil {
				t.Fatalf("MaxIndex(%v) неожиданная ошибка: %v", tt.arr, err)
			}
			if got != tt.want {
				t.Errorf("MaxIndex(%v) = %d, want %d", tt.arr, got, tt.want)
			}
		})
	}
}

func TestSum(t *testing.T) {
	tests := []struct {
		name string
		arr  []int
		want int
	}{
		{"пустой", []int{}, 0},
		{"положительные", []int{1, 2, 3, 4}, 10},
		{"с нулём", []int{0, 5, 0}, 5},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := Sum(tt.arr); got != tt.want {
				t.Errorf("Sum(%v) = %d, want %d", tt.arr, got, tt.want)
			}
		})
	}
}

func TestGenerateArray(t *testing.T) {
	arr := GenerateArray(10)
	if len(arr) != 10 {
		t.Fatalf("GenerateArray(10) дал %d элементов", len(arr))
	}
	for _, x := range arr {
		if x < 1 || x > 100 {
			t.Errorf("элемент %d вне диапазона [1, 100]", x)
		}
	}
}

func TestStack(t *testing.T) {
	var s Stack[int]
	if !s.IsEmpty() {
		t.Fatal("новый стек должен быть пустым")
	}
	if _, err := s.Pop(); !errors.Is(err, ErrEmpty) {
		t.Errorf("Pop пустого стека: ожидали ErrEmpty, получили %v", err)
	}
	if _, err := s.Peek(); !errors.Is(err, ErrEmpty) {
		t.Errorf("Peek пустого стека: ожидали ErrEmpty, получили %v", err)
	}

	for _, v := range []int{10, 20, 30} {
		s.Push(v)
	}
	if s.IsEmpty() {
		t.Fatal("после Push стек не должен быть пустым")
	}
	if got, _ := s.Peek(); got != 30 {
		t.Errorf("Peek = %d, want 30", got)
	}
	if got := s.Values(); !reflect.DeepEqual(got, []int{30, 20, 10}) {
		t.Errorf("Values = %v, want [30 20 10]", got)
	}

	got, err := s.Pop()
	if err != nil || got != 30 {
		t.Errorf("Pop = (%d, %v), want (30, nil)", got, err)
	}
	if got, _ := s.Peek(); got != 20 {
		t.Errorf("после Pop Peek = %d, want 20", got)
	}
}
