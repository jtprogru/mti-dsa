// Демо context: операция с таймаутом и отменой по сигналу.
package main

import (
	"context"
	"fmt"
	"time"
)

// slowWork эмулирует долгую операцию, уважает отмену через ctx.
func slowWork(ctx context.Context, name string, duration time.Duration) error {
	select {
	case <-time.After(duration):
		fmt.Printf("[%s] завершилась за %v\n", name, duration)
		return nil
	case <-ctx.Done():
		fmt.Printf("[%s] отменена: %v\n", name, ctx.Err())
		return ctx.Err()
	}
}

func main() {
	// 1. WithTimeout
	ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
	defer cancel()

	_ = slowWork(ctx, "быстрая", 100*time.Millisecond)
	_ = slowWork(ctx, "медленная", 500*time.Millisecond) // не успеет

	// 2. WithCancel — отменим вручную
	ctx2, cancel2 := context.WithCancel(context.Background())
	go func() {
		time.Sleep(150 * time.Millisecond)
		fmt.Println("отменяем вручную...")
		cancel2()
	}()
	_ = slowWork(ctx2, "длинная", 1*time.Second)
}
