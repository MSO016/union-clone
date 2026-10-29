# Brute PYEN com oraculo de plaintext conhecido (magic 3.13 = f30d0d0a + flags 0).
# ks em blocos de 32; verifica apenas os primeiros 8 bytes -> rapidissimo.
import hashlib, itertools, base64, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

SAMPLES = [
    r"D:\MSO\Projects\union-clone\extracted\app\app\database\migrations\001_initial.pyc",
    r"D:\MSO\Projects\union-clone\extracted\app\app\utils\_ci_sentinel.pyc",
]
MAGIC = bytes.fromhex("f30d0d0a00000000")  # magic + flags=0 (8 bytes conhecidos)

salt16 = bytes.fromhex("30072026cafebabedeadf00d12345678")
magic16 = bytes.fromhex("7a3f91c244b80ed5a16c28f355891de7")
b16_alt = bytes.fromhex("8001d8040b883790279811982ea802d02a3ab827c011")
k32 = bytes.fromhex("8001e0040b883590049043907198069863a012a034a074a832a853b003b031")
z32 = bytes(32)
try:
    KEYFILE = open(r"D:\MSO\Projects\union-clone\extracted\app\app\database\.key", "rb").read().strip()
except Exception:
    KEYFILE = b""

MAT = {
    "salt16": salt16, "magic16": magic16, "b16alt": b16_alt, "k32": k32, "z32": z32,
    "PYEN": b"PYEN", "UNI": b"UNI", "fallback": b"fallback_key_union_2026",
    "union_str": b"union_sol_2026_v2", "keyfile": KEYFILE,
    "keyfile_raw": base64.b64decode(KEYFILE) if KEYFILE else b"",
}

# ---- k1 = candidatos a chave derivada (_pyc_derive_key e misturas) ----
k1 = {}
for n, v in MAT.items():
    if not v:
        continue
    k1["sha256(" + n + ")"] = hashlib.sha256(v).digest()
    if len(v) in (16, 24, 32):
        k1[n] = v if len(v) == 32 else v.ljust(32, b"\0")
for (na, a), (nb, b) in itertools.product(MAT.items(), MAT.items()):
    if not a or not b:
        continue
    k1[f"sha256({na}+{nb})"] = hashlib.sha256(a + b).digest()
# pares com separador (so strings pequenas)
for sep in (b"_", b":", b"|"):
    for na, a in MAT.items():
        for nb, b in MAT.items():
            if not a or not b or len(a) > 40 or len(b) > 40:
                continue
            k1[f"sha256({na}{sep.decode(errors='replace')}{nb})"] = hashlib.sha256(a + sep + b).digest()

print(f"materiais={len(MAT)} chaves k1={len(k1)}")

def check8(pt8):
    return pt8 == MAGIC

hits = []
tested = 0

