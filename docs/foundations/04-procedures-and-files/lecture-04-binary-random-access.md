# Лекция 4. Бинарные файлы и произвольный доступ

В прошлой лекции мы открывали файлы последовательно — от начала к концу. Но реальные задачи часто требуют другого: открыть гигабайтную базу данных и быстро прочитать запись по индексу; прочитать заголовок медиафайла, чтобы понять его параметры; обновить одно поле в середине файла, не переписывая весь.

Для этого нужен **произвольный доступ** (random access) — возможность поставить «указатель чтения» в любую позицию файла. И часто — работать с **бинарным** содержимым по байтам, а не по строкам.

## Произвольный доступ: `seek` и `tell`

Все методы — про работу с файлом, открытым в бинарном режиме (`"rb"`, `"wb"`, `"r+b"`).

### Python

```python
fh.seek(offset, whence=0)
```

- `offset` — смещение в **байтах** (может быть отрицательным);
- `whence` — откуда отсчитывать:
    - `0` — от начала файла (`os.SEEK_SET`, по умолчанию);
    - `1` — от текущей позиции (`os.SEEK_CUR`);
    - `2` — от конца файла (`os.SEEK_END`).

`fh.tell()` возвращает текущую позицию (в байтах).

```python
with open("data.bin", "rb") as fh:
    fh.seek(100)        # переместиться к 100-му байту
    chunk = fh.read(50)  # прочитать 50 байт
    pos = fh.tell()      # 150

    fh.seek(-10, 2)     # 10 байт от конца
    tail = fh.read(10)
```

### Go

В Go тот же API, но через интерфейс `io.Seeker`:

```go
f, _ := os.Open("data.bin")
defer f.Close()

// Переместиться к 100-му байту
_, _ = f.Seek(100, io.SeekStart)
buf := make([]byte, 50)
_, _ = f.Read(buf)

// 10 байт от конца
_, _ = f.Seek(-10, io.SeekEnd)
tail := make([]byte, 10)
_, _ = f.Read(tail)

// Текущая позиция
pos, _ := f.Seek(0, io.SeekCurrent)
```

Константы `io.SeekStart`, `io.SeekCurrent`, `io.SeekEnd` — то же, что `0`, `1`, `2` в Python.

## Бинарные данные: `struct` (Python) и `encoding/binary` (Go)

Бинарный файл — последовательность байтов. Чтобы преобразовать байты в осмысленные числа и строки и обратно, нужно знать **структуру** данных.

### Python: модуль `struct`

`struct` упаковывает значения в байты по описанию формата и распаковывает обратно.

```python
import struct

# Упаковать три числа
data = struct.pack("hhl", 1, 2, 3)
# h — short (2 байта), l — long (4 байта)
print(data)
# b'\x01\x00\x02\x00\x03\x00\x00\x00'

# Распаковать обратно
a, b, c = struct.unpack("hhl", data)
print(a, b, c)  # 1 2 3
```

### Спецификаторы порядка байт

| Префикс | Порядок | Размер | Выравнивание |
|---------|---------|--------|--------------|
| `@` | native | native | native (по умолчанию) |
| `=` | native | стандартный | нет |
| `<` | little-endian | стандартный | нет |
| `>` | big-endian | стандартный | нет |
| `!` | network (big-endian) | стандартный | нет |

> **Главный совет:** для кроссплатформенных файлов всегда указывайте порядок байт явно (`<`, `>` или `!`). Дефолтный `@` зависит от железа и компилятора — на Intel это little-endian, на старых Mac PowerPC было big-endian.

### Спецификаторы типов

| Символ | Тип C | Тип Python | Размер (байт) |
|--------|-------|------------|---------------|
| `c` | `char` | `bytes` длины 1 | 1 |
| `b` / `B` | `int8` / `uint8` | `int` | 1 |
| `?` | `_Bool` | `bool` | 1 |
| `h` / `H` | `int16` / `uint16` | `int` | 2 |
| `i` / `I` | `int32` / `uint32` | `int` | 4 |
| `l` / `L` | `int32` / `uint32` | `int` | 4 |
| `q` / `Q` | `int64` / `uint64` | `int` | 8 |
| `e` | half float | `float` | 2 |
| `f` | float | `float` | 4 |
| `d` | double | `float` | 8 |
| `s` | `char[]` | `bytes` фиксированной длины | переменно |
| `p` | паскалевская строка | `bytes` | переменно |

Перед типом можно поставить число повторений: `"4h"` ≡ `"hhhh"`. Для `s` число означает **длину строки**: `"10s"` — строка ровно 10 байт.

### Пример: упаковать запись и записать в файл

```python
import struct

record = struct.pack("if5s", 24, 12.48, b"12345")
# i — int32, f — float, 5s — 5-байтная строка

with open("data.bin", "wb") as f:
    f.write(record)

# Прочитать обратно
with open("data.bin", "rb") as f:
    data = f.read()

value, value2, value3 = struct.unpack("if5s", data)
print(value, value2, value3)
# 24 12.479999542236328 b'12345'

print(struct.calcsize("if5s"))  # 13
```

