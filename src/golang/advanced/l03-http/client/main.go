// HTTP-клиент с явным таймаутом и контекстом.
package main

import (
	"context"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"time"
)

// fetch выполняет GET-запрос и возвращает статус и тело ответа.
func fetch(ctx context.Context, client *http.Client, url string) (int, string, error) {
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return 0, "", err
	}
	resp, err := client.Do(req)
	if err != nil {
		return 0, "", err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return 0, "", err
	}
	return resp.StatusCode, string(body), nil
}

// run выполняет запрос и печатает результат в out. Логику вынесли из main,
// чтобы её можно было покрыть тестами (main остаётся тонкой обёрткой над сетью).
func run(ctx context.Context, out io.Writer, client *http.Client, url string) error {
	status, body, err := fetch(ctx, client, url)
	if err != nil {
		return err
	}
	fmt.Fprintln(out, "статус:", status)
	fmt.Fprintln(out, "тело:  ", body)
	return nil
}

func main() {
	client := &http.Client{Timeout: 5 * time.Second}

	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	if err := run(ctx, os.Stdout, client, "http://localhost:8080/users/42"); err != nil {
		log.Fatal(err)
	}
}
