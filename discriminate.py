# Discrimina REP32 x CHAIN: decifra o disco e compara com o plaintext do PYZ (build diferente, mas ~igual).
import hashlib, os, glob

magic16 = bytes.fromhex("7a3f91c244b80ed5a16c28f355891de7")
salt16  = bytes.fromhex("30072026cafebabedeadf00d12345678")
KEY = hashlib.sha256(magic16 + salt16).digest()

PYZ = r"D:\MSO\Projects\union-clone\pyz\RESTORECELL.exe_extracted\PYZ.pyz_extracted\app"
DISK = r"D:\MSO\Projects\union-clone\extracted\app\app"

def rel(root):
    return {os.path.relpath(p, root).replace("\\", "/"): p
            for p in glob.glob(os.path.join(root, "**", "*.pyc"), recursive=True)}

pz, dk = rel(PYZ), rel(DISK)

def ks_rep(nonce, n):
    b = hashlib.sha256(KEY + nonce).digest()
    return (b * (n // 32 + 1))[:n]

def ks_chain(nonce, n):
    out = bytearray()
    h = hashlib.sha256(KEY + nonce).digest()
    while len(out) < n:
        out += h
        h = hashlib.sha256(h).digest()
    return bytes(out[:n])

def dec(blob, ks):
    nonce, ct = blob[4:20], blob[20:-16]
    k = ks(nonce, len(ct))
    return bytes(a ^ b for a, b in zip(ct, k))

pairs = []
for r in sorted(set(pz) & set(dk)):
    b = open(dk[r], "rb").read()
    if b[:4] == b"PYEN":
        pairs.append(r)
print("pares:", len(pairs))

agg = {"REP32": [], "CHAIN": []}
for r in pairs:
    pt_d = dec(open(dk[r], "rb").read(), ks_rep if True else ks_chain)
    plain = open(pz[r], "rb").read()
    for name, fn in (("REP32", ks_rep), ("CHAIN", ks_chain)):
        d = dec(open(dk[r], "rb").read(), fn)
        n = min(len(d), len(plain))
        # compara a partir do offset 64 (apos header, onde os keystreams divergem)
        m = sum(1 for i in range(64, n) if d[i] == plain[i])
        agg[name].append(m / max(1, n - 64))

for name in ("REP32", "CHAIN"):
    v = agg[name]
    print(f"{name}: match medio={sum(v)/len(v):.3f}  max={max(v):.3f}  min={min(v):.3f}")
    top = sorted(zip(v, pairs), reverse=True)[:5]
    for s, p in top:
        print(f"   {s:.3f}  {p}")
