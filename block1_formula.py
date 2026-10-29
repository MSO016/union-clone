# Testa a formula do keystream do bloco 1 (i=32) extraida do dump Ghidra:
#   ks = sha256(A + i.to_bytes(4, 'little')).digest(),  A = KEY + NONCE
# Oraculo marshal 3.13: pt[32]=0 (MSB de stacksize), pt[34]=0, pt[35]=0 (bytes de flags)
# -> ks1[0]=ct[32], ks1[2]=ct[34], ks1[3]=ct[35]  (pt[36] pode ser 1 com __future__ annotations)
import hashlib, os

KEY = hashlib.sha256(bytes.fromhex(
    "7a3f91c244b80ed5a16c28f355891de7" + "30072026cafebabedeadf00d12345678")).digest()

DISK = r"D:\MSO\Projects\union-clone\extracted\app\app"
files = []
for root, _, fs in os.walk(DISK):
    for f in fs:
        if f.endswith(".pyc"):
            p = os.path.join(root, f)
            with open(p, "rb") as fh:
                if fh.read(4) == b"PYEN":
                    files.append(p)
files.sort()
print("arquivos PYEN:", len(files))

def candidates(A, i, blk):
    K, N = KEY, A[32:]  # nonce
    return {
        "A+le32(i)":   A + i.to_bytes(4, "little"),
        "A+be32(i)":   A + i.to_bytes(4, "big"),
        "A+le32(blk)": A + blk.to_bytes(4, "little"),
        "A+be32(blk)": A + blk.to_bytes(4, "big"),
        "A+le8(i)":    A + i.to_bytes(8, "little"),
        "A+be8(i)":    A + i.to_bytes(8, "big"),
        "A+le8(blk)":  A + blk.to_bytes(8, "little"),
        "A+be8(blk)":  A + blk.to_bytes(8, "big"),
        "A+byte(i)":   A + bytes([i & 0xFF]),
        "A+byte(blk)": A + bytes([blk]),
        "le32(i)+A":   i.to_bytes(4, "little") + A,
        "be32(i)+A":   i.to_bytes(4, "big") + A,
        "A+le16(i)":   A + i.to_bytes(2, "little"),
        "A+le16(blk)": A + blk.to_bytes(2, "little"),
        "K+le32(i)":   K + i.to_bytes(4, "little"),
        "N+le32(i)":   N + i.to_bytes(4, "little"),
        "K+N+le32":    K + N + i.to_bytes(4, "little"),
        "A":           A,  # REP32 baseline
    }

scores = {}
for p in files:
    b = open(p, "rb").read()
    nonce, ct = b[4:20], b[20:-16]
    if len(ct) < 40:
        continue
    A = KEY + nonce
    exp = (ct[32], ct[34], ct[35], ct[36])  # ks1[0], ks1[2], ks1[3], ks1[4]
    for name, inp in candidates(A, 32, 1).items():
        d = hashlib.sha256(inp).digest()
        got = (d[0], d[2], d[3], d[4])
        m3 = sum(x == y for x, y in zip(got[:3], exp[:3]))
        m4 = sum(x == y for x, y in zip(got, exp))
        s = scores.setdefault(name, [0, 0])
        s[0] += m3
        s[1] += m4

n = sum(1 for p in files if len(open(p, "rb").read()) > 40)
print(f"oraculo solido (j=0,2,3): {3*n} pontos; fraco (j=4): +{n}")
for name, (s3, s4) in sorted(scores.items(), key=lambda kv: -kv[1][0]):
    print(f"  {name:12} solido={s3:5}/{3*n}  com-j4={s4:5}/{4*n}")