> Обратите внимание: `12.48` стало `12.479999542236328`. Это нормально для `float` (32 бита) — точность ограничена. Если важна точность — используйте `d` (`double`, 64 бита) или храните в виде масштабированного целого.

### Итерация по однотипным записям

```python
# Файл содержит N записей по 13 байт
with open("records.bin", "rb") as f:
    data = f.read()

for record in struct.iter_unpack("if5s", data):
    a, b, s = record
    print(a, b, s.decode("ascii"))
```

### Go: пакет `encoding/binary`

```go
import (
    "encoding/binary"
    "os"
)

type Record struct {
    Value    int32
    Value2   float32
    Value3   [5]byte
}

// Запись
f, _ := os.Create("data.bin")
defer f.Close()

r := Record{Value: 24, Value2: 12.48}
copy(r.Value3[:], []byte("12345"))

_ = binary.Write(f, binary.LittleEndian, r)

// Чтение
f2, _ := os.Open("data.bin")
defer f2.Close()

var loaded Record
_ = binary.Read(f2, binary.LittleEndian, &loaded)
fmt.Println(loaded.Value, loaded.Value2, string(loaded.Value3[:]))
```

`binary.LittleEndian` и `binary.BigEndian` — аналоги `<` и `>` в Python `struct`. Для сетевых протоколов используется `binary.BigEndian` (сетевой порядок байт).

## Сравнение Python ↔ Go: бинарные данные

| Аспект | Python (`struct`) | Go (`encoding/binary`) |
|--------|-------------------|------------------------|
| Описание структуры | строка формата `"<if5s"` | тип/структура Go |
| Порядок байт | `<`, `>`, `!`, `=` | `binary.LittleEndian`, `binary.BigEndian` |
| Упаковка | `struct.pack(...)` | `binary.Write(w, order, v)` |
| Распаковка | `struct.unpack(fmt, data)` | `binary.Read(r, order, &v)` |
| Размер записи | `struct.calcsize(fmt)` | `binary.Size(v)` |
| Итерация | `struct.iter_unpack` | цикл с `binary.Read` |

## Практика: чтение заголовка WAV-файла

WAV (Windows PCM) — простой бинарный формат для звука. Файл состоит из двух частей: **заголовок** и **данные сэмплов**.

### Структура заголовка

| Смещение | Размер | Поле | Описание |
|----------|--------|------|----------|
| 0 | 4 | `chunkId` | `"RIFF"` в ASCII |
| 4 | 4 | `chunkSize` | размер файла минус 8 |
| 8 | 4 | `format` | `"WAVE"` |
| 12 | 4 | `subchunk1Id` | `"fmt "` |
| 16 | 4 | `subchunk1Size` | 16 для PCM |
| 20 | 2 | `audioFormat` | 1 = PCM |
| 22 | 2 | `numChannels` | моно = 1, стерео = 2 |
| 24 | 4 | `sampleRate` | частота дискретизации, Гц |
| 28 | 4 | `byteRate` | байт/сек |
| 32 | 2 | `blockAlign` | байт на один сэмпл (по всем каналам) |
| 34 | 2 | `bitsPerSample` | глубина звука |
| 36 | 4 | `subchunk2Id` | `"data"` |
| 40 | 4 | `subchunk2Size` | размер данных в байтах |

### Python

```python
from pathlib import Path
import struct

WAV_HEADER_FORMAT = "<4sI4s4sIHHIIHH4sI"  # 44 байта


def read_wav_header(path: Path) -> dict | None:
    if not path.is_file() or path.stat().st_size < 44:
        return None

    with path.open("rb") as f:
        header = f.read(44)

    fields = struct.unpack(WAV_HEADER_FORMAT, header)
    (
        riff, file_size, wave, fmt, chunk_size,
        audio_format, channels, sample_rate, byte_rate,
        block_align, bps, data, data_size,
    ) = fields

    if riff != b"RIFF" or wave != b"WAVE" or fmt != b"fmt ":
        return None

    return {
        "file_size": file_size + 8,
        "audio_format": "PCM" if audio_format == 1 else "compressed",
        "channels": channels,
        "sample_rate": sample_rate,
        "byte_rate": byte_rate,
        "block_align": block_align,
        "bits_per_sample": bps,
        "data_size": data_size,
    }


info = read_wav_header(Path("pluck-pcm8.wav"))
if info is None:
    print("not a WAV file")
else:
    for key, value in info.items():
        print(f"{key:20} {value}")
```

Вывод примерно такой:

```
file_size            6756
audio_format         PCM
channels             2
sample_rate          11025
byte_rate            22050
block_align          2
bits_per_sample      8
data_size            6712
```

### Go

