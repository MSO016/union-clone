// Varredura de magic/compressao no Inno payload e estrutura do loader.
const fs = require("fs");
const file = process.argv[2];
const b = fs.readFileSync(file);
console.log("size: " + b.length.toLocaleString("en-US"));

const hits = {};
function find(needle, label, max) {
  const n = Buffer.from(needle, "latin1");
  const out = [];
  let i = b.indexOf(n, 0);
  while (i !== -1 && out.length < (max || 12)) { out.push(i); i = b.indexOf(n, i + 1); }
  if (out.length) hits[label] = out;
}

// Inno compression IDs
find("zlb\x1a", "inno-zlib(zlb 1A)");
find("lzma\x1a", "inno-lzma(lzma 1A)");   // 'lzma' + 0x1A
find("bzip\x1a", "inno-bzip2");
find("unc0", "inno-uncompressed");
// generic compressors
find("\x1a\x6c\x62\x7a", "inno-zlib(rev)");
find("\x28\xb5\x2f\xfd", "zstd");
find("\xfd\x37\x7a\x58\x5a\x00", "xz");
find("\x1f\x8b\x08", "gzip");
find("\x04\x22\x4d\x18", "lz4");
find("PK\x03\x04", "zip-localhdr");
find("PK\x05\x06", "zip-eocd");
find("7z\xbc\xaf\x27\x1c", "7z");
find("Rar!\x1a\x07", "rar");
find("\x5d\x00\x00\x00", "lzma-alone-marker(5d000000)");
find("Inno Setup", "Inno Setup text");
find("Inno", "Inno text");

for (const [k, v] of Object.entries(hits)) {
  console.log(`\n${k}  (${v.length}+ mostrados):`);
  console.log("   " + v.map((x) => "0x" + x.toString(16)).join("  "));
}

// dump the first 512 bytes of the overlay (Inno setup loader header region)
const ov = 0x165600;
console.log("\n--- overlay head @0x" + ov.toString(16) + " ---");
const head = b.slice(ov, ov + 256);
for (let i = 0; i < head.length; i += 16) {
  const row = head.slice(i, i + 16);
  console.log(
    (ov + i).toString(16).padStart(8, "0") + "  " +
    row.map((x) => x.toString(16).padStart(2, "0")).join(" ") + "  " +
    row.toString("latin1").replace(/[^\x20-\x7e]/g, ".")
  );
}

// strings (ASCII >= 6) in the first 64KB of overlay
let s = "", out = [];
for (let i = ov; i < Math.min(ov + 65536, b.length); i++) {
  const c = b[i];
  if (c >= 0x20 && c < 0x7f) s += String.fromCharCode(c);
  else { if (s.length >= 6) out.push(s); s = ""; }
}
console.log("\n--- strings nas primeiras 64KB do overlay (" + out.length + ") ---");
console.log(out.slice(0, 60).join("\n"));

// strings do .rsrc (icones/textos de UI do instalador)
console.log("\n--- ALL interesting strings do PE inteiro (scan limitado 12MB) ---");
const lim = Math.min(b.length, 12 * 1024 * 1024);
s = ""; out = [];
const pat = /(https?:\/\/|www\.|[A-Za-z]:\\|\.dll|\.exe|\.json|\.db|\.sqlite|union|Union|UNION)/;
for (let i = 0; i < lim; i++) {
  const c = b[i];
  if (c >= 0x20 && c < 0x7f) s += String.fromCharCode(c);
  else { if (s.length >= 8 && pat.test(s)) out.push(s); s = ""; }
}
console.log(out.slice(0, 80).join("\n"));
