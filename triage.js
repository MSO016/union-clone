// Triagem estatica de PE: header, secoes, imports, overlay, magics de tecnologia.
const fs = require("fs");
const path = require("path");

const file = process.argv[2];
const b = fs.readFileSync(file);
console.log("file: " + path.basename(file));
console.log("size: " + b.length.toLocaleString("en-US"));

if (b.readUInt16LE(0) !== 0x5a4d) { console.log("NOT MZ"); process.exit(1); }
const peOff = b.readUInt32LE(0x3c);
if (b.readUInt32LE(peOff) !== 0x4550) { console.log("NOT PE"); process.exit(1); }

const coff = peOff + 4;
const nSec = b.readUInt16LE(coff + 2);
const timedate = b.readUInt32LE(coff + 4);
const optSize = b.readUInt16LE(coff + 16);
const chars = b.readUInt16LE(coff + 18);
const opt = coff + 20;
const magic = b.readUInt16LE(opt);
const is64 = magic === 0x20b;

console.log("\n--- COFF/OPTIONAL ---");
console.log("machine: 0x" + b.readUInt16LE(coff).toString(16) + " (" + (b.readUInt16LE(coff) === 0x8664 ? "x64" : b.readUInt16LE(coff) === 0x14c ? "x86" : "?") + ")");
console.log("sections: " + nSec);
console.log("timestamp: " + new Date(timedate * 1000).toISOString() + "  (0x" + timedate.toString(16) + ")");
console.log("linker: " + b[opt + 2] + "." + b[opt + 3]);
console.log("imageBase: 0x" + (is64 ? b.readBigUInt64LE(opt + 24).toString(16) : b.readUInt32LE(opt + 28).toString(16)));
console.log("entryRVA: 0x" + b.readUInt32LE(opt + 16).toString(16));
console.log("subsystem: " + b.readUInt16LE(opt + 68) + (b.readUInt16LE(opt + 68) === 2 ? " (GUI)" : b.readUInt16LE(opt + 68) === 3 ? " (CUI)" : ""));
console.log("dllChars: 0x" + b.readUInt16LE(opt + 70).toString(16));
console.log("checksum: 0x" + b.readUInt32LE(opt + 64).toString(16));
const ddOff = opt + (is64 ? 112 : 96);
const numDD = b.readUInt32LE(opt + (is64 ? 108 : 92));

const secOff = opt + optSize;
const secs = [];
for (let i = 0; i < nSec; i++) {
  const o = secOff + i * 40;
  secs.push({
    name: b.slice(o, o + 8).toString("latin1").replace(/\0.*$/, ""),
    vsize: b.readUInt32LE(o + 8),
    va: b.readUInt32LE(o + 12),
    rawsize: b.readUInt32LE(o + 16),
    rawptr: b.readUInt32LE(o + 20),
    chars: b.readUInt32LE(o + 36),
  });
}
console.log("\n--- SECOES ---");
let lastEnd = 0;
for (const s of secs) {
  const end = s.rawptr + s.rawsize;
  if (end > lastEnd) lastEnd = end;
  console.log(
    `  ${JSON.stringify(s.name).padEnd(14)} va=0x${s.va.toString(16).padStart(6)} v=${String(s.vsize).padStart(9)} raw=${String(s.rawsize).padStart(9)} off=0x${s.rawptr.toString(16).padStart(7)} chars=0x${s.chars.toString(16)}`
  );
}
console.log("\n--- OVERLAY (dados apos ultima secao) ---");
const overlaySize = b.length - lastEnd;
console.log("fim da ultima secao: 0x" + lastEnd.toString(16) + "  overlay = " + overlaySize.toLocaleString("en-US") + " bytes (" + ((overlaySize / b.length) * 100).toFixed(1) + "% do arquivo)");
if (overlaySize > 0 && overlaySize < 4096) {
  const d = b.slice(lastEnd, lastEnd + 256);
  console.log("overlay hex: " + d.slice(0, 128).toString("hex"));
  console.log("overlay ascii: " + d.toString("latin1").replace(/[^\x20-\x7e]/g, "."));
}

// ---- imports
const rva2off = (rva) => {
  for (const s of secs) if (rva >= s.va && rva < s.va + Math.max(s.vsize, s.rawsize)) return s.rawptr + (rva - s.va);
  return null;
};
const strAt = (off, max = 1024) => {
  if (off == null || off < 0 || off >= b.length) return null;
  const e = b.indexOf(0, off);
  return b.slice(off, e === -1 || e - off > max ? off + max : e).toString("latin1");
};

