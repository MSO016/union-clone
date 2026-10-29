// Le bytes/strings em endereços virtuais (VA) de um PE.
// uso: node peva.js <exe> <va1> <va2> ...
const fs = require("fs");
const file = process.argv[2];
const vas = process.argv.slice(3);
const b = fs.readFileSync(file);

const peOff = b.readUInt32LE(0x3c);
const nsec = b.readUInt16LE(peOff + 6);
const optSize = b.readUInt16LE(peOff + 20);
const optOff = peOff + 24;
const magic = b.readUInt16LE(optOff);
const imageBase = magic === 0x20b ? Number(b.readBigUInt64LE(optOff + 24)) : b.readUInt32LE(optOff + 28);
const secOff = optOff + optSize;

const secs = [];
for (let i = 0; i < nsec; i++) {
  const o = secOff + i * 40;
  const name = b.slice(o, o + 8).toString("latin1").replace(/\0.*$/, "");
  const vsize = b.readUInt32LE(o + 8);
  const va = b.readUInt32LE(o + 12);
  const rsize = b.readUInt32LE(o + 16);
  const raw = b.readUInt32LE(o + 20);
  secs.push({ name, va, vsize, raw, rsize });
}
console.log("imageBase=0x" + imageBase.toString(16));
for (const s of secs) console.log(`  ${s.name.padEnd(9)} va=0x${s.va.toString(16)} raw=0x${s.raw.toString(16)} vsize=${s.vsize} rawsize=${s.rsize}`);

function fo(va) {
  const rva = va - imageBase;
  for (const s of secs) if (rva >= s.va && rva < s.va + Math.max(s.vsize, s.rsize)) return s.raw + (rva - s.va);
  return -1;
}
function cstr(off) {
  let e = off;
  while (e < b.length && b[e] !== 0) e++;
  return b.slice(off, e).toString("latin1");
}

for (const v of vas) {
  const va = parseInt(v.replace(/^0x/i, ""), 16);
  const off = fo(va);
  console.log(`\n=== VA 0x${va.toString(16)} -> file 0x${off.toString(16)} ===`);
  if (off < 0) { console.log("  fora de secoes"); continue; }
  const slice = b.slice(off, off + 96);
  console.log("  hex: " + slice.slice(0, 48).toString("hex").replace(/(..)/g, "$1 ").trim());
  // tentativas de interpretacao
  try { console.log("  qword[0]=0x" + slice.readBigUInt64LE(0).toString(16)); } catch (e) {}
  console.log("  ascii: " + slice.toString("latin1").replace(/[^\x20-\x7e]/g, "."));
  // se ponteiro para string dentro da imagem
  const p = Number(slice.readBigUInt64LE(0));
  if (p > imageBase && p < imageBase + 0x100000) {
    const po = fo(p);
    if (po >= 0) console.log("  -> ptr string: " + JSON.stringify(cstr(po)));
  }
}
