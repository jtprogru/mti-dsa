package mathx

import "testing"

func TestSum(t *testing.T) {
	cases := []struct {
		name    string
		a, b, w int
	}{
		{"positive", 2, 3, 5},
		{"zero", 0, 0, 0},
		{"negative", -1, -1, -2},
		{"mixed", -5, 3, -2},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()
			if got := Sum(tc.a, tc.b); got != tc.w {
				t.Errorf("Sum(%d, %d) = %d, want %d", tc.a, tc.b, got, tc.w)
			}
		})
	}
}

func TestMax(t *testing.T) {
	if got := Max(3, 5); got != 5 {
		t.Errorf("Max(3, 5) = %d, want 5", got)
	}
	if got := Max(7, 2); got != 7 {
		t.Errorf("Max(7, 2) = %d, want 7", got)
	}
}

func TestSign(t *testing.T) {
	// внутренний тест — проверяет приватную функцию
	if sign(5) != 1 || sign(-5) != -1 || sign(0) != 0 {
		t.Error("sign не работает")
	}
}

func BenchmarkSum(b *testing.B) {
	for i := 0; i < b.N; i++ {
		_ = Sum(1, 2)
	}
}
