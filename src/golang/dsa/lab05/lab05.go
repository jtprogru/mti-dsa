// Package lab05 — хеш-таблицы с разрешением коллизий: метод цепочек и открытая
// адресация (линейное пробирование и двойное хеширование).
//
// Go-версия labs/lab05.py. Ключи и значения — any; поддерживаются ключи типов
// int и string (как в Python). Хеш считается беззнаковым (uint64), поэтому
// индекс h % capacity всегда неотрицателен — в отличие от знакового % в Go.
package lab05

import "fmt"

// HashInt — хеш целого: само число (для отрицательных берём модуль).
func HashInt(key int) uint64 {
	if key >= 0 {
		return uint64(key)
	}
	return uint64(-key)
}

// HashStr — полиномиальный хеш строки по схеме Горнера с базой 31.
// Перебор идёт по рунам (code points), как ord() в Python.
func HashStr(key string) uint64 {
	var h uint64
	for _, ch := range key {
		h = h*31 + uint64(ch)
	}
	return h
}

// HashKey — диспетчер хеширования: int -> HashInt, string -> HashStr.
// Для прочих типов возвращает ошибку (таблица работает только с int/string).
func HashKey(key any) (uint64, error) {
	switch k := key.(type) {
	case int:
		return HashInt(k), nil
	case string:
		return HashStr(k), nil
	default:
		return 0, fmt.Errorf("неподдерживаемый тип ключа: %T, ожидается int или string", key)
	}
}

// mustHash возвращает хеш ключа или паникует на неподдерживаемом типе —
// аналог исключения TypeError в Python (использование чужого типа ключа это
// ошибка программиста, а не штатная ситуация).
func mustHash(key any) uint64 {
	h, err := HashKey(key)
	if err != nil {
		panic(err)
	}
	return h
}

// Pair — пара ключ/значение.
type Pair struct {
	Key   any
	Value any
}

// HashMapChaining — хеш-таблица с разрешением коллизий методом цепочек.
//
// Каждый бакет — срез пар. При коллизии новая пара дописывается в бакет,
// поэтому таблица не «переполняется». Collisions растёт, когда новый ключ
// попадает в уже непустой бакет.
type HashMapChaining struct {
	capacity   int
	size       int
	Collisions int
	maxLoad    float64
	buckets    [][]Pair
}

// NewHashMapChaining создаёт таблицу заданной ёмкости (по умолчанию 8).
func NewHashMapChaining(capacity int) *HashMapChaining {
	if capacity <= 0 {
		capacity = 8
	}
	return &HashMapChaining{
		capacity: capacity,
		maxLoad:  0.75,
		buckets:  make([][]Pair, capacity),
	}
}

func (m *HashMapChaining) index(key any) int {
	return int(mustHash(key) % uint64(m.capacity))
}

// Put вставляет пару или обновляет значение существующего ключа.
func (m *HashMapChaining) Put(key, value any) {
	idx := m.index(key)
	bucket := m.buckets[idx]
	for i := range bucket {
		if bucket[i].Key == key {
			m.buckets[idx][i].Value = value // обновление существующего ключа
			return
		}
	}
	if len(bucket) > 0 {
		m.Collisions++ // ключ лёг в уже занятый бакет — коллизия
	}
	m.buckets[idx] = append(m.buckets[idx], Pair{key, value})
	m.size++
	if m.LoadFactor() > m.maxLoad {
		m.resize(m.capacity * 2)
	}
}

// Get возвращает значение по ключу и признак наличия.
func (m *HashMapChaining) Get(key any) (any, bool) {
	for _, p := range m.buckets[m.index(key)] {
		if p.Key == key {
			return p.Value, true
		}
	}
	return nil, false
}

// Contains сообщает, есть ли ключ в таблице.
func (m *HashMapChaining) Contains(key any) bool {
	_, ok := m.Get(key)
	return ok
}

