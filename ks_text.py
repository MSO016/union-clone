# Oraculo textual: procura strings esperadas do modulo em cada variante de keystream.
import hashlib, os, re

magic16 = bytes.fromhex("7a3f91c244b80ed5a16c28f355891de7")
salt16  = bytes.fromhex("30072026cafebabedeadf00d12345678")
KEY = hashlib.sha256(magic16 + salt16).digest()

TARGETS = {
    r"D:\MSO\Projects\union-clone\extracted\app\app\database\migrations\001_initial.pyc":
        [b"CREATE TABLE", b"company_settings", b"upgrade"],
    r"D:\MSO\Projects\union-clone\extracted\app\app\utils\_pkg_defs.pyc":
        [b"def ", b"import ", b"__"],
    r"D:\MSO\Projects\union-clone\extracted\app\app\database\downloads_cache.pyc":
        [b"DownloadsCache", b"sqlite3", b"backup"],
}

def variants(key, nonce, n):
    out = {}
    b0 = hashlib.sha256(key + nonce).digest()
    nb = n // 32 + 2
    out["A_rep"] = (b0 * nb)[:n]
    s = bytearray(); h = b0
    while len(s) < n: s += h; h = hashlib.sha256(h).digest()
    out["B_chain"] = bytes(s[:n])
    # C: sha256(key+nonce+i) i = indice de bloco, i a partir de 1 (bloco0 = b0)
    s = bytearray(); i = 0
    while len(s) < n:
        s += b0 if i == 0 else hashlib.sha256(key + nonce + i.to_bytes(4, "little")).digest()
        i += 1
    out["C_blk1up"] = bytes(s[:n])
    # P: sha256(b0 + i) bloco 1.. (i bytes de bloco)
    s = bytearray(); i = 0
    while len(s) < n:
        s += b0 if i == 0 else hashlib.sha256(b0 + i.to_bytes(4, "little")).digest()
        i += 1
    out["H_b0ctr"] = bytes(s[:n])
    # Q: h = sha256(key + h_prev) com h_prev = b0 no bloco0? (ja J)
    # R: sha256(nonce + b0 + i)
    s = bytearray(); i = 0
    while len(s) < n:
        s += b0 if i == 0 else hashlib.sha256(nonce + b0 + i.to_bytes(4, "little")).digest()
        i += 1
    out["R_nbc"] = bytes(s[:n])
    # S: keystream = sha256(key+nonce) XOR contador por bloco
    s = bytearray(); i = 0
    while len(s) < n:
        blk = b0 if i == 0 else bytes(x ^ y for x, y in zip(b0, (i.to_bytes(4, "little") * 8)))
        s += blk; i += 1
    out["S_xorctr"] = bytes(s[:n])
    # T: sha256(sha256(key) + nonce + i)
    kb = hashlib.sha256(key).digest()
    s = bytearray(); i = 0
    while len(s) < n:
        s += b0 if i == 0 else hashlib.sha256(kb + nonce + i.to_bytes(4, "little")).digest()
        i += 1
    out["T_kbnc"] = bytes(s[:n])
    # U: h_{i+1} = sha256(key + nonce + h_i)
    s = bytearray(); h = b0
    while len(s) < n: s += h; h = hashlib.sha256(key + nonce + h).digest()
    out["U_chainknh"] = bytes(s[:n])
    # V: h_{i+1} = sha256(nonce + h_i)
    s = bytearray(); h = b0
    while len(s) < n: s += h; h = hashlib.sha256(nonce + h).digest()
    out["V_chainnh"] = bytes(s[:n])
    # W: keystream bytewise: sha256(key+nonce+i.to_bytes(8)) a cada bloco (8B LE)
    s = bytearray(); i = 0
    while len(s) < n:
        s += b0 if i == 0 else hashlib.sha256(key + nonce + i.to_bytes(8, "little")).digest()
        i += 1
    out["W_blk8"] = bytes(s[:n])
    return out

for path, needles in TARGETS.items():
    blob = open(path, "rb").read()
    nonce, ct = blob[4:20], blob[20:-16]
    print("\n===", os.path.basename(path))
    for vn, ks in variants(KEY, nonce, len(ct)).items():
        pt = bytes(a ^ b for a, b in zip(ct, ks))
        if pt[:4] != bytes.fromhex("f30d0d0a"):
            print(f"  {vn:14} magic-ERR")
            continue
        found = [nd.decode(errors="replace") for nd in needles if nd in pt]
        # conta strings ascii razoaveis no marshal
        strs = re.findall(rb"[\x20-\x7e]{6,}", pt)
        print(f"  {vn:14} alvos={len(found)}/{len(needles)} {found} strings={len(strs)} ex={strs[:3]}")
