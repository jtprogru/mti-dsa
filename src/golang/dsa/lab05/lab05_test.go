package lab05

import "testing"

// hashMap — общий интерфейс обеих таблиц для совместных табличных тестов.
type hashMap interface {
	Put(k, v any)
	Get(k any) (any, bool)
	Contains(k any) bool
	Delete(k any) bool
	Len() int
}

func TestHashInt(t *testing.T) {
	tests := []struct {
		key  int
		want uint64
	}{
		{0, 0}, {7, 7}, {100, 100}, {-5, 5},
	}
	for _, tt := range tests {
		if got := HashInt(tt.key); got != tt.want {
			t.Errorf("HashInt(%d) = %d, want %d", tt.key, got, tt.want)
		}
	}
}

func TestHashStr(t *testing.T) {
	// Полиномиальный хеш с базой 31 по схеме Горнера.
	if got := HashStr(""); got != 0 {
		t.Errorf("HashStr(\"\") = %d, want 0", got)
	}
	if got := HashStr("A"); got != 65 { // ord('A') == 65
		t.Errorf("HashStr(\"A\") = %d, want 65", got)
	}
	if got := HashStr("AB"); got != 65*31+66 { // 2081
		t.Errorf("HashStr(\"AB\") = %d, want %d", got, 65*31+66)
	}
	// Детерминированность.
	if HashStr("hello") != HashStr("hello") {
		t.Error("HashStr недетерминирован")
	}
}

func TestHashKey(t *testing.T) {
	if h, err := HashKey(42); err != nil || h != 42 {
		t.Errorf("HashKey(42) = (%d, %v)", h, err)
	}
	if h, err := HashKey("A"); err != nil || h != 65 {
		t.Errorf("HashKey(\"A\") = (%d, %v)", h, err)
	}
	if _, err := HashKey(3.14); err == nil {
		t.Error("HashKey(float) должен вернуть ошибку")
	}
}

// newChaining и newOpenLinear/Double — фабрики для совместных тестов.
func maps() map[string]func() hashMap {
	return map[string]func() hashMap{
		"chaining":    func() hashMap { return NewHashMapChaining(8) },
		"open-linear": func() hashMap { return NewHashMapOpenAddr(8, ProbeLinear) },
		"open-double": func() hashMap { return NewHashMapOpenAddr(8, ProbeDouble) },
	}
}

func TestPutGetContainsDelete(t *testing.T) {
	for name, factory := range maps() {
		t.Run(name, func(t *testing.T) {
			m := factory()
			if _, ok := m.Get("нет"); ok {
				t.Error("Get несуществующего ключа вернул ok=true")
			}
			m.Put(1, "один")
			m.Put("two", 2)
			m.Put(3, 3.0)
			if m.Len() != 3 {
				t.Errorf("Len = %d, want 3", m.Len())
			}
			if v, ok := m.Get(1); !ok || v != "один" {
				t.Errorf("Get(1) = (%v, %v)", v, ok)
			}
			if v, ok := m.Get("two"); !ok || v != 2 {
				t.Errorf("Get(\"two\") = (%v, %v)", v, ok)
			}
			// Обновление значения существующего ключа.
			m.Put(1, "ОДИН")
			if v, _ := m.Get(1); v != "ОДИН" {
				t.Errorf("после обновления Get(1) = %v, want ОДИН", v)
			}
			if m.Len() != 3 {
				t.Errorf("после обновления Len = %d, want 3", m.Len())
			}
			if !m.Contains("two") {
				t.Error("Contains(\"two\") = false")
			}
			if !m.Delete("two") {
				t.Error("Delete(\"two\") = false")
			}
			if m.Contains("two") {
				t.Error("после Delete Contains(\"two\") = true")
			}
			if m.Len() != 2 {
				t.Errorf("после Delete Len = %d, want 2", m.Len())
			}
			if m.Delete("two") {
				t.Error("повторный Delete должен вернуть false")
			}
		})
	}
}

func TestChainingCollisions(t *testing.T) {
	// Ключи 1, 9, 17 при capacity=8 дают один индекс (1 % 8 == 9 % 8 == 17 % 8).
	m := NewHashMapChaining(8)
	for _, k := range []int{1, 9, 17} {
		m.Put(k, k*10)
	}
	if m.Capacity() != 8 {
		t.Errorf("capacity = %d, want 8 (resize не должен сработать)", m.Capacity())
	}
	if m.Collisions != 2 {
		t.Errorf("Collisions = %d, want 2", m.Collisions)
	}
	for _, k := range []int{1, 9, 17} {
		if v, ok := m.Get(k); !ok || v != k*10 {
			t.Errorf("Get(%d) = (%v, %v), want (%d, true)", k, v, ok, k*10)
		}
	}
}

func TestOpenAddrCollisionsRetrievable(t *testing.T) {
	for _, probe := range []ProbeMode{ProbeLinear, ProbeDouble} {
		m := NewHashMapOpenAddr(8, probe)
		for _, k := range []int{1, 9, 17} {
			m.Put(k, k*10)
		}
		for _, k := range []int{1, 9, 17} {
			if v, ok := m.Get(k); !ok || v != k*10 {
				t.Errorf("probe=%d Get(%d) = (%v, %v)", probe, k, v, ok)
			}
		}
	}
}