for path in SAMPLES:
    blob = open(path, "rb").read()
    nonce, ct, tag = blob[4:20], blob[20:-16], blob[-16:]
    n = len(ct)
    nb = (n + 31) // 32

    def report(label):
        hits.append((path.split("\\")[-1], label))

    for kn, key in k1.items():
        # 1) keystream = bloco unico repetido (periodo 32)
        for lbl, ks32 in (
            ("sha256(k+n)", hashlib.sha256(key + nonce).digest()),
            ("sha256(n+k)", hashlib.sha256(nonce + key).digest()),
            ("sha256(k+n+0)", hashlib.sha256(key + nonce + b"\x00" * 4).digest()),
            ("sha256(n+k+0)", hashlib.sha256(nonce + b"\x00" * 4 + key).digest()),
            ("k", key),
            ("k^n_rep", bytes(x ^ y for x, y in zip(key, (nonce * 3)[:32]))),
            ("hmac(k,n)", __import__("hmac").new(key, nonce, hashlib.sha256).digest()),
        ):
            tested += 1
            if check8(bytes(a ^ b for a, b in zip(ct[:8], ks32[:8]))):
                report(f"REP32 {lbl} key={kn}")
        # 2) AES-CTR / AES-GCM com k1
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            tested += 1
            d = Cipher(algorithms.AES(key), modes.CTR(nonce)).decryptor()
            pt8 = d.update(ct[:8])
            if check8(pt8):
                report(f"AES-CTR key={kn}")
        except Exception:
            pass
        try:
            tested += 1
            pt8 = AESGCM(key).decrypt(nonce, ct[:8 + 0], None) if False else None
        except Exception:
            pass
        # 3) stream em blocos com contador
        for tmpl, ctrs in (
            ("k+n+c", [("4L", None), ("8L", None), ("4B", None), ("s", None)]),
            ("k+c+n", [("4L", None), ("8L", None), ("4B", None), ("s", None)]),
            ("n+c+k", [("4L", None), ("8L", None), ("4B", None), ("s", None)]),
            ("c+k+n", [("4L", None), ("8L", None), ("4B", None), ("s", None)]),
            ("n+k+c", [("4L", None), ("8L", None), ("4B", None), ("s", None)]),
        ):
            for ctrmode, _ in ctrs:
                b0i = 0
                if tmpl == "k+n+c":
                    if ctrmode == "4L": c = (0).to_bytes(4, "little"); h = hashlib.sha256(key + nonce + c).digest()
                    elif ctrmode == "8L": c = (0).to_bytes(8, "little"); h = hashlib.sha256(key + nonce + c).digest()
                    elif ctrmode == "4B": c = (0).to_bytes(4, "big"); h = hashlib.sha256(key + nonce + c).digest()
                    else: h = hashlib.sha256(key + nonce + b"0").digest()
                elif tmpl == "k+c+n":
                    if ctrmode == "4L": c = (0).to_bytes(4, "little"); h = hashlib.sha256(key + c + nonce).digest()
                    elif ctrmode == "8L": c = (0).to_bytes(8, "little"); h = hashlib.sha256(key + c + nonce).digest()
                    elif ctrmode == "4B": c = (0).to_bytes(4, "big"); h = hashlib.sha256(key + c + nonce).digest()
                    else: h = hashlib.sha256(key + b"0" + nonce).digest()
                elif tmpl == "n+c+k":
                    if ctrmode == "4L": c = (0).to_bytes(4, "little"); h = hashlib.sha256(nonce + c + key).digest()
                    elif ctrmode == "8L": c = (0).to_bytes(8, "little"); h = hashlib.sha256(nonce + c + key).digest()
                    elif ctrmode == "4B": c = (0).to_bytes(4, "big"); h = hashlib.sha256(nonce + c + key).digest()
                    else: h = hashlib.sha256(nonce + b"0" + key).digest()
                elif tmpl == "c+k+n":
                    if ctrmode == "4L": c = (0).to_bytes(4, "little"); h = hashlib.sha256(c + key + nonce).digest()
                    elif ctrmode == "8L": c = (0).to_bytes(8, "little"); h = hashlib.sha256(c + key + nonce).digest()
                    elif ctrmode == "4B": c = (0).to_bytes(4, "big"); h = hashlib.sha256(c + key + nonce).digest()
                    else: h = hashlib.sha256(b"0" + key + nonce).digest()
                else:  # n+k+c
                    if ctrmode == "4L": c = (0).to_bytes(4, "little"); h = hashlib.sha256(nonce + key + c).digest()
                    elif ctrmode == "8L": c = (0).to_bytes(8, "little"); h = hashlib.sha256(nonce + key + c).digest()
                    elif ctrmode == "4B": c = (0).to_bytes(4, "big"); h = hashlib.sha256(nonce + key + c).digest()
                    else: h = hashlib.sha256(nonce + key + b"0").digest()
                tested += 1
                if check8(bytes(a ^ b for a, b in zip(ct[:8], h[:8]))):
                    report(f"BLK {tmpl}/{ctrmode} key={kn}")
        # 4) cadeia encadeada h0=sha256(k+n), h{i+1}=sha256(h{i})
        h = hashlib.sha256(key + nonce).digest()
        tested += 1
        if check8(bytes(a ^ b for a, b in zip(ct[:8], h[:8]))):
            report(f"CHAIN k+n key={kn}")
        # 5) nonce aplicado por XOR antes do keystream fixo
        tested += 1
        ks = bytes(a ^ b for a, b in zip(key, (nonce * 2)[:32]))
        if check8(bytes(a ^ b for a, b in zip(ct[:8], ks[:8]))):
            report(f"XOR-NONCE key={kn}")

print(f"testes={tested} hits={len(hits)}")
for h in hits[:40]:
    print("  HIT:", h)
