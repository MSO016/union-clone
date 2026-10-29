# Busca periodo do keystream com tolerancia (plaintexts de builds distintos)
import os, glob, zlib

PYZ = r"D:\MSO\Projects\union-clone\pyz\RESTORECELL.exe_extracted\PYZ.pyz_extracted\app"
DISK = r"D:\MSO\Projects\union-clone\extracted\app\app"

def rel_set(root):
    return {os.path.relpath(p, root).replace("\\", "/"): p
            for p in glob.glob(os.path.join(root, "**", "*.pyc"), recursive=True)}

pz, dk = rel_set(PYZ), rel_set(DISK)
pairs = []
for r in sorted(set(pz) & set(dk)):
    enc = open(dk[r], "rb").read()
    if enc[:4] != b"PYEN":
        continue
    pairs.append((r, enc[20:-16], open(pz[r], "rb").read()))

print("pares:", len(pairs))

def best_periods(ks, top=6):
    n = len(ks)
    scores = []
    for k in range(1, min(257, n)):
        match = sum(1 for i in range(k, n) if ks[i] == ks[i - k])
        scores.append((match / (n - k), k))
    scores.sort(reverse=True)
    return scores[:top]

for r, data, plain in pairs[:8]:
    n = min(len(data), len(plain))
    ks = bytes(a ^ b for a, b in zip(data[:n], plain[:n]))
    bp = best_periods(ks)
    print(f"\n{r}  n={n}")
    print("  top periodos:", ", ".join(f"k={k}:{s:.3f}" for s, k in bp))
