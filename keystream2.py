# Hipotese: DATA = zlib.compress(pyc) XOR keystream (periodo K)
import os, glob, zlib, itertools

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
    pairs.append((r, enc[4:20], enc[20:-16], enc[-16:], open(pz[r], "rb").read()))
print("pares:", len(pairs))

def periodicity(buf, maxk=128):
    for k in range(1, min(maxk, len(buf)) + 1):
        if all(buf[i] == buf[i - k] for i in range(k, len(buf))):
            return k
    return None

# Testa niveis de compressao
for level in (6, 9, 1):
    results = []
    for r, nonce, data, tag, plain in pairs[:8]:
        for wbits in (15, -15, 31):
            try:
                c = zlib.compress(plain, level) if wbits == 15 else zlib.compress(plain, level, wbits)
            except Exception:
                continue
            n = min(len(c), len(data))
            if n < 64:
                continue
            ks = bytes(a ^ b for a, b in zip(data[:n], c[:n]))
            results.append((r, wbits, len(c), len(data), periodicity(ks), ks[:12].hex()))
            break
    print(f"\n=== level {level} ===")
    for x in results:
        print("  ", x)

# Se keystream e constante entre arquivos, data1^comp1 == data2^comp2
print("\n=== igualdade entre arquivos (level 6, wbits 15) ===")
ks_list = []
for r, nonce, data, tag, plain in pairs[:4]:
    c = zlib.compress(plain, 6)
    n = min(len(c), len(data))
    ks = bytes(a ^ b for a, b in zip(data[:n], c[:n]))
    ks_list.append((r, ks))
    print(f"  {r}: comp={len(c)} data={len(data)} ks[:16]={ks[:16].hex()} per={periodicity(ks)}")
if len(ks_list) > 1:
    a, b = ks_list[0][1], ks_list[1][1]
    n = min(len(a), len(b))
    print("  ks igual?", a[:n] == b[:n])
