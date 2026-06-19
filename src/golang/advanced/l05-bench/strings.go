// Сравним два способа склейки строк: + и strings.Builder.
package l05bench

import "strings"

func ConcatPlus(parts []string) string {
	var s string
	for _, p := range parts {
		s += p
	}
	return s
}

func ConcatBuilder(parts []string) string {
	var b strings.Builder
	for _, p := range parts {
		b.WriteString(p)
	}
	return b.String()
}
