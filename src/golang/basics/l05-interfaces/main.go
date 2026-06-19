package main

import (
	"fmt"
	"math"
)

type Shape interface {
	Area() float64
	Perimeter() float64
}

type Circle struct{ R float64 }

func (c Circle) Area() float64      { return math.Pi * c.R * c.R }
func (c Circle) Perimeter() float64 { return 2 * math.Pi * c.R }

type Rectangle struct{ W, H float64 }

func (r Rectangle) Area() float64      { return r.W * r.H }
func (r Rectangle) Perimeter() float64 { return 2 * (r.W + r.H) }

func describe(s Shape) {
	fmt.Printf("%T: площадь=%.2f, периметр=%.2f\n", s, s.Area(), s.Perimeter())
}

func anyKind(v any) string {
	switch x := v.(type) {
	case int:
		return fmt.Sprintf("int=%d", x)
	case string:
		return fmt.Sprintf("string=%q", x)
	case []int:
		return fmt.Sprintf("[]int len=%d", len(x))
	case nil:
		return "nil"
	default:
		return fmt.Sprintf("unknown type %T", v)
	}
}

func main() {
	shapes := []Shape{
		Circle{R: 5},
		Rectangle{W: 3, H: 4},
	}
	for _, s := range shapes {
		describe(s)
	}

	for _, v := range []any{42, "привет", []int{1, 2, 3}, nil, 3.14} {
		fmt.Println(anyKind(v))
	}
}
