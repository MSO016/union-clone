# Decryptor PYEN completo — union v1.3.4.5 (_security_crypto.cp313)
# Formula fechada por RE estatica (Ghidra) + oraculos:
#   A = KEY + NONCE,  KEY = sha256(_PYC_HALF_KEY + _PYC_BUILD_SALT)
#   ks_bloco0 = sha256(A)
#   ks_bloco_i (i=32,64,..) = sha256(A + i.to_bytes(4, 'little'))
#   out[i] = ct[i] ^ ks[i % 32]
# Tag (HMAC-ish) nao e necessaria para o decrypt; validamos por magic marshal.
import hashlib, os, sys

HALF = bytes.fromhex("7a3f91c244b80ed5a16c28f355891de7")
SALT = bytes.fromhex("30072026cafebabedeadf00d12345678")
KEY = hashlib.sha256(HALF + SALT).digest()

def decrypt(blob: bytes) -> bytes:
    if blob[:4] != b"PYEN":
        raise ValueError("nao PYEN")
    nonce, ct, tag = blob[4:20], blob[20:-16], blob[-16:]
    A = KEY + nonce
    ks = hashlib.sha256(A).digest()
    out = bytearray(len(ct))
    for i in range(len(ct)):
        if i % 32 == 0 and i:
            ks = hashlib.sha256(A + i.to_bytes(4, "little")).digest()
        out[i] = ct[i] ^ ks[i % 32]
    return bytes(out)

def main(src_root, dst_root):
    ok = bad = 0
    fails = []
    for root, _, fs in os.walk(src_root):
        for f in fs:
            if not f.endswith(".pyc"):
                continue
            p = os.path.join(root, f)
            with open(p, "rb") as fh:
                b = fh.read()
            if b[:4] != b"PYEN":
                continue
            rel = os.path.relpath(p, src_root)
            try:
                pt = decrypt(b)
            except Exception as e:
                bad += 1
                fails.append((rel, str(e)))
                continue
            # validacao: header py3.13 magic f30d0d0a + marshal TYPE_CODE 0xe3
            if pt[:4] != bytes.fromhex("f30d0d0a") or pt[16] != 0xe3:
                bad += 1
                fails.append((rel, f"magic={pt[:4].hex()} pt[16]={pt[16]:02x}"))
                continue
            dst = os.path.join(dst_root, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "wb") as fh:
                fh.write(pt)
            ok += 1
    print(f"decifrados OK: {ok}   falhas: {bad}")
    for rel, why in fails[:40]:
        print(f"  FAIL {rel}: {why}")
    return bad

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else r"D:\MSO\Projects\union-clone\extracted\app\app"
    dst = sys.argv[2] if len(sys.argv) > 2 else r"D:\MSO\Projects\union-clone\decrypted"
    sys.exit(1 if main(src, dst) else 0)
