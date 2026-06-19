// Демо encoding/json: теги, omitempty, кастомный Marshaler.
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"os"
	"time"
)

type Date time.Time

func (d Date) MarshalJSON() ([]byte, error) {
	return []byte(fmt.Sprintf(`"%s"`, time.Time(d).Format("2006-01-02"))), nil
}

func (d *Date) UnmarshalJSON(b []byte) error {
	if len(b) < 2 {
		return fmt.Errorf("пустая дата")
	}
	t, err := time.Parse("2006-01-02", string(b[1:len(b)-1]))
	if err != nil {
		return err
	}
	*d = Date(t)
	return nil
}

type User struct {
	ID       int    `json:"id"`
	Name     string `json:"name"`
	Email    string `json:"email,omitempty"`
	JoinDate Date   `json:"join_date"`
	Internal string `json:"-"`
}

// demo сериализует пример пользователя и разбирает raw обратно, печатая шаги в
// out. Логику вынесли из main, чтобы покрыть тестами обе ветки разбора.
func demo(out io.Writer, raw string) error {
	u := User{
		ID:       1,
		Name:     "Alice",
		JoinDate: Date(time.Date(2026, 3, 15, 0, 0, 0, 0, time.UTC)),
		Internal: "секрет",
	}
	data, _ := json.MarshalIndent(u, "", "  ")
	fmt.Fprintln(out, "Сериализованный JSON:")
	fmt.Fprintln(out, string(data))

	var u2 User
	if err := json.Unmarshal([]byte(raw), &u2); err != nil {
		return err
	}
	fmt.Fprintf(out, "Десериализованный: %+v\n", u2)
	return nil
}

func main() {
	raw := `{"id":2,"name":"Bob","email":"bob@example.com","join_date":"2026-01-01"}`
	if err := demo(os.Stdout, raw); err != nil {
		log.Println("ошибка:", err)
	}
}
