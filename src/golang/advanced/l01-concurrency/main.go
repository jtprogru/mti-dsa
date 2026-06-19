// Демо worker pool: 5 воркеров параллельно возводят числа в квадрат.
package main

import (
	"fmt"
	"sync"
	"time"
)

func worker(id int, jobs <-chan int, results chan<- int, wg *sync.WaitGroup) {
	defer wg.Done()
	for j := range jobs {
		time.Sleep(50 * time.Millisecond) // эмулируем нагрузку
		fmt.Printf("worker %d обработал %d\n", id, j)
		results <- j * j
	}
}

func main() {
	const numWorkers = 5
	const numJobs = 20

	jobs := make(chan int, numJobs)
	results := make(chan int, numJobs)

	var wg sync.WaitGroup
	for w := 1; w <= numWorkers; w++ {
		wg.Add(1)
		go worker(w, jobs, results, &wg)
	}

	for j := 1; j <= numJobs; j++ {
		jobs <- j
	}
	close(jobs)

	// горутина-закрывальщик: ждёт всех воркеров, потом закрывает results
	go func() {
		wg.Wait()
		close(results)
	}()

	total := 0
	for r := range results {
		total += r
	}
	fmt.Println("сумма квадратов:", total)
}
