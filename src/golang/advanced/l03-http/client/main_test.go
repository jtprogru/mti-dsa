package main

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func TestFetch(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("привет"))
	}))
	defer srv.Close()

	status, body, err := fetch(context.Background(), srv.Client(), srv.URL)
	if err != nil {
		t.Fatalf("fetch error: %v", err)
	}
	if status != http.StatusOK {
		t.Errorf("status = %d, want 200", status)
	}
	if body != "привет" {
		t.Errorf("body = %q, want привет", body)
	}
}

func TestFetchError(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Millisecond)
	defer cancel()
	// Порт 0 недоступен для подключения — ожидаем ошибку.
	if _, _, err := fetch(ctx, &http.Client{Timeout: 10 * time.Millisecond}, "http://127.0.0.1:0"); err == nil {
		t.Error("ожидали ошибку для недоступного адреса")
	}
}

func TestFetchRequestError(t *testing.T) {
	// Управляющий символ в URL ломает http.NewRequestWithContext ещё до запроса.
	if _, _, err := fetch(context.Background(), http.DefaultClient, "http://\x7f"); err == nil {
		t.Error("ожидали ошибку построения запроса для битого URL")
	}
}

func TestFetchBodyReadError(t *testing.T) {
	// Перехватываем соединение, обещаем больше байт, чем шлём, и рвём связь —
	// io.ReadAll на клиенте упрётся в неожиданный EOF.
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		hj, ok := w.(http.Hijacker)
		if !ok {
			t.Error("ResponseWriter не поддерживает Hijack")
			return
		}
		conn, _, err := hj.Hijack()
		if err != nil {
			t.Errorf("Hijack: %v", err)
			return
		}
		_, _ = conn.Write([]byte("HTTP/1.1 200 OK\r\nContent-Length: 100\r\n\r\nкороткий хвост"))
		_ = conn.Close()
	}))
	defer srv.Close()

	if _, _, err := fetch(context.Background(), srv.Client(), srv.URL); err == nil {
		t.Error("ожидали ошибку чтения тела (неожиданный EOF)")
	}
}

func TestRun(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_, _ = w.Write([]byte("тело"))
	}))
	defer srv.Close()

	var buf strings.Builder
	if err := run(context.Background(), &buf, srv.Client(), srv.URL); err != nil {
		t.Fatalf("run error: %v", err)
	}
	if out := buf.String(); !strings.Contains(out, "статус: 200") || !strings.Contains(out, "тело") {
		t.Errorf("run вывод = %q", out)
	}

	// Ошибка fetch пробрасывается наружу.
	if err := run(context.Background(), &buf, srv.Client(), "http://\x7f"); err == nil {
		t.Error("ожидали ошибку run для битого URL")
	}
}