// Delete удаляет ключ. Возвращает true, если ключ был найден.
func (m *HashMapChaining) Delete(key any) bool {
	idx := m.index(key)
	bucket := m.buckets[idx]
	for i := range bucket {
		if bucket[i].Key == key {
			m.buckets[idx] = append(bucket[:i], bucket[i+1:]...)
			m.size--
			return true
		}
	}
	return false
}

// LoadFactor — коэффициент заполнения: число пар / число бакетов.
func (m *HashMapChaining) LoadFactor() float64 {
	return float64(m.size) / float64(m.capacity)
}

// Capacity возвращает текущую ёмкость таблицы.
func (m *HashMapChaining) Capacity() int { return m.capacity }

// Len возвращает число пар в таблице.
func (m *HashMapChaining) Len() int { return m.size }

func (m *HashMapChaining) resize(newCapacity int) {
	old := m.buckets
	m.capacity = newCapacity
	m.buckets = make([][]Pair, newCapacity)
	m.size = 0
	m.Collisions = 0
	for _, bucket := range old {
		for _, p := range bucket {
			m.Put(p.Key, p.Value)
		}
	}
}

// Keys возвращает все ключи (порядок зависит от раскладки по бакетам).
func (m *HashMapChaining) Keys() []any {
	result := []any{}
	for _, bucket := range m.buckets {
		for _, p := range bucket {
			result = append(result, p.Key)
		}
	}
	return result
}

// Items возвращает все пары (ключ, значение).
func (m *HashMapChaining) Items() []Pair {
	result := []Pair{}
	for _, bucket := range m.buckets {
		result = append(result, bucket...)
	}
	return result
}

// ProbeMode — стратегия пробирования для открытой адресации.
type ProbeMode int

const (
	// ProbeLinear — линейное пробирование, шаг всегда 1.
	ProbeLinear ProbeMode = iota
	// ProbeDouble — двойное хеширование, шаг зависит от ключа.
	ProbeDouble
)

type slotState int

const (
	slotEmpty slotState = iota // никогда не использовался — поиск останавливается
	slotFilled
	slotDeleted // надгробие (tombstone): поиск идёт сквозь, вставка может занять
)

type slot struct {
	state slotState
	key   any
	value any
}

// HashMapOpenAddr — хеш-таблица с открытой адресацией: все пары живут в одном
// массиве слотов. При коллизии элемент ищет другой свободный слот по
// последовательности проб. Collisions растёт на каждый шаг пробы, наткнувшийся
// на слот, занятый ДРУГИМ живым ключом.
//
// Ёмкость держим степенью двойки (8 -> 16 -> ...), тогда нечётный шаг двойного
// хеширования взаимно прост с ёмкостью и проба обходит все слоты.
type HashMapOpenAddr struct {
	capacity   int
	probe      ProbeMode
	size       int
	tombstones int
	Collisions int
	maxLoad    float64
	slots      []slot
}

// NewHashMapOpenAddr создаёт таблицу заданной ёмкости и стратегии пробирования.
func NewHashMapOpenAddr(capacity int, probe ProbeMode) *HashMapOpenAddr {
	if capacity <= 0 {
		capacity = 8
	}
	return &HashMapOpenAddr{
		capacity: capacity,
		probe:    probe,
		maxLoad:  0.5,
		slots:    make([]slot, capacity),
	}
}

func (m *HashMapOpenAddr) index(key any) int {
	return int(mustHash(key) % uint64(m.capacity))
}

func (m *HashMapOpenAddr) hash2(key any) uint64 {
	return mustHash(key)/uint64(m.capacity) + 1
}

// probeStep: linear -> 1; double -> нечётный шаг, зависящий от ключа.
func (m *HashMapOpenAddr) probeStep(key any) int {
	if m.probe == ProbeLinear {
		return 1
	}
	return int(m.hash2(key)%uint64(m.capacity)) | 1
}

