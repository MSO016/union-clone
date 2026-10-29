# Testa hipotese de decrypt PYEN: AES-256-GCM com chave do database\.key
# Formato docstring: [MAGIC 4][NONCE 16][DATA][TAG 16]
import base64, hashlib, sys, os

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    print("falta 'cryptography' -> pip install cryptography"); sys.exit(2)

BASE = r"D:\MSO\Projects\union-clone\extracted\app\app"
keyfile = os.path.join(BASE, "database", ".key")
sample = os.path.join(BASE, "controllers", "login_controller.pyc")

raw_key = open(keyfile, "rb").read().strip()
print("key file:", raw_key)

blob = open(sample, "rb").read()
print("sample:", len(blob), "bytes, magic:", blob[:4])

nonce = blob[4:20]
tag = blob[-16:]
ct = blob[20:-16]
print("nonce:", nonce.hex(), "tag:", tag.hex(), "ct:", len(ct))

candidates = {}
try:
    candidates["keyfile-b64"] = base64.b64decode(raw_key)
except Exception as e:
    print("b64 decode falhou:", e)
candidates["keyfile-sha256"] = hashlib.sha256(raw_key).digest()
candidates["keyfile-raw-sha256"] = hashlib.sha256(base64.b64decode(raw_key)).digest() if "keyfile-b64" in candidates else None
candidates["hardcoded-pad"] = b"0" * 32
candidates["PYEN-salt"] = hashlib.sha256(b"PYEN").digest()

py313 = bytes([0xF3, 0x0D, 0x0D, 0x0A])

for name, key in candidates.items():
    if not key or len(key) not in (16, 24, 32):
        print(f"  [{name}] tamanho invalido ({len(key) if key else 0})"); continue
    for aad_label, aad in (("sem-aad", None), ("aad-magic", b"PYEN")):
        try:
            pt = AESGCM(key).decrypt(nonce, ct, aad)
            head = pt[:16].hex()
            ok = pt[:4] == py313
            print(f"  [{name}] aad={aad_label} -> SUCESSO! len={len(pt)} head={head} py313={ok}")
            if ok:
                out = sample + ".dec"
                open(out, "wb").write(pt)
                print("  salvo:", out)
                sys.exit(0)
        except Exception as e:
            print(f"  [{name}] aad={aad_label} -> falhou: {type(e).__name__}: {e}")
print("nenhuma combinacao funcionou")
sys.exit(1)