console.log("\n--- IMPORTS (DLLs) ---");
const dd = (i) => (numDD > i ? [b.readUInt32LE(ddOff + i * 8), b.readUInt32LE(ddOff + i * 8 + 4)] : [0, 0]);
const [iRva] = dd(1);
const allImp = {};
if (iRva) {
  const io = rva2off(iRva);
  if (io != null) {
    for (let i = 0; i < 800; i++) {
      const o = io + i * 20;
      const nameRva = b.readUInt32LE(o + 12);
      if (!nameRva) break;
      const dll = strAt(rva2off(nameRva));
      if (!dll) break;
      let thunkRva = b.readUInt32LE(o + 0);
      const iatRva = b.readUInt32LE(o + 16);
      let viaIat = false;
      if (!thunkRva) { thunkRva = iatRva; viaIat = true; }
      const to = rva2off(thunkRva);
      const names = [];
      if (to != null) {
        for (let j = 0; j < 5000; j++) {
          const t = is64 ? BigInt.asUintN(64, b.readBigUInt64LE(to + j * 8)) : BigInt(b.readUInt32LE(to + j * 4));
          if (t === 0n) break;
          const ordFlag = is64 ? 0x8000000000000000n : 0x80000000n;
          if ((t & ordFlag) !== 0n) { names.push("#" + Number(t & 0xffffn)); continue; }
          let r = Number(t & 0x7fffffffn);
          if (viaIat && r >= 0x40000000) r -= 0x40000000;
          names.push(strAt(rva2off(r) + 2) || "?");
        }
      }
      allImp[dll] = names;
    }
  }
}
for (const [dll, names] of Object.entries(allImp)) console.log(`  ${dll} (${names.length})`);

// ---- exports
console.log("\n--- EXPORTS ---");
const [eRva] = dd(0);
if (eRva) {
  const eo = rva2off(eRva);
  if (eo != null) {
    const nNames = b.readUInt32LE(eo + 24);
    const no = rva2off(b.readUInt32LE(eo + 32));
    const dllName = strAt(rva2off(b.readUInt32LE(eo + 12)));
    console.log("  dllname: " + dllName + "  count=" + nNames);
    if (no != null) for (let i = 0; i < Math.min(nNames, 40); i++) console.log("    " + strAt(rva2off(b.readUInt32LE(no + i * 4))));
  }
} else console.log("  (nenhum)");

// ---- data directories resumo
const ddNames = ["export", "import", "resource", "exception", "security", "basereloc", "debug", "arch", "globalptr", "tls", "loadcfg", "boundimport", "iat", "delayimport", "comdesc", "reserved"];
console.log("\n--- DATA DIRECTORIES ---");
for (let i = 0; i < Math.min(numDD, 16); i++) {
  const r = b.readUInt32LE(ddOff + i * 8), s = b.readUInt32LE(ddOff + i * 8 + 4);
  if (r || s) console.log(`  ${ddNames[i].padEnd(14)} rva=0x${r.toString(16).padStart(8)} size=${s.toLocaleString("en-US")}`);
}

// ---- magics de tecnologia no arquivo inteiro (janela limitada p/ performance)
console.log("\n--- TECH MAGICS (scan) ---");
const needles = [
  ["PyInstaller", "PyInstaller\x00"],
  ["MEI temp", "MEI"],
  ["PyInit_", "PyInit_"],
  ["python dll", "python3"],
  ["Electron", "electron"],
  ["Chromium", "Chrome_"],
  ["Node.js", "node.dll"],
  [".NET mscorlib", "mscorlib"],
  [".NET Core", "hostfxr"],
  ["CoreCLR", "coreclr"],
  ["NSIS", "Nullsoft"],
  ["Inno Setup", "Inno Setup"],
  ["7z SFX", "7z\xBC\xAF\x27\x1C"],
  ["WinRAR SFX", "WinRAR"],
  ["Install4j", "install4j"],
  ["Java/JAR", "PK\x03\x04"],
  ["Rust/cargo", ".cargo"],
  ["Go buildinfo", "Go buildinf"],
  ["Delphi", "Borland"],
  ["Qt", "QtCore"],
  ["MFC", "AFX"],
  ["AutoIt", "AU3!"],
  ["AutoHotkey", "AutoHotkey"],
  ["Lua bundled", "LuaJIT"],
  ["UPX", "UPX!"],
  ["VMProtect", "VMProtect"],
  ["Themida", ".themida"],
  ["Enigma", "Enigma"],
  ["Py2Exe", "py2exe"],
  ["Tesseract PyOxidizer", "pyoxidizer"],
];
const hay = b; // buffer scan
for (const [label, nd] of needles) {
  const needle = Buffer.from(nd, "latin1");
  const idx = hay.indexOf(needle);
  if (idx >= 0) console.log(`  HIT ${label.padEnd(24)} @ 0x${idx.toString(16)} (${idx.toLocaleString("en-US")})`);
}
