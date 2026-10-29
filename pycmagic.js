// Agrupa .pyc pela magica (4 primeiros bytes) para achar quais estao ofuscados.
const fs = require("fs");
const path = require("path");
const root = process.argv[2];

const groups = {};
const files = [];
(function walk(d) {
  let e;
  try { e = fs.readdirSync(d, { withFileTypes: true }); } catch (x) { return; }
  for (const x of e) {
    const p = path.join(d, x.name);
    if (x.isDirectory()) walk(p);
    else if (x.name.endsWith(".pyc") || x.name.endsWith(".pyo")) files.push(p);
  }
})(root);

for (const f of files) {
  let fd, head;
  try {
    fd = fs.openSync(f, "r");
    head = Buffer.alloc(4);
    fs.readSync(fd, head, 0, 4, 0);
    fs.closeSync(fd);
  } catch (e) { continue; }
  const key = head.toString("hex") + "  [" + head.toString("latin1").replace(/[^\x20-\x7e]/g, ".") + "]";
  groups[key] = groups[key] || { n: 0, ex: [] };
  groups[key].n++;
  if (groups[key].ex.length < 8) groups[key].ex.push(path.relative(root, f));
}

console.log("total .pyc: " + files.length + "\n");
const sorted = Object.entries(groups).sort((a, b) => b[1].n - a[1].n);
for (const [k, v] of sorted) {
  console.log(`${k}  n=${v.n}`);
  for (const e of v.ex) console.log("     " + e);
  console.log("");
}
