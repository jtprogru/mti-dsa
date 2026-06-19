package main

import (
	"encoding/json"
	"io"
	"strings"
	"testing"
	"time"
)

func TestDateMarshal(t *testing.T) {
	d := Date(time.Date(2026, 3, 15, 0, 0, 0, 0, time.UTC))
	b, err := json.Marshal(d)
	if err != nil {
		t.Fatal(err)
	}
	if string(b) != `"2026-03-15"` {
		t.Errorf("Marshal = %s, want \"2026-03-15\"", b)
	}
}

func TestDateUnmarshal(t *testing.T) {
	var d Date
	if err := json.Unmarshal([]byte(`"2026-01-01"`), &d); err != nil {
		t.Fatal(err)
	}
	if got := time.Time(d).Format("2006-01-02"); got != "2026-01-01" {
		t.Errorf("Unmarshal got %s, want 2026-01-01", got)
	}
}

func TestDateUnmarshalErrors(t *testing.T) {
	var d Date
	if err := d.UnmarshalJSON([]byte("")); err == nil {
		t.Error("ожидали ошибку для пустого ввода")
	}
	if err := d.UnmarshalJSON([]byte(`"не-дата"`)); err == nil {
		t.Error("ожидали ошибку парсинга даты")
	}
}

func TestUserRoundTrip(t *testing.T) {
	raw := `{"id":2,"name":"Bob","email":"bob@example.com","join_date":"2026-01-01"}`
	var u User
	if err := json.Unmarshal([]byte(raw), &u); err != nil {
		t.Fatal(err)
	}
	if u.ID != 2 || u.Name != "Bob" || u.Email != "bob@example.com" {
		t.Errorf("user = %+v", u)
	}
}

func TestDemo(t *testing.T) {
	var buf strings.Builder
	raw := `{"id":2,"name":"Bob","email":"bob@example.com","join_date":"2026-01-01"}`
	if err := demo(&buf, raw); err != nil {
		t.Fatalf("demo вернул ошибку: %v", err)
	}
	out := buf.String()
	if !strings.Contains(out, "Сериализованный JSON") || !strings.Contains(out, "Bob") {
		t.Errorf("demo вывод = %q", out)
	}

	// Битый JSON пробрасывает ошибку разбора наружу.
	if err := demo(io.Discard, `{не json`); err == nil {
		t.Error("ожидали ошибку разбора битого JSON")
	}
}

// TestSmoke проверяет, что демо запускается без паники.
func TestSmoke(t *testing.T) {
	main()
}
