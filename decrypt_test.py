# Decrypt PYEN: pt = ct XOR sha256(sha256(magic16+salt16) + nonce) [repetido]
import hashlib, glob, os, sys, marshal

magic16 = bytes.fromhex("7a3f91c244b80ed5a16c28f355891de7")
salt16  = bytes.fromhex("30072026cafebabedeadf00d12345678")
KEY = hashlib.sha256(magic16 + salt16).digest()

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

SAMPLES = [
    r"D:\MSO\Projects\union-clone\extracted\app\app\database\migrations\001_initial.pyc",
    r"D:\MSO\Projects\union-clone\extracted\app\app\utils\_ci_sentinel.pyc",
    r"D:\MSO\Projects\union-clone\extracted\app\app\utils\_pkg_defs.pyc",
    r"D:\MSO\Projects\union-clone\extracted\app\app\database\downloads_cache.pyc",
]

for p in SAMPLES:
    blob = open(p, "rb").read()
    assert blob[:4] == b"PYEN", p
    nonce, ct, tag = blob[4:20], blob[20:-16], blob[-16:]
    print("\n===", os.path.basename(p), f"ct={len(ct)}")
    for name, fn in (("REP32", ks_rep), ("CHAIN", ks_chain)):
        ks = fn(nonce, len(ct))
        pt = bytes(a ^ b for a, b in zip(ct, ks))
        ok_magic = pt[:4] == bytes.fromhex("f30d0d0a")
        flags_ok = pt[4:8] == b"\0\0\0\0"
        # profundidade: strings legiveis no fim do arquivo
        tail = pt[-400:]
        ascii_tail = sum(1 for c in tail if 32 <= c < 127 or c in (10, 13, 9)) / len(tail)
        b16 = pt[16]
        print(f"  {name}: magic={ok_magic} flags0={flags_ok} pt[16]=0x{b16:02x} ascii_tail={ascii_tail:.2f}")
        if ok_magic:
            head = pt[:24]
            print("    head:", head.hex())
            # tenta marshal (pode falhar entre versoes 3.13/3.14)
            try:
                co = marshal.loads(pt[16:])
                print("    marshal OK: code", getattr(co, "co_name", "?"), "consts:", len(getattr(co, "co_consts", []) or []))
            except Exception as e:
                print("    marshal falhou:", type(e).__name__, e)