// Put вставляет пару или обновляет значение существующего ключа.
func (m *HashMapOpenAddr) Put(key, value any) {
	start := m.index(key)
	step := m.probeStep(key)
	firstTombstone := -1
	i := 0
	idx := start
	for m.slots[idx].state != slotEmpty {
		s := m.slots[idx]
		switch {
		case s.state == slotDeleted:
			if firstTombstone == -1 {
				firstTombstone = idx
			}
		case s.key == key:
			m.slots[idx].value = value // обновление существующего ключа
			return
		default:
			m.Collisions++ // слот занят чужим ключом — коллизия
		}
		i++
		idx = (start + i*step) % m.capacity
	}
	if firstTombstone != -1 {
		m.slots[firstTombstone] = slot{slotFilled, key, value} // переиспользуем надгробие
		m.tombstones--
	} else {
		m.slots[idx] = slot{slotFilled, key, value}
	}
	m.size++
	m.maybeResize()
}

// findSlot возвращает индекс живого слота с ключом или -1.
func (m *HashMapOpenAddr) findSlot(key any) int {
	start := m.index(key)
	step := m.probeStep(key)
	i := 0
	idx := start
	for m.slots[idx].state != slotEmpty {
		s := m.slots[idx]
		if s.state != slotDeleted && s.key == key {
			return idx
		}
		i++
		idx = (start + i*step) % m.capacity
	}
	return -1
}

// Get возвращает значение по ключу и признак наличия.
func (m *HashMapOpenAddr) Get(key any) (any, bool) {
	idx := m.findSlot(key)
	if idx == -1 {
		return nil, false
	}
	return m.slots[idx].value, true
}

// Contains сообщает, есть ли ключ в таблице.
func (m *HashMapOpenAddr) Contains(key any) bool {
	return m.findSlot(key) != -1
}

// Delete удаляет ключ, ставя надгробие. Возвращает true, если ключ был.
//
// Очистить слот в slotEmpty нельзя — это разорвало бы цепочку проб, и Get для
// вставленных «дальше» ключей перестал бы их находить.
func (m *HashMapOpenAddr) Delete(key any) bool {
	idx := m.findSlot(key)
	if idx == -1 {
		return false
	}
	m.slots[idx] = slot{state: slotDeleted}
	m.size--
	m.tombstones++
	return true
}

// LoadFactor — коэффициент заполнения по живым парам: size / capacity.
func (m *HashMapOpenAddr) LoadFactor() float64 {
	return float64(m.size) / float64(m.capacity)
}

// Capacity возвращает текущую ёмкость таблицы.
func (m *HashMapOpenAddr) Capacity() int { return m.capacity }

// Len возвращает число живых пар.
func (m *HashMapOpenAddr) Len() int { return m.size }

// maybeResize расширяет таблицу, если занятых слотов (пары + надгробия) много.
func (m *HashMapOpenAddr) maybeResize() {
	if float64(m.size+m.tombstones)/float64(m.capacity) >= m.maxLoad {
		m.resize(m.capacity * 2)
	}
}

func (m *HashMapOpenAddr) resize(newCapacity int) {
	old := m.slots
	m.capacity = newCapacity
	m.slots = make([]slot, newCapacity)
	m.size = 0
	m.tombstones = 0
	m.Collisions = 0
	for _, s := range old {
		if s.state == slotFilled {
			m.Put(s.key, s.value)
		}
	}
}

// Keys возвращает все живые ключи.
func (m *HashMapOpenAddr) Keys() []any {
	result := []any{}
	for _, s := range m.slots {
		if s.state == slotFilled {
			result = append(result, s.key)
		}
	}
	return result
}

// Items возвращает все живые пары (ключ, значение).
func (m *HashMapOpenAddr) Items() []Pair {
	result := []Pair{}
	for _, s := range m.slots {
		if s.state == slotFilled {
			result = append(result, Pair{s.key, s.value})
		}
	}
	return result
}
