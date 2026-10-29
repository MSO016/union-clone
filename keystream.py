# Deriva o keystream PYEN comparando modulo puro (PYZ) x cifrado (disco).
import os, sys, glob, hashlib, collections

PYZ = r"D:\MSO\Projects\union-clone\pyz\RESTORECELL.exe_extracted\PYZ.pyz_extracted\app"
DISK = r"D:\MSO\Projects\union-clone\extracted\app\app"

def rel_set(root):
    out = {}
    for p in glob.glob(os.path.join(root, "**", "*.pyc"), recursive=True):
        r = os.path.relpath(p, root).replace("\\", "/")
        out[r] = p
    return out

pz = rel_set(PYZ)
dk = rel_set(DISK)
common = sorted(set(pz) & set(dk))
print(f"puro={len(pz)} cifrado={len(dk)} comuns={len(common)}")

pairs = []
for r in common:
    enc = open(dk[r], "rb").read()
    if enc[:4] != b"PYEN":
        continue
    plain = open(pz[r], "rb").read()
    nonce, data, tag = enc[4:20], enc[20:-16], enc[-16:]
    pairs.append((r, nonce, data, tag, plain))
print(f"pares PYEN x puro: {len(pairs)}")

for r, nonce, data, tag, plain in pairs[:6]:
    print("\n---", r)
    print("  enc data:", len(data), " plain:", len(plain))
    print("  data[:12] :", data[:12].hex())
    print("  plain[:12]:", plain[:12].hex())
    n = min(len(data), len(plain))
    ks = bytes(a ^ b for a, b in zip(data[:n], plain[:n]))
    # procura periodo do keystream
    per = None
    for k in range(1, 129):
        if all(ks[i] == ks[i - k] for i in range(k, n)):
            per = k
            break
    print("  keystream[:16]:", ks[:16].hex(), " periodo:", per)
    if per:
        print("  bloco-chave:", ks[:per].hex())

# se nao houver periodo, talvez o header do plain difira -> alinha pelo magic
print("\n=== se header difere: compara so apos byte 16 ===")
for r, nonce, data, tag, plain in pairs[:3]:
    n = min(len(data), len(plain))
    ks = bytes(a ^ b for a, b in zip(data[:n], plain[:n]))
    per = None
    for k in range(1, 129):
        if all(ks[i] == ks[i - k] for i in range(k, n)):
            per = k
            break
    print(f"  {r}: n={n} periodo={per}")
