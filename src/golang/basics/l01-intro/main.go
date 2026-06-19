package main

import (
	"fmt"
	"runtime"
)

func main() {
	fmt.Println("Привет, Go!")
	fmt.Printf("Go %s на %s/%s\n", runtime.Version(), runtime.GOOS, runtime.GOARCH)
}
