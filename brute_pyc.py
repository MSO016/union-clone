# Forca-bruta dirigida do formato PYEN usando constantes extraidas do .pyd.
import hashlib, hmac, base64, itertools, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

SAMPLE = r"D:\MSO\Projects\union-clone\extracted\app\app\database\migrations\001_initial.pyc"
blob = open(SAMPLE, "rb").read()
assert blob[:4] == b"PYEN"
nonce, ct, tag = blob[4:20], blob[20:-16], blob[-16:]
MAGIC313 = bytes.fromhex("f30d0d0a")
print(f"nonce={nonce.hex()} ct={len(ct)}B tag={tag.hex()}")

# materiais candidatos (strings do modulo)
mats = [
    "union_sol_2026_v2", "PYC_BUILD_SALT", "PYC_HALF_KEY", "PYC_MAGIC",
    "fallback_key", "_union_2026", "union_2026", "PYEN", "UNI",
    "_KEY_CACHE", "MAGIC", "PYC_BUILD_SALT_union_sol_2026_v2",
    "union_sol_2026_v2_PYC_BUILD_SALT", "PYENUNI", "UNIPYEN",
]
try:
    keyfile = open(r"D:\MSO\Projects\union-clone\extracted\app\app\database\.key", "rb").read().strip()
    mats += [keyfile.decode(), "6doKwDJrTMBjPKig0u4rBgEaW57vjxY9vq06MxuBbwU="]
except Exception as e:
    print("sem .key:", e)

def keys_for(m: bytes):
    out = {}
    out["raw"] = m
    out["sha256"] = hashlib.sha256(m).digest()
    out["sha512-32"] = hashlib.sha512(m).digest()[:32]
    try:
        out["b64"] = base64.b64decode(m, validate=True)
    except Exception:
        pass
    if len(m) in (16, 24, 32):
        out["pad"] = m.ljust(32, b"\0")
    return out

def check(pt, label):
    if pt and pt[:4] == MAGIC313:
        print("*** MATCH:", label, "len=", len(pt), "head=", pt[:24].hex())
        return True
    return False

found = False
tested = 0
for m in mats:
    mb = m.encode() if isinstance(m, str) else m
    for kn, key in keys_for(mb).items():
        if len(key) not in (16, 24, 32):
            continue
        # 1) AES-GCM
        tested += 1
        try:
            pt = AESGCM(key).decrypt(nonce, ct + tag, None)
            if check(pt, f"AESGCM key={m!r}/{kn}"):
                found = True
        except Exception:
            pass
        try:
            pt = AESGCM(key).decrypt(nonce, ct + tag, b"PYEN")
            if check(pt, f"AESGCM+AAD key={m!r}/{kn}"):
                found = True
        except Exception:
            pass
        # 2) XOR keystream repetido (sha256(key+nonce) etc.)
        for ksn, ks in (
            ("sha256(key+nonce)", hashlib.sha256(key + nonce).digest()),
            ("sha256(nonce+key)", hashlib.sha256(nonce + key).digest()),
            ("sha256(key)", hashlib.sha256(key).digest()),
            ("hmac(key,nonce)", hmac.new(key, nonce, hashlib.sha256).digest()),
            ("key32", key if len(key) == 32 else hashlib.sha256(key).digest()),
        ):
            rep = (ks * (len(ct) // len(ks) + 1))[:len(ct)]
            pt = bytes(a ^ b for a, b in zip(ct, rep))
            tested += 1
            if check(pt, f"XOR rep {ksn} key={m!r}/{kn}"):
                found = True
        # 3) XOR com blocos encadeados sha256(key||i||nonce)
        for order in ("kiN", "ki", "Ni"):
            out = bytearray()
            i = 0
            while len(out) < len(ct):
                if order == "kiN":
                    h = hashlib.sha256(key + bytes([i]) + nonce).digest()
                elif order == "ki":
                    h = hashlib.sha256(key + bytes([i])).digest()
                else:
                    h = hashlib.sha256(nonce + bytes([i]) + key).digest()
                out += h
                i += 1
            pt = bytes(a ^ b for a, b in zip(ct, out[:len(ct)]))
            tested += 1
            if check(pt, f"XOR blk {order} key={m!r}/{kn}"):
                found = True

print(f"testes={tested}  match={found}")
