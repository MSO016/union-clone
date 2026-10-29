# Busca ampla: constantes string + binarias, varios esquemas, verifica magic 3.13 ou zlib.
import hashlib, hmac, base64, itertools, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

SAMPLE = r"D:\MSO\Projects\union-clone\extracted\app\app\database\migrations\001_initial.pyc"
blob = open(SAMPLE, "rb").read()
nonce, ct, tag = blob[4:20], blob[20:-16], blob[-16:]
MAGIC313 = bytes.fromhex("f30d0d0a")

STRINGS = [
    "union_sol_2026_v2", "PYC_BUILD_SALT", "PYC_HALF_KEY", "PYC_MAGIC",
    "fallback_key_union_2026", "fallback_key", "_union_2026", "union_2026",
    "PYEN", "UNI", "PYENUNI", "_KEY_CACHE", "MAGIC", "_security_crypto.py",
    "union_sol", "2026", "union", "sol",
]
BYTES = [
    bytes.fromhex("30072026cafebabedeadf00d12345678"),
    bytes(32),
    bytes.fromhex("8001e0040b883590049043907198069863a012a034a074a832a853b003b031"),
    bytes.fromhex("7a3f91c244b80ed5a16c28f355891de7"),
    b"PYEN", b"UNI", b"fallback_key_union_2026",
]
try:
    KEYFILE = open(r"D:\MSO\Projects\union-clone\extracted\app\app\database\.key", "rb").read().strip()
except Exception:
    KEYFILE = b""

def materials():
    for s in STRINGS:
        yield s.encode()
    for bb in BYTES:
        yield bb
    if KEYFILE:
        yield KEYFILE
        try: yield base64.b64decode(KEYFILE)
        except Exception: pass
    # pares (concat com separadores)
    base = [s.encode() for s in STRINGS] + BYTES[:2]
    for a, b in itertools.product(base, base):
        if a == b: continue
        for sep in (b"", b"_", b":", b"|"):
            yield a + sep + b

def keys_of(m):
    out = { "sha256": hashlib.sha256(m).digest() }
    if len(m) in (16, 24, 32): out["raw"] = m
    if len(m) < 32: out["pad"] = m.ljust(32, b"\0")
    if len(m) > 32: out["sha512"] = hashlib.sha512(m).digest()
    try:
        d = base64.b64decode(m, validate=True)
        if len(d) in (16, 24, 32): out["b64"] = d
    except Exception: pass
    return out

def ok(pt):
    return pt[:4] == MAGIC313 or pt[:2] in (b"x\x9c", b"x\xda", b"x\x01")

tested = 0
hits = []
for m in materials():
    for kn, key in keys_of(m).items():
        # AES-GCM
        for nk, nk_name in ((nonce, "n16"), (nonce[:12], "n12"), (nonce[4:], "n12b")):
            for aad in (None, b"PYEN"):
                tested += 1
                try:
                    pt = AESGCM(key).decrypt(nk, ct + tag, aad)
                    if ok(pt): hits.append(("AESGCM", m[:40], kn, nk_name, aad, pt[:32]))
                except Exception: pass
        # AES-CTR (nonce 16)
        tested += 1
        try:
            d = Cipher(algorithms.AES(key), modes.CTR(nonce)).decryptor()
            pt = d.update(ct) + d.finalize()
            if ok(pt): hits.append(("AESCTR", m[:40], kn, "n16", None, pt[:32]))
        except Exception: pass
        # XOR keystream
        for lbl, ks in (
            ("sha256(k+n)", hashlib.sha256(key + nonce).digest()),
            ("sha256(n+k)", hashlib.sha256(nonce + key).digest()),
            ("sha256(k)",   hashlib.sha256(key).digest()),
            ("hmac(k,n)",   hmac.new(key, nonce, hashlib.sha256).digest()),
        ):
            tested += 1
            rep = (ks * (len(ct)//len(ks) + 1))[:len(ct)]
            pt = bytes(a ^ b for a, b in zip(ct, rep))
            if ok(pt): hits.append(("XOR-" + lbl, m[:40], kn, "n16", None, pt[:32]))

    if tested % 20000 == 0: print("...", tested, flush=True)

print(f"testes={tested}  hits={len(hits)}")
for h in hits:
    print("  HIT:", h)
