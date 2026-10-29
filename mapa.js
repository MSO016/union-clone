// Fase 3: mapa de funcionalidades - extrai classes/defs/docstrings dos .py decompilados.
const fs = require("fs");
const path = require("path");
const root = process.argv[2] || "D:/MSO/Projects/union-clone/decomp";

const files = [];
(function walk(d) {
  let e;
  try { e = fs.readdirSync(d, { withFileTypes: true }); } catch (x) { return; }
  for (const x of e) {
    const p = path.join(d, x.name);
    if (x.isDirectory()) walk(p);
    else if (x.name.endsWith(".py")) files.push(p);
  }
})(root);
files.sort();

const out = [];
for (const f of files) {
  const rel = path.relative(root, f).replace(/\\/g, "/");
  const lines = fs.readFileSync(f, "utf8").split(/\r?\n/);
  const classes = [];
  const funcs = [];
  const imports = new Set();
  let curClass = null;
  for (const ln of lines) {
    let m;
    if ((m = ln.match(/^import\s+(.+)$/)) || (m = ln.match(/^from\s+\S+\s+import\s+(.+)$/))) {
      for (const n of m[1].split(",")) {
        const name = n.trim().split(/\s+as\s+/)[0].trim();
        if (name) imports.add(name);
      }
    }
    if ((m = ln.match(/^class\s+(\w+)/))) {
      curClass = { name: m[1], methods: [], doc: null, bases: (ln.match(/^class\s+\w+\(([^)]*)\)/) || [,""])[1].trim() };
      classes.push(curClass);
      continue;
    }
    if ((m = ln.match(/^ {4}def\s+(\w+)\s*\(([^)]*)\)/))) {
      if (curClass) curClass.methods.push(m[1] + "(" + m[2].slice(0, 80) + ")");
      continue;
    }
    if ((m = ln.match(/^def\s+(\w+)\s*\(([^)]*)\)/))) {
      curClass = null;
      funcs.push(m[1] + "(" + m[2].slice(0, 90) + ")");
      continue;
    }
    if (curClass && curClass.doc === null && /^\s{8}'''/.test(ln) === false) {}
  }
  const totalMethods = classes.reduce((a, c) => a + c.methods.length, 0);
  out.push(`\n### ${rel}  [${lines.length} linhas] classes=${classes.length} metodos=${totalMethods} funcsLivres=${funcs.length}`);
  if (imports.size) out.push("  imports: " + [...imports].slice(0, 25).join(", "));
  for (const c of classes.slice(0, 12)) {
    out.push(`  class ${c.name}${c.bases ? "(" + c.bases + ")" : ""}  {${c.methods.length} métodos}`);
    for (const mm of c.methods.slice(0, 40)) out.push("      " + mm);
    if (c.methods.length > 40) out.push("      ... +" + (c.methods.length - 40));
  }
  if (classes.length > 12) out.push("  ... +" + (classes.length - 12) + " classes");
  for (const fn of funcs.slice(0, 30)) out.push("  fn " + fn);
}
console.log(out.join("\n"));
