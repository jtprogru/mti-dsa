package main

import (
	"fmt"
	"unicode/utf8"
)

type Weekday int

const (
	Sunday Weekday = iota
	Monday
	Tuesday
	Wednesday
	Thursday
	Friday
	Saturday
)

func (d Weekday) String() string {
	return [...]string{"Вс", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"}[d]
}

func classify(n int) string {
	switch {
	case n < 0:
		return "отрицательное"
	case n == 0:
		return "ноль"
	default:
		return "положительное"
	}
}

func sumTo(n int) (total int) {
	defer fmt.Printf("(sumTo завершилась: total=%d)\n", total)
	for i := 1; i <= n; i++ {
		total += i
	}
	return
}

func main() {
	// Объявления переменных
	var x int = 42
	y := 3.14
	const Pi = 3.14159

	fmt.Println("x:", x, "y:", y, "Pi:", Pi)

	// iota и String()
	fmt.Println("Сегодня:", Friday)

	// switch без тега
	for _, n := range []int{-5, 0, 7} {
		fmt.Printf("%d — %s\n", n, classify(n))
	}

	// defer и named return
	fmt.Println("sumTo(10) =", sumTo(10))

	// Строка vs руны
	s := "Привет"
	fmt.Printf("len(%q) = %d байт, рун = %d\n", s, len(s), utf8.RuneCountInString(s))
}
