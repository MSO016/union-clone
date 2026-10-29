# Oraculo para bloco 1: marshal 3.13 = e3 + argcount(4) + posonly(4) + kwonly(4) + stacksize(4) + flags(4)
# -> bytes 30,31,32 (MSB de stacksize) e 34,35,36 (MSB de flags) = 0.
# logo ks[i] = ct[i] nesses offsets. Compara com b0 (REP32) e mostra os bytes reais.
import hashlib, os, glob

magic16 = bytes.fromhex("7a3f91c244b80ed5a16c28f355891de7")
salt16  = bytes.fromhex("30072026cafebabedeadf00d12345678")
KEY = hashlib.sha256(magic16 + salt16).digest()

DISK = r"D:\MSO\Projects\union-clone\extracted\app\app"
files = []
for root, _, fs in os.walk(DISK):
    for f in fs:
        if f.endswith(".pyc"):
            p = os.path.join(root, f)
            if open(p, "rb").read(4) == b"PYEN":
                files.append(p)
files.sort()
print("arquivos PYEN:", len(files))

ok_rep = 0
ks1_samples = []
for p in files:
    b = open(p, "rb").read()
    nonce, ct = b[4:20], b[20:-16]
    if len(ct) < 40:
        continue
    b0 = hashlib.sha256(KEY + nonce).digest()
    # ks esperado por REP32 nos offsets conhecidos-zero: 32,34,35,36
    rep_ok = all(ct[i] == b0[i % 32] for i in (32, 34, 35, 36))
    ok_rep += rep_ok
    if len(ks1_samples) < 6:
        ks1_samples.append((os.path.basename(p), bytes(ct[i] for i in (32, 34, 35, 36)), bytes(b0[i % 32] for i in (32, 34, 35, 36))))

print(f"REP32 bate nos offsets-zero do bloco1: {ok_rep}/{len(files)}")
for n, ks_ct, ks_rep in ks1_samples:
    print(f"  {n:34} ks_bloco1(ct)={ks_ct.hex()}  rep32(b0)={ks_rep.hex()}")
