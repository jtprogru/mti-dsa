// Package lab02 — связный список, очередь (FIFO) на нём и бинарное дерево поиска.
//
// Go-версия labs/lab02.py. Печать структур заменена на методы-обходы (Values,
// InOrder), которые удобнее тестировать; логика вставки/удаления/обхода —
// та же, что в Python.
package lab02

import "errors"

// ErrEmpty возвращается операциями очереди, требующими непустую структуру.
var ErrEmpty = errors.New("структура пуста")

// Node — узел односвязного списка и очереди.
type Node struct {
	Value int
	Next  *Node
}

// LinkedList — односвязный список с добавлением в хвост.
type LinkedList struct {
	Head *Node
}

// Add добавляет значение в конец списка.
func (l *LinkedList) Add(value int) {
	node := &Node{Value: value}
	if l.Head == nil {
		l.Head = node
		return
	}
	current := l.Head
	for current.Next != nil {
		current = current.Next
	}
	current.Next = node
}

// Remove удаляет первый узел с заданным значением (если он есть).
func (l *LinkedList) Remove(value int) {
	if l.Head == nil {
		return
	}
	if l.Head.Value == value {
		l.Head = l.Head.Next
		return
	}
	current := l.Head
	for current.Next != nil {
		if current.Next.Value == value {
			current.Next = current.Next.Next
			return
		}
		current = current.Next
	}
}

// Values возвращает значения списка от головы к хвосту.
func (l *LinkedList) Values() []int {
	result := []int{}
	for current := l.Head; current != nil; current = current.Next {
		result = append(result, current.Value)
	}
	return result
}

// Queue — очередь (FIFO) на основе связного списка с указателями на оба конца.
type Queue struct {
	head *Node // front — откуда извлекаем
	tail *Node // back  — куда добавляем
}

// IsEmpty сообщает, пуста ли очередь.
func (q *Queue) IsEmpty() bool {
	return q.head == nil
}

// Enqueue добавляет значение в конец очереди.
func (q *Queue) Enqueue(value int) {
	node := &Node{Value: value}
	if q.tail == nil {
		q.head = node
		q.tail = node
		return
	}
	q.tail.Next = node
	q.tail = node
}

// Dequeue извлекает значение из начала очереди. Для пустой — ErrEmpty.
func (q *Queue) Dequeue() (int, error) {
	if q.IsEmpty() {
		return 0, ErrEmpty
	}
	value := q.head.Value
	q.head = q.head.Next
	if q.head == nil {
		q.tail = nil
	}
	return value, nil
}

// Peek возвращает начало очереди, не извлекая его. Для пустой — ErrEmpty.
func (q *Queue) Peek() (int, error) {
	if q.IsEmpty() {
		return 0, ErrEmpty
	}
	return q.head.Value, nil
}

// Values возвращает значения очереди от начала к концу.
func (q *Queue) Values() []int {
	result := []int{}
	for current := q.head; current != nil; current = current.Next {
		result = append(result, current.Value)
	}
	return result
}

// TreeNode — узел бинарного дерева поиска.
type TreeNode struct {
	Value int
	Left  *TreeNode
	Right *TreeNode
}

// BinaryTree — бинарное дерево поиска (BST).
type BinaryTree struct {
	Root *TreeNode
}

// Add вставляет значение: меньшие уходят влево, остальные (>=) — вправо.
func (t *BinaryTree) Add(value int) {
	node := &TreeNode{Value: value}
	if t.Root == nil {
		t.Root = node
		return
	}
	current := t.Root
	for {
		if value < current.Value {
			if current.Left == nil {
				current.Left = node
				return
			}
			current = current.Left
		} else {
			if current.Right == nil {
				current.Right = node
				return
			}
			current = current.Right
		}
	}
}

// InOrder возвращает значения при симметричном обходе (для BST — по возрастанию).
func (t *BinaryTree) InOrder() []int {
	result := []int{}
	var walk func(n *TreeNode)
	walk = func(n *TreeNode) {
		if n == nil {
			return
		}
		walk(n.Left)
		result = append(result, n.Value)
		walk(n.Right)
	}
	walk(t.Root)
	return result
}
