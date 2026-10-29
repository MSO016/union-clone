# Testa variantes de keystream e usa pycdc-new como oraculo de validade do marshal.
import hashlib, os, subprocess, sys

magic16 = bytes.fromhex("7a3f91c244b80ed5a16c28f355891de7")
salt16  = bytes.fromhex("30072026cafebabedeadf00d12345678")
KEY = hashlib.sha256(magic16 + salt16).digest()
PYCDC = r"D:\MSO\Projects\union-clone\tools\pycdc-new.exe"
OUT = r"D:\MSO\Projects\union-clone\ks-test"
os.makedirs(OUT, exist_ok=True)

SAMPLES = [
    r"D:\MSO\Projects\union-clone\extracted\app\app\database\migrations\001_initial.pyc",
    r"D:\MSO\Projects\union-clone\extracted\app\app\utils\_pkg_defs.pyc",
]

def variants(key, nonce, n):
    nb = (n + 31) // 32
    out = {}
    b0 = hashlib.sha256(key + nonce).digest()
    # A: repetido
    out["A_rep"] = (b0 * (nb + 1))[:n]
    # B: cadeia h=sha256(h)
    s = bytearray(); h = b0
    while len(s) < n:
        s += h; h = hashlib.sha256(h).digest()
    out["B_chain"] = bytes(s[:n])
    # E: sha256(key+nonce+byte(i)) i=byte index
    s = bytearray(); i = 0
    while len(s) < n:
        s += hashlib.sha256(key + nonce + bytes([i & 0xFF])).digest() if i else b0
        i += 1
    out["E_byteidx"] = bytes(s[:n])
    # H: sha256(b0 + i.to_bytes(4,'little')) por bloco
    s = bytearray(); i = 0
    while len(s) < n:
        s += b0 if i == 0 else hashlib.sha256(b0 + i.to_bytes(4, "little")).digest()
        i += 1
    out["H_b0ctr"] = bytes(s[:n])
    # H2: sha256(b0 + i.to_bytes(4)) por bloco (inclui 0)
    s = bytearray(); i = 0
    while len(s) < n:
        s += hashlib.sha256(b0 + i.to_bytes(4, "little")).digest()
        i += 1
    out["H2_b0ctr0"] = bytes(s[:n])
    # I: h0=b0; h=sha256(h+nonce)
    s = bytearray(); h = b0
    while len(s) < n:
        s += h; h = hashlib.sha256(h + nonce).digest()
    out["I_chain_nonce"] = bytes(s[:n])
    # J: h=sha256(key+h)
    s = bytearray(); h = b0
    while len(s) < n:
        s += h; h = hashlib.sha256(key + h).digest()
    out["J_chain_key"] = bytes(s[:n])
    # K: sha256(key + nonce + i.to_bytes(4,'little')) por bloco (counter=block idx)
    s = bytearray(); i = 0
    while len(s) < n:
        s += hashlib.sha256(key + nonce + i.to_bytes(4, "little")).digest()
        i += 1
    out["K_blkctr"] = bytes(s[:n])
    # L: sha256(nonce + key + i.to_bytes(4)) por bloco
    s = bytearray(); i = 0
    while len(s) < n:
        s += hashlib.sha256(nonce + key + i.to_bytes(4, "little")).digest()
        i += 1
    out["L_nkc"] = bytes(s[:n])
    # M: sha256(key + i.to_bytes(4) + nonce)
    s = bytearray(); i = 0
    while len(s) < n:
        s += hashlib.sha256(key + i.to_bytes(4, "little") + nonce).digest()
        i += 1
    out["M_kcn"] = bytes(s[:n])
    # N: sha256(nonce + i.to_bytes(4) + key)
    s = bytearray(); i = 0
    while len(s) < n:
        s += hashlib.sha256(nonce + i.to_bytes(4, "little") + key).digest()
        i += 1
    out["N_nck"] = bytes(s[:n])
    # O: chain duplo sha256
    s = bytearray(); h = b0
    while len(s) < n:
        s += h; h = hashlib.sha256(hashlib.sha256(h).digest()).digest()
    out["O_dblchain"] = bytes(s[:n])
    return out

results = {}
for sp in SAMPLES:
    blob = open(sp, "rb").read()
    nonce, ct = blob[4:20], blob[20:-16]
    name = os.path.basename(sp)
    for vn, ks in variants(KEY, nonce, len(ct)).items():
        pt = bytes(a ^ b for a, b in zip(ct, ks))
        if pt[:4] != bytes.fromhex("f30d0d0a"):
            results[(name, vn)] = "magic-ERR"
            continue
        p = os.path.join(OUT, f"{vn}_{name}")
        open(p, "wb").write(pt)
        try:
            r = subprocess.run([PYCDC, p], capture_output=True, timeout=60)
        except Exception as e:
            results[(name, vn)] = f"run-ERR {e}"
            continue
        txt = (r.stdout or b"").decode("utf-8", "replace") + (r.stderr or b"").decode("utf-8", "replace")
        score = sum(txt.count(k) for k in ("def ", "class ", "import ", "self.", "return "))
        err = txt.count("Syntax Error") + txt.count("WARNING")
        results[(name, vn)] = f"score={score} err={err} len={len(txt)}"

names = [os.path.basename(p) for p in SAMPLES]
print(f"{'variante':16} " + "  ".join(names))
vs = sorted({v for _, v in results})
for v in vs:
    row = [str(results.get((n, v), "-")) for n in names]
    print(f"{v:16} " + "  |  ".join(row))
