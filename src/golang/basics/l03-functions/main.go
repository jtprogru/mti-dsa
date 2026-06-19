package main

import (
	"errors"
	"fmt"
)

// ErrDivideByZero — sentinel error.
var ErrDivideByZero = errors.New("деление на ноль")

// divide возвращает результат деления или ErrDivideByZero.
func divide(a, b float64) (float64, error) {
	if b == 0 {
		return 0, ErrDivideByZero
	}
	return a / b, nil
}

// ValidationError — типизированная ошибка.
type ValidationError struct {
	Field   string
	Message string
}

func (e *ValidationError) Error() string {
	return fmt.Sprintf("валидация %s: %s", e.Field, e.Message)
}

func checkAge(age int) error {
	if age < 0 {
		return &ValidationError{Field: "age", Message: "не может быть отрицательным"}
	}
	if age > 150 {
		return &ValidationError{Field: "age", Message: "слишком большой"}
	}
	return nil
}

// counter — замыкание над n.
func counter() func() int {
	n := 0
	return func() int {
		n++
		return n
	}
}

// recoverable демонстрирует panic/recover.
func recoverable() (err error) {
	defer func() {
		if r := recover(); r != nil {
			err = fmt.Errorf("recovered: %v", r)
		}
	}()
	panic("что-то пошло не так")
}

func main() {
	// Простой error
	if q, err := divide(10, 2); err == nil {
		fmt.Println("10/2 =", q)
	}
	if _, err := divide(1, 0); err != nil {
		fmt.Println("ошибка:", err)
		if errors.Is(err, ErrDivideByZero) {
			fmt.Println("(распознали ErrDivideByZero)")
		}
	}

	// Типизированная ошибка через errors.As
	if err := checkAge(-5); err != nil {
		var ve *ValidationError
		if errors.As(err, &ve) {
			fmt.Println("поле:", ve.Field, "—", ve.Message)
		}
	}

	// Замыкание
	next := counter()
	fmt.Println(next(), next(), next())

	// panic + recover
	if err := recoverable(); err != nil {
		fmt.Println("после паники:", err)
	}
}