```go
package main

import (
    "bytes"
    "encoding/binary"
    "fmt"
    "io"
    "os"
)

type WAVHeader struct {
    ChunkID       [4]byte
    ChunkSize     uint32
    Format        [4]byte
    Subchunk1ID   [4]byte
    Subchunk1Size uint32
    AudioFormat   uint16
    NumChannels   uint16
    SampleRate    uint32
    ByteRate      uint32
    BlockAlign    uint16
    BitsPerSample uint16
    Subchunk2ID   [4]byte
    Subchunk2Size uint32
}

func ReadWAVHeader(path string) (*WAVHeader, error) {
    f, err := os.Open(path)
    if err != nil {
        return nil, err
    }
    defer f.Close()

    var h WAVHeader
    if err := binary.Read(f, binary.LittleEndian, &h); err != nil {
        if err == io.EOF || err == io.ErrUnexpectedEOF {
            return nil, fmt.Errorf("файл слишком короткий")
        }
        return nil, err
    }

    if !bytes.Equal(h.ChunkID[:], []byte("RIFF")) ||
        !bytes.Equal(h.Format[:], []byte("WAVE")) {
        return nil, fmt.Errorf("не WAV-файл")
    }

    return &h, nil
}

func main() {
    h, err := ReadWAVHeader("pluck-pcm8.wav")
    if err != nil {
        fmt.Println("error:", err)
        return
    }

    fmt.Printf("channels:        %d\n", h.NumChannels)
    fmt.Printf("sample_rate:     %d Гц\n", h.SampleRate)
    fmt.Printf("byte_rate:       %d байт/сек\n", h.ByteRate)
    fmt.Printf("bits_per_sample: %d\n", h.BitsPerSample)
    fmt.Printf("data_size:       %d байт\n", h.Subchunk2Size)
}
```

### Перейти к сэмплу в середине файла

После чтения заголовка известно:

- `block_align` — сколько байт на один сэмпл (моно 16-бит = 2 байта, стерео 16-бит = 4 байта, стерео 8-бит = 2 байта);
- общее число сэмплов = `data_size / block_align`.

Чтобы прочитать сэмпл с индексом `i`:

```python
samples_count = data_size // block_align
mid_offset = 44 + (samples_count // 2) * block_align

f.seek(mid_offset)
sample = f.read(block_align)
```

В Go аналогично:

```go
samplesCount := int(h.Subchunk2Size) / int(h.BlockAlign)
midOffset := 44 + (samplesCount/2)*int(h.BlockAlign)

_, _ = f.Seek(int64(midOffset), io.SeekStart)
sample := make([]byte, h.BlockAlign)
_, _ = f.Read(sample)
```

## `mmap`: файл как массив байтов

Для огромных файлов (несколько ГБ) есть ещё одна техника: **memory-mapped files**. ОС «отображает» файл в память — обращения к нему выглядят как обычные обращения к массиву байтов, а ОС сама подгружает нужные страницы.

### Python: модуль `mmap`

```python
import mmap

with open("huge.bin", "r+b") as f:
    with mmap.mmap(f.fileno(), 0) as mm:
        # mm можно использовать как bytearray
        print(mm[:10])
        mm[100:104] = b"\xff\xff\xff\xff"  # изменили 4 байта
        idx = mm.find(b"GIF89a")           # поиск
        print(idx)
```

### Go: пакет `golang.org/x/exp/mmap`

В стандартной библиотеке Go готового `mmap` нет, есть низкоуровневые `syscall.Mmap`. Чаще используют `golang.org/x/exp/mmap` или сторонние пакеты.

Когда `mmap` имеет смысл:

- файл очень большой, в память целиком не помещается;
- нужно много раз обращаться в разные места;
- хочется работать с файлом как с массивом (например, для индексов).

Когда **не** имеет смысла:

- маленький файл — `ReadFile` проще и быстрее;
- последовательное чтение — `bufio.Scanner` / `read()` проще.

## Сравнение Python ↔ Go: бинарный random access

| Аспект | Python | Go |
|--------|--------|-----|
| Перемещение в файле | `f.seek(offset, whence)` | `f.Seek(offset, whence)` |
| Текущая позиция | `f.tell()` | `f.Seek(0, io.SeekCurrent)` |
| Упаковка структуры | `struct.pack/unpack` | `binary.Write/Read` |
| Порядок байт | `<`, `>`, `!` в формате | `binary.LittleEndian/BigEndian` |
| Memory-mapped | `mmap` (стандартный) | `golang.org/x/exp/mmap` |

---

## Контрольные вопросы

- Чем отличаются режимы `r` и `rb` при открытии файла, что важнее всего знать про последний?
- Что такое `whence` в `seek` и какие у него значения?
- Зачем явно указывать порядок байт (`<`, `>`) при работе с `struct`? Что произойдёт, если не указать?
- Объясните: чем `i` отличается от `I` в формате `struct.pack`?
- Что такое `block_align` в WAV и зачем он нужен при поиске сэмпла?
- Почему `12.48` после `pack/unpack` через `"f"` стало `12.4799…`, и как это исправить?
- Как в Go прочитать структуру из бинарного файла «одним вызовом»?
- В каких случаях имеет смысл использовать `mmap`?
- Что вернёт `f.read(50)`, если до конца файла осталось меньше 50 байт?
- Что произойдёт, если открыть файл в `"r+b"` и сделать `seek` за конец файла, потом записать?
