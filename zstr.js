// Localiza e descomprime o blob zlib embutido no .pyd (string table do Cython).
const fs = require("fs");
const zlib = require("zlib");
const b = fs.readFileSync(process.argv[2]);

const found = [];
for (let i = 0; i < b.length - 2; i++) {
  const c = b[i];
  if (c !== 0x78) continue;
  const cmf = c, flg = b[i + 1];
  if ((cmf * 256 + flg) % 31 !== 0) continue;
  if ((flg & 0x20) !== 0) continue; // FDICT
  found.push(i);
}
console.log("candidatos zlib: " + found.length + " -> " + found.slice(0, 20).map(x => "0x" + x.toString(16)).join(", "));

let best = null;
for (const off of found) {
  try {
    const out = zlib.inflateSync(b.slice(off));
    if (!best || out.length > best.out.length) best = { off, out };
    console.log(`  OK em 0x${off.toString(16)}: ${out.length} bytes`);
  } catch (e) { /* nao e stream valido */ }
}

if (best) {
  console.log(`\nMELHOR: offset 0x${best.off.toString(16)} -> ${best.out.length} bytes`);
  fs.writeFileSync(process.argv[3] || "cython-strings.bin", best.out);
  const s = best.out.toString("latin1");
  // imprime tokens legíveis
  const toks = s.split(/[^\x20-\x7e]+/).filter(t => t.length >= 3);
  console.log("tokens: " + toks.length);
  console.log(toks.join("\n"));
}
