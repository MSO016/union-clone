// Lista a arvore relativa de um dir e (opcional) conteudo dos .py
const fs = require("fs");
const path = require("path");

const root = process.argv[2];
const mode = process.argv[3] || "tree"; // tree | py

const files = [];
(function walk(d) {
  let e;
  try { e = fs.readdirSync(d, { withFileTypes: true }); } catch (x) { return; }
  for (const x of e) {
    const p = path.join(d, x.name);
    if (x.isDirectory()) walk(p);
    else files.push(path.relative(root, p));
  }
})(root);

files.sort();

if (mode === "tree") {
  const groups = {};
  for (const f of files) {
    const top = f.split(path.sep).slice(0, 2).join(path.sep);
    groups[top] = groups[top] || [];
    groups[top].push(f);
  }
  for (const [g, list] of Object.entries(groups)) {
    console.log(`\n### ${g}  (${list.length} arq)`);
    if (list.length <= 60) console.log(list.join("\n"));
    else console.log(list.slice(0, 60).join("\n") + `\n... +${list.length - 60}`);
  }
  console.log("\nTOTAL: " + files.length);
} else if (mode === "py") {
  const pat = process.argv[4] ? new RegExp(process.argv[4], "i") : null;
  const pys = files.filter((f) => f.endsWith(".py") && (!pat || pat.test(f)));
  for (const f of pys) {
    const c = fs.readFileSync(path.join(root, f), "utf8");
    console.log("\n" + "=".repeat(70));
    console.log("### " + f + "  (" + c.length + " chars)");
    console.log("=".repeat(70));
    console.log(c.length > 40000 ? c.slice(0, 40000) + "\n...[truncado]" : c);
  }
}
