# Mapeia DAT_18001xxxx (cache de strings do Cython) -> indice -> string nos ranges das funcoes de crypto.
import re, sys

C = r"D:\MSO\Projects\union-clone\decomp\native\_security_crypto.c"
STRF = r"D:\MSO\Projects\union-clone\cython-strings.txt"

strings = []
for ln in open(STRF, encoding="utf-8"):
    m = re.match(r"\s*(\d+)\s+(str|bytes)\s+(.*)$", ln.rstrip("\n"))
    if m:
        rep = m.group(3).split(" hex=")[0]
        strings.append(eval(rep))  # repr python

BASE = 0x168b0  # calibrado: 0x169b0 -> idx 32 'digest', 0x16a08 -> 43 'hashlib'

def idx(addr):
    return (addr - BASE) // 8

def name(addr):
    i = idx(addr)
    if 0 <= i < len(strings):
        s = strings[i]
        return f"{s!r}[{i}]"
    return f"?{i}"

lines = open(C, encoding="utf-8", errors="replace").read().splitlines()
marks = []
for n, l in enumerate(lines, 1):
    m = re.match(r"^// ==== (FUN_\w+) @", l)
    if m:
        marks.append((n, m.group(1)))

def func_range(target):
    prev = None
    for n, nm in marks:
        if n > target:
            return prev, n
        prev = (n, nm)
    return prev, len(lines)

# ranges conhecidos
ranges = {
    "_machine_key": (297, 721),
    "_pyc_derive_key": (2797, 3011),
    "encrypt_pyc": (2930, 3011),
    "encrypt_core": (3017, 3966),
    "decrypt_pyc": (3966, 4056),
    "decrypt_core": (4056, 5056),
}

for label, (a, b) in ranges.items():
    print(f"\n===== {label} (linhas {a}-{b}) =====")
    seen = []
    for i in range(a - 1, min(b, len(lines))):
        l = lines[i]
        for m in re.finditer(r"DAT_(180[0-9a-f]{6})", l):
            addr = int(m.group(1), 16) - 0x180000000
            if 0x16800 <= addr <= 0x16c00:
                entry = (i + 1, name(addr), l.strip()[:90])
                seen.append(entry)
    # agrupa linhas consecutivas
    last = -10
    for ln, nm, src in seen:
        if ln - last <= 1:
            continue
        print(f"  {ln:5}: {nm}")
        last = ln
