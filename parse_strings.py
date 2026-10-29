# Parse robusto: lines da tabela de comprimentos + blob zlib -> strings do modulo.
import re, zlib

C = r"D:\MSO\Projects\union-clone\decomp\native\_security_crypto.c"
PYD = r"D:\MSO\Projects\union-clone\extracted\app\app\utils\_security_crypto.cp313-win_amd64.pyd"
OUT = r"D:\MSO\Projects\union-clone\cython-strings.txt"

lines = open(C, encoding="utf-8", errors="replace").read().splitlines()
start = next(i for i, l in enumerate(lines) if l.strip() == "local_1f8 = 1;")
end = next(i for i, l in enumerate(lines) if "PyUnicode_FromString" in l and i > start)
lengths = []
for l in lines[start:end]:
    m = re.match(r"\s*local_[0-9a-f]+ = (0x[0-9a-f]+|\d+);\s*$", l)
    if m:
        lengths.append(int(m.group(1), 0) & 0xFF)
print("comprimentos capturados:", len(lengths))

b = open(PYD, "rb").read()
blob = zlib.decompress(b[0xffd0:])
print("blob:", len(blob))

# se faltam entradas, completa greedy: procura o valor faltante que faz o parse bater
def try_parse(lens, n_uni, n_byt):
    if len(lens) < n_uni + n_byt:
        return None
    pos = 0
    uni, byt = [], []
    for n in lens[:n_uni]:
        if pos + n > len(blob): return None
        uni.append(blob[pos:pos + n]); pos += n
    for n in lens[n_uni:n_uni + n_byt]:
        if pos + n > len(blob): return None
        byt.append(blob[pos:pos + n]); pos += n
    return uni, byt, pos

# completa com 0.. ate bater
res = None
missing = 90 + 19 - len(lengths)
print("faltando:", missing)
if missing == 1:
    for pos_ins in range(len(lengths) + 1):
        for val in range(0, 256):
            cand = lengths[:pos_ins] + [val] + lengths[pos_ins:]
            r = try_parse(cand, 90, 19)
            if r and r[2] == len(blob):
                res = (cand, r)
                print(f"  inserido {val} na posicao {pos_ins}")
                break
        if res: break
else:
    r = try_parse(lengths, 90, 19)
    if r: res = (lengths, r)

if not res:
    print("parse nao bateu; usando greedy com o que temos")
    r = try_parse(lengths + [1] * 4, 90, 19)
    res = (lengths, r)

lens, (uni, byt, pos) = res
print(f"consumido {pos}/{len(blob)}")

out = []
out.append(f"# strings do modulo _security_crypto (109 constantes)")
for i, s in enumerate(uni):
    out.append(f"{i:3} str  {s.decode('utf-8', 'replace')!r}")
for i, s in enumerate(byt):
    out.append(f"{90+i:3} bytes {s!r} hex={s.hex()}")
open(OUT, "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
