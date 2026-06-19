# Превращает объединённый Go coverprofile (stdin) в таблицу в стиле
# `pytest --cov --cov-report=term-missing`: Name / Stmts / Miss / Cover / Missing,
# с подытогом по каждому модулю и общим TOTAL.
#
# Параметр -v prefix=... задаёт префикс импорт-пути, который обрезается в колонке Name.
# Написано на POSIX-подмножестве awk (работает и в BSD awk на macOS, и в gawk в CI).

BEGIN {
    if (prefix == "") prefix = "github.com/jtprogru/dsa-for-ops/src/golang/"
    nf = 0
}

/^mode:/ { next }
NF < 3   { next }

{
    loc = $1
    # Позиционная часть :SL.SC,EL.EC в конце токена пути.
    if (match(loc, /:[0-9]+\.[0-9]+,[0-9]+\.[0-9]+$/) == 0) next
    file = substr(loc, 1, RSTART - 1)
    rng  = substr(loc, RSTART + 1)
    comma = index(rng, ",")
    split(substr(rng, 1, comma - 1), a, ".")
    split(substr(rng, comma + 1), b, ".")
    sl = a[1] + 0
    el = b[1] + 0

    name = file
    if (index(name, prefix) == 1) name = substr(name, length(prefix) + 1)

    nstmt = $2 + 0
    cnt   = $3 + 0

    if (!(name in seen)) {
        seen[name] = 1
        order[++nf] = name
        if (length(name) > maxn) maxn = length(name)
    }
    stmts[name] += nstmt
    if (cnt > 0) {
        covered[name] += nstmt
    } else {
        k = ++mc[name]
        ms[name, k] = sl
        me[name, k] = el
    }
}

END {
    # Сортируем имена файлов лексикографически (insertion sort).
    for (i = 2; i <= nf; i++) {
        v = order[i]; j = i - 1
        while (j >= 1 && order[j] > v) { order[j + 1] = order[j]; j-- }
        order[j + 1] = v
    }

    label = "TOTAL"
    if (length(label) > maxn) maxn = length(label)
    if (maxn < 4) maxn = 4

    # Ширины колонок и форматы строк.
    hfmt = "%-" maxn "s  %6s %6s  %6s  %s"
    rfmt = "%-" maxn "s  %6d %6d  %5d%%  %s"

    print rtrim(sprintf(hfmt, "Name", "Stmts", "Miss", "Cover", "Missing"))
    sep = dashes(maxn + 31)
    print sep

    prevmod = ""
    for (i = 1; i <= nf; i++) {
        name = order[i]
        mod = substr(name, 1, index(name, "/") - 1)
        if (prevmod != "" && mod != prevmod) {
            print_subtotal(prevmod, rfmt, maxn)
            print ""
        }
        prevmod = mod

        miss = stmts[name] - covered[name]
        print rtrim(sprintf(rfmt, name, stmts[name], miss, pct(covered[name], stmts[name]), missing(name)))

        modS[mod] += stmts[name]
        modC[mod] += covered[name]
        totS += stmts[name]
        totC += covered[name]
    }
    if (prevmod != "") print_subtotal(prevmod, rfmt, maxn)

    print sep
    print rtrim(sprintf(rfmt, label, totS, totS - totC, pct(totC, totS), ""))
}

function rtrim(s) {
    sub(/[ \t]+$/, "", s)
    return s
}

# Процент покрытия с округлением (как coverage.py).
function pct(c, s) {
    if (s == 0) return 100
    return int(c * 100.0 / s + 0.5)
}

function dashes(n,    s, i) {
    s = ""
    for (i = 0; i < n; i++) s = s "-"
    return s
}

function print_subtotal(mod, rfmt, maxn,    miss) {
    miss = modS[mod] - modC[mod]
    print rtrim(sprintf(rfmt, ("  " mod), modS[mod], miss, pct(modC[mod], modS[mod]), ""))
}

# Непокрытые строки файла: интервалы блоков, отсортированные и слитые в диапазоны.
function missing(name,    n, i, j, s, e, ts, te, out, lo, hi) {
    n = mc[name]
    if (n == 0) return ""
    # Сортируем интервалы по началу.
    for (i = 1; i <= n; i++) { s[i] = ms[name, i]; e[i] = me[name, i] }
    for (i = 2; i <= n; i++) {
        ts = s[i]; te = e[i]; j = i - 1
        while (j >= 1 && s[j] > ts) { s[j + 1] = s[j]; e[j + 1] = e[j]; j-- }
        s[j + 1] = ts; e[j + 1] = te
    }
    # Сливаем пересекающиеся/смежные интервалы.
    out = ""
    lo = s[1]; hi = e[1]
    for (i = 2; i <= n; i++) {
        if (s[i] <= hi + 1) {
            if (e[i] > hi) hi = e[i]
        } else {
            out = out range(lo, hi) ", "
            lo = s[i]; hi = e[i]
        }
    }
    out = out range(lo, hi)
    return out
}

function range(lo, hi) {
    if (lo == hi) return lo
    return lo "-" hi
}
