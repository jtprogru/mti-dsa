package lab02

import (
	"errors"
	"reflect"
	"testing"
)

func TestLinkedList(t *testing.T) {
	tests := []struct {
		name   string
		add    []int
		remove []int
		want   []int
	}{
		{"только добавление", []int{10, 20, 30}, nil, []int{10, 20, 30}},
		{"удаление из середины", []int{10, 20, 30}, []int{20}, []int{10, 30}},
		{"удаление головы", []int{10, 20, 30}, []int{10}, []int{20, 30}},
		{"удаление хвоста", []int{10, 20, 30}, []int{30}, []int{10, 20}},
		{"удаление отсутствующего", []int{10, 20}, []int{99}, []int{10, 20}},
		{"удаление из пустого", nil, []int{1}, []int{}},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var l LinkedList
			for _, v := range tt.add {
				l.Add(v)
			}
			for _, v := range tt.remove {
				l.Remove(v)
			}
			if got := l.Values(); !reflect.DeepEqual(got, tt.want) {
				t.Errorf("Values = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestQueue(t *testing.T) {
	var q Queue
	if !q.IsEmpty() {
		t.Fatal("новая очередь должна быть пустой")
	}
	if _, err := q.Dequeue(); !errors.Is(err, ErrEmpty) {
		t.Errorf("Dequeue пустой: ожидали ErrEmpty, получили %v", err)
	}
	if _, err := q.Peek(); !errors.Is(err, ErrEmpty) {
		t.Errorf("Peek пустой: ожидали ErrEmpty, получили %v", err)
	}

	for _, v := range []int{10, 20, 30, 40} {
		q.Enqueue(v)
	}
	if got := q.Values(); !reflect.DeepEqual(got, []int{10, 20, 30, 40}) {
		t.Errorf("Values = %v, want [10 20 30 40]", got)
	}
	if got, _ := q.Peek(); got != 10 {
		t.Errorf("Peek = %d, want 10", got)
	}
	got, err := q.Dequeue()
	if err != nil || got != 10 {
		t.Errorf("Dequeue = (%d, %v), want (10, nil)", got, err)
	}
	if got, _ := q.Peek(); got != 20 {
		t.Errorf("после Dequeue Peek = %d, want 20", got)
	}
}

func TestQueueDrainResetsTail(t *testing.T) {
	var q Queue
	q.Enqueue(1)
	if _, err := q.Dequeue(); err != nil {
		t.Fatal(err)
	}
	if !q.IsEmpty() {
		t.Fatal("очередь должна стать пустой")
	}
	// После полного опустошения очередь снова пригодна к использованию.
	q.Enqueue(2)
	if got, _ := q.Peek(); got != 2 {
		t.Errorf("Peek = %d, want 2", got)
	}
}

func TestBinaryTreeInOrder(t *testing.T) {
	tests := []struct {
		name string
		add  []int
		want []int
	}{
		{"сбалансированный", []int{50, 30, 70, 20, 40, 60, 80}, []int{20, 30, 40, 50, 60, 70, 80}},
		{"вырожденный по возрастанию", []int{1, 2, 3, 4}, []int{1, 2, 3, 4}},
		{"вырожденный по убыванию", []int{4, 3, 2, 1}, []int{1, 2, 3, 4}},
		{"с дубликатами", []int{5, 3, 5, 3}, []int{3, 3, 5, 5}},
		{"один узел", []int{42}, []int{42}},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var bt BinaryTree
			for _, v := range tt.add {
				bt.Add(v)
			}
			if got := bt.InOrder(); !reflect.DeepEqual(got, tt.want) {
				t.Errorf("InOrder = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestBinaryTreeStructure(t *testing.T) {
	// Дубликаты должны уходить вправо (value >= current -> right).
	var bt BinaryTree
	bt.Add(5)
	bt.Add(5)
	if bt.Root.Left != nil {
		t.Error("дубликат не должен попадать в левое поддерево")
	}
	if bt.Root.Right == nil || bt.Root.Right.Value != 5 {
		t.Error("дубликат должен попадать в правое поддерево")
	}
}
