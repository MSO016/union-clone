// Verifica ZIP embutido + strings em offsets especificos.
const fs = require("fs");
const file = process.argv[2];
const fd = fs.openSync(file, "r");

function rd(off, len) {
  const buf = Buffer.alloc(len);
  const n = fs.readSync(fd, buf, 0, len, off);
  return buf.slice(0, n);
}

function strings(buf, min) {
  const out = [];
  let s = "";
  for (const c of buf) {
    if (c >= 0x20 && c < 0x7f) s += String.fromCharCode(c);
    else { if (s.length >= min) out.push(s); s = ""; }
  }
  if (s.length >= min) out.push(s);
  return out;
}

console.log("=== A) strings em 0x11a100 (regiao .data do stub, 1KB) ===");
console.log(strings(rd(0x11a100, 0x400), 5).join("\n"));

console.log("\n=== B) strings em 0x164c000..0x1656000 (fim .rsrc = VERSIONINFO do stub) ===");
console.log(strings(rd(0x164c000, 0x1656000 - 0x164c000), 4).slice(0, 120).join("\n"));

console.log("\n=== C) EOCD suspect @0x62c5c90 ===");
const e = rd(0x62c5c90, 22);
console.log("hex:   " + e.slice(0, 22).toString("hex"));
console.log("ascii: " + e.toString("latin1").replace(/[^\x20-\x7e]/g, "."));
if (e.readUInt32LE(0) === 0x06054b50) {
  const nEntries = e.readUInt16LE(8);
  const cdSize = e.readUInt32LE(12);
  const cdOffset = e.readUInt32LE(16);
  console.log(`EOCD VALIDO: nEntries=${nEntries} cdSize=${cdSize} cdOffset=${cdOffset} (0x${cdOffset.toString(16)})`);
  const zipStart = 0x62c5c90 - cdOffset - cdSize;
  console.log("=> ZIP comecaria em 0x" + zipStart.toString(16) + "  (tamanho ~" + ((0x62c5c90 + 22 - zipStart) / 1048576).toFixed(1) + " MB)");
} else {
  console.log("NAO e EOCD valido (falso positivo), sig=" + e.readUInt32LE(0).toString(16));
}

console.log("\n=== D) scan de assinaturas ZIP no arquivo inteiro ===");
const size = fs.fstatSync(fd).size;
const CHUNK = 8 * 1024 * 1024;
const counts = { local: 0, cd: 0, eocd: 0 };
const eocdList = [];
const localList = [];
const cdList = [];
let prevTail = Buffer.alloc(0);
for (let off = 0; off < size; off += CHUNK) {
  const buf = rd(off, CHUNK);
  const scan = prevTail.length ? Buffer.concat([prevTail, buf]) : buf;
  const base = off - prevTail.length;
  let i;
  for (const [sig, key, list] of [
    [Buffer.from("PK\x03\x04"), "local", localList],
    [Buffer.from("PK\x01\x02"), "cd", cdList],
    [Buffer.from("PK\x05\x06"), "eocd", eocdList],
  ]) {
    i = scan.indexOf(sig);
    while (i !== -1) {
      counts[key]++;
      if (list.length < 25) list.push(base + i);
      i = scan.indexOf(sig, i + 1);
    }
  }
  prevTail = buf.slice(buf.length - 3);
}
console.log("counts: " + JSON.stringify(counts));
console.log("local hdrs: " + localList.map((x) => "0x" + x.toString(16)).join(" "));
console.log("central dirs: " + cdList.map((x) => "0x" + x.toString(16)).join(" "));
console.log("eocd: " + eocdList.map((x) => "0x" + x.toString(16)).join(" "));

fs.closeSync(fd);
