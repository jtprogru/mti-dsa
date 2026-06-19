package main

import (
	"context"
	"encoding/json"
	"net"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestHandleUser(t *testing.T) {
	srv := httptest.NewServer(newServer("").Handler)
	defer srv.Close()

	resp, err := http.Get(srv.URL + "/users/42")
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Fatalf("status = %d, want 200", resp.StatusCode)
	}
	var u User
	if err := json.NewDecoder(resp.Body).Decode(&u); err != nil {
		t.Fatal(err)
	}
	if u.ID != "42" || u.Name != "Пользователь 42" {
		t.Errorf("user = %+v", u)
	}
}

func TestHandleHealth(t *testing.T) {
	rec := httptest.NewRecorder()
	req := httptest.NewRequest("GET", "/health", nil)
	handleHealth(rec, req)
	if got := rec.Body.String(); got != "ok" {
		t.Errorf("health = %q, want ok", got)
	}
}

func TestRunGracefulShutdown(t *testing.T) {
	srv := newServer("127.0.0.1:0")
	ctx, cancel := context.WithCancel(context.Background())

	done := make(chan error, 1)
	go func() { done <- run(ctx, srv) }()

	time.Sleep(50 * time.Millisecond) // даём серверу подняться
	cancel()

	select {
	case err := <-done:
		if err != nil {
			t.Errorf("run вернул ошибку: %v", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("run не завершился после отмены контекста")
	}
}

func TestRunListenError(t *testing.T) {
	// Занимаем порт, затем поднимаем сервер на том же адресе — ListenAndServe
	// сразу вернёт ошибку «address already in use», которая дойдёт через errCh.
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer ln.Close()

	srv := newServer(ln.Addr().String())
	if err := run(context.Background(), srv); err == nil {
		t.Error("ожидали ошибку run: адрес уже занят")
	}
}
