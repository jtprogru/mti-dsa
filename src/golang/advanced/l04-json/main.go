// Демо encoding/json: теги, omitempty, кастомный Marshaler.
package main

import (
	"encoding/json"
	"fmt"
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

func main() {
	u := User{
		ID:       1,
		Name:     "Alice",
		JoinDate: Date(time.Date(2026, 3, 15, 0, 0, 0, 0, time.UTC)),
		Internal: "секрет",
	}
	data, _ := json.MarshalIndent(u, "", "  ")
	fmt.Println("Сериализованный JSON:")
	fmt.Println(string(data))

	raw := `{"id":2,"name":"Bob","email":"bob@example.com","join_date":"2026-01-01"}`
	var u2 User
	if err := json.Unmarshal([]byte(raw), &u2); err != nil {
		fmt.Println("ошибка:", err)
		return
	}
	fmt.Printf("Десериализованный: %+v\n", u2)
}
