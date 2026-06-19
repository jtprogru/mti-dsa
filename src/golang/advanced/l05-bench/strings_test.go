package l05bench

import (
	"strings"
	"testing"
)

func TestConcat(t *testing.T) {
	parts := []string{"a", "b", "c"}
	want := "abc"
	if got := ConcatPlus(parts); got != want {
		t.Errorf("ConcatPlus = %q, want %q", got, want)
	}
	if got := ConcatBuilder(parts); got != want {
		t.Errorf("ConcatBuilder = %q, want %q", got, want)
	}
}

func makeParts(n int) []string {
	parts := make([]string, n)
	for i := range parts {
		parts[i] = "x"
	}
	return parts
}

func BenchmarkConcatPlus(b *testing.B) {
	parts := makeParts(1000)
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = ConcatPlus(parts)
	}
}

func BenchmarkConcatBuilder(b *testing.B) {
	parts := makeParts(1000)
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = ConcatBuilder(parts)
	}
}

// для самопроверки: strings.Join — самый быстрый в этом случае
func BenchmarkConcatJoin(b *testing.B) {
	parts := makeParts(1000)
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = strings.Join(parts, "")
	}
}
