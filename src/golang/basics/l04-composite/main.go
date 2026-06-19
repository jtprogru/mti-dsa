package main

import (
	"fmt"
	"slices"
)

type Animal struct {
	Name string
}

func (a *Animal) Greet() {
	fmt.Println("Привет, я", a.Name)
}

// Dog встраивает Animal через embedding — методы и поля
// доступны напрямую через d.Name / d.Greet().
type Dog struct {
	Animal
	Breed string
}

func main() {
	// Срез: общий с массивом
	nums := []int{10, 20, 30, 40, 50}
	view := nums[1:4]
	view[0] = 999
	fmt.Println("nums после правки view:", nums)

	// slices.Clone для независимой копии
	copy := slices.Clone(nums)
	copy[0] = -1
	fmt.Println("nums после правки copy:", nums)

	// Карта
	counts := map[string]int{"яблоко": 3, "груша": 2}
	counts["слива"] = 5
	if v, ok := counts["вишня"]; !ok {
		fmt.Println("вишни нет (zero value:", v, ")")
	}
	delete(counts, "груша")
	fmt.Println("counts:", counts)

	// Set через map[T]struct{}
	tags := map[string]struct{}{}
	for _, t := range []string{"go", "python", "go", "rust", "python"} {
		tags[t] = struct{}{}
	}
	fmt.Println("уникальных тегов:", len(tags))

	// Embedding
	d := Dog{Animal: Animal{Name: "Рекс"}, Breed: "лабрадор"}
	d.Greet()
	fmt.Println("Порода:", d.Breed, "Имя:", d.Name)
}
