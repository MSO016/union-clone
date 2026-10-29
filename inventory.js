// Inventario: arvore do app, contagem por extensao, strings de rede/caminho em fontes.
const fs = require("fs");
const path = require("path");

const root = process.argv[2];
if (!root) { console.log("uso: node inventory.js <dir>"); process.exit(1); }

const stats = { dirs: 0, files: 0, bytes: 0, byExt: {} };
const tree = new Map(); // dir -> {files, bytes, exts}

function walk(dir, depth) {
  let entries;
  try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch (e) { return; }
  stats.dirs++;
  const t = tree.get(dir) || { files: 0, bytes: 0, exts: {} };
  for (const e of entries) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) {
      walk(p, depth + 1);
    } else {
      let sz = 0;
      try { sz = fs.statSync(p).size; } catch (x) {}
      stats.files++; stats.bytes += sz;
      const ext = path.extname(e.name).toLowerCase() || "(sem)";
      stats.byExt[ext] = stats.byExt[ext] || { n: 0, b: 0 };
      stats.byExt[ext].n++; stats.byExt[ext].b += sz;
      t.files++; t.bytes += sz;
      t.exts[ext] = (t.exts[ext] || 0) + 1;
      tree.set(dir, t);
    }
  }
}

console.log("root: " + root);
walk(root, 0);
console.log(`dirs=${stats.dirs}  files=${stats.files}  bytes=${stats.bytes.toLocaleString("en-US")}`);

console.log("\n--- EXTENSOES (top 40 por bytes) ---");
const exts = Object.entries(stats.byExt).sort((a, b) => b[1].b - a[1].b);
for (const [k, v] of exts.slice(0, 40)) {
  console.log(`  ${k.padEnd(14)} n=${String(v.n).padStart(5)}  ${(v.b / 1048576).toFixed(1).padStart(8)} MB`);
}

console.log("\n--- ARVORE (diretorios com >0 arquivos, ate 4 niveis) ---");
function printTree(dir, prefix, level) {
  let entries;
  try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch (e) { return; }
  const dirs = entries.filter((e) => e.isDirectory()).map((e) => e.name).sort();
  const t = tree.get(dir) || { files: 0, bytes: 0 };
  for (let i = 0; i < dirs.length; i++) {
    const d = dirs[i];
    const last = i === dirs.length - 1;
    const sub = path.join(dir, d);
    const st = tree.get(sub) || { files: 0, bytes: 0 };
    console.log(`${prefix}${last ? "\u2514" : "\u251c"}\u2500\u2500 ${d}/  (${st.files} arq, ${(st.bytes / 1024).toFixed(0)} KB)`);
    if (level < 3) printTree(sub, prefix + (last ? "    " : "\u2502   "), level + 1);
  }
}
printTree(root, "", 0);