func TestChainingResize(t *testing.T) {
	m := NewHashMapChaining(8)
	for i := 0; i < 8; i++ {
		m.Put(i, i)
	}
	if m.Capacity() <= 8 {
		t.Errorf("capacity = %d, ожидали рост после превышения load factor", m.Capacity())
	}
	if m.Len() != 8 {
		t.Errorf("Len = %d, want 8", m.Len())
	}
	for i := 0; i < 8; i++ {
		if v, ok := m.Get(i); !ok || v != i {
			t.Errorf("после resize Get(%d) = (%v, %v)", i, v, ok)
		}
	}
}

func TestOpenAddrResize(t *testing.T) {
	m := NewHashMapOpenAddr(8, ProbeLinear)
	for i := 0; i < 4; i++ {
		m.Put(i, i)
	}
	if m.Capacity() <= 8 {
		t.Errorf("capacity = %d, ожидали рост (load factor 0.5)", m.Capacity())
	}
	for i := 0; i < 4; i++ {
		if v, ok := m.Get(i); !ok || v != i {
			t.Errorf("после resize Get(%d) = (%v, %v)", i, v, ok)
		}
	}
}

func TestMustHashPanicsOnBadKey(t *testing.T) {
	defer func() {
		if r := recover(); r == nil {
			t.Error("ожидали панику при неподдерживаемом типе ключа")
		}
	}()
	NewHashMapChaining(8).Put(3.14, "плохой ключ") // float -> mustHash паникует
}

func TestDefaultCapacity(t *testing.T) {
	if c := NewHashMapChaining(0).Capacity(); c != 8 {
		t.Errorf("NewHashMapChaining(0).Capacity() = %d, want 8", c)
	}
	if c := NewHashMapChaining(-1).Capacity(); c != 8 {
		t.Errorf("NewHashMapChaining(-1).Capacity() = %d, want 8", c)
	}
	if c := NewHashMapOpenAddr(0, ProbeLinear).Capacity(); c != 8 {
		t.Errorf("NewHashMapOpenAddr(0).Capacity() = %d, want 8", c)
	}
}

// containsKey проверяет наличие ключа в срезе ключей (порядок не фиксирован).
func containsKey(keys []any, key any) bool {
	for _, k := range keys {
		if k == key {
			return true
		}
	}
	return false
}

func TestKeysAndItems(t *testing.T) {
	for name, factory := range maps() {
		t.Run(name, func(t *testing.T) {
			m := factory()
			want := map[any]any{1: "один", "two": 2, 3: 3.0}
			for k, v := range want {
				m.Put(k, v)
			}

			var keys []any
			var items []Pair
			switch tbl := m.(type) {
			case *HashMapChaining:
				keys, items = tbl.Keys(), tbl.Items()
			case *HashMapOpenAddr:
				keys, items = tbl.Keys(), tbl.Items()
			}

			if len(keys) != len(want) {
				t.Errorf("Keys() = %v, want %d ключей", keys, len(want))
			}
			for k := range want {
				if !containsKey(keys, k) {
					t.Errorf("Keys() не содержит %v", k)
				}
			}
			if len(items) != len(want) {
				t.Errorf("Items() = %v, want %d пар", items, len(want))
			}
			for _, p := range items {
				if want[p.Key] != p.Value {
					t.Errorf("Items() пара %v = %v, want %v", p.Key, p.Value, want[p.Key])
				}
			}
		})
	}
}

func TestOpenAddrLoadFactor(t *testing.T) {
	m := NewHashMapOpenAddr(8, ProbeLinear)
	if lf := m.LoadFactor(); lf != 0 {
		t.Errorf("LoadFactor пустой таблицы = %v, want 0", lf)
	}
	m.Put(1, "a")
	m.Put(2, "b")
	if lf := m.LoadFactor(); lf != 0.25 { // 2 / 8
		t.Errorf("LoadFactor = %v, want 0.25", lf)
	}
}

func TestOpenAddrTombstoneReuse(t *testing.T) {
	m := NewHashMapOpenAddr(8, ProbeLinear)
	m.Put(1, 10) // слот 1
	m.Put(9, 90) // коллизия -> слот 2
	if !m.Delete(1) {
		t.Fatal("Delete(1) = false")
	}
	// Сквозь надгробие на слоте 1 ключ 9 всё ещё находится.
	if v, ok := m.Get(9); !ok || v != 90 {
		t.Errorf("после удаления соседа Get(9) = (%v, %v)", v, ok)
	}
	// Новый ключ той же цепочки переиспользует надгробие.
	m.Put(17, 170)
	if v, ok := m.Get(17); !ok || v != 170 {
		t.Errorf("Get(17) = (%v, %v)", v, ok)
	}
	if m.Contains(1) {
		t.Error("ключ 1 должен оставаться удалённым")
	}
	if m.Capacity() != 8 {
		t.Errorf("capacity = %d, want 8 (resize не ожидался)", m.Capacity())
	}
}
