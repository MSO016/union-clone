// Strings de um binario (min length, filtro).
const fs = require("fs");
const file = process.argv[2];
const min = parseInt(process.argv[3] || "5", 10);
const filt = process.argv[4] ? new RegExp(process.argv[4], "i") : null;
const b = fs.readFileSync(file);
let s = "";
const out = [];
for (const c of b) {
  if (c >= 0x20 && c < 0x7f) s += String.fromCharCode(c);
  else { if (s.length >= min && (!filt || filt.test(s))) out.push(s); s = ""; }
}
if (s.length >= min && (!filt || filt.test(s))) out.push(s);
console.log("strings: " + out.length);
console.log(out.join("\n"));
