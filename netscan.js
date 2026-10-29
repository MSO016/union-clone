// Scan de endpoints/caminhos/credenciais em arquivos de texto-ish de um dir.
const fs = require("fs");
const path = require("path");

const root = process.argv[2];
const out = [];
const seen = new Set();

const URL = /https?:\/\/[^\s"'<>\\)\]},;]+/gi;
const WSS = /wss?:\/\/[^\s"'<>\\)\]},;]+/gi;
const IP = /\b(?:\d{1,3}\.){3}\d{1,3}(?::\d{1,5})?\b/g;
const HOST = /\b[a-z0-9][a-z0-9-]{1,61}\.[a-z]{2,18}\b(?=[/"'\s:@]|$)/gi;
const REG = /HKEY_[A-Z_]+\\[^\s"'<>]+|HK(?:CU|LM|CR)\\[^\s"'<>]+/g;
const WINPATH = /[A-Za-z]:\\(?:[^\\\/\s"'<>|*?]{1,60}\\)*[^\\\/\s"'<>|*?]{1,60}/g;
const SECRET = /(?:api[_-]?key|token|secret|password|passwd|passwd_hash|license[_-]?key|auth[_-]?token|private[_-]?key|aws[_-]?access)/i;

const CODE_ONLY = process.argv[5] === "code";
const TEXT_EXT = CODE_ONLY
  ? new Set([".py", ".pyc", ".pyd"])
  : new Set([".py", ".pyc", ".pyd", ".json", ".txt", ".env", ".ini", ".cfg", ".sql", ".mako", ".html", ".htm", ".js", ".bat", ".ps1", ".state", ".key", ".flaskenv", ".manifest", ".xml", ".yaml", ".yml", ".csv", ".log", ".gitignore", ".ssl_enabled"]);
const EXCLUDE = /(test\.json|blacklist_union_apps_v2|requirements\.txt)/i;

const files = [];
(function walk(d) {
  let e;
  try { e = fs.readdirSync(d, { withFileTypes: true }); } catch (x) { return; }
  for (const x of e) {
    const p = path.join(d, x.name);
    if (x.isDirectory()) walk(p);
    else {
      let sz = 0;
      try { sz = fs.statSync(p).size; } catch (y) {}
      if (sz > 0 && sz < 6 * 1024 * 1024) files.push([p, sz]);
    }
  }
})(root);

const cats = { url: [], wss: [], ip: [], reg: [], host: [], secret: [], winpath: [] };

function add(cat, val, file) {
  const key = cat + "|" + val.toLowerCase();
  if (seen.has(key)) return;
  seen.add(key);
  cats[cat].push(`${val}   << ${path.relative(root, file)}`);
}

for (const [f] of files) {
  const ext = path.extname(f).toLowerCase();
  if (!TEXT_EXT.has(ext) && ext !== "") continue;
  if (EXCLUDE.test(f)) continue;
  let buf;
  try { buf = fs.readFileSync(f); } catch (e) { continue; }
  // pula binarios reais
  const sample = buf.slice(0, 2000);
  let ctrl = 0;
  for (const b of sample) if (b === 0) ctrl++;
  if (ctrl > sample.length * 0.15) continue;
  const s = buf.toString("latin1");

  for (const m of s.matchAll(URL)) add("url", m[0].replace(/[.,'"`]+$/, ""), f);
  for (const m of s.matchAll(WSS)) add("wss", m[0].replace(/[.,'"`]+$/, ""), f);
  for (const m of s.matchAll(REG)) add("reg", m[0], f);
  if (ext === ".py" || ext === ".pyc" || ext === ".txt" || ext === ".env" || ext === ".ini" || ext === ".json" || ext === ".cfg") {
    for (const m of s.matchAll(IP)) add("ip", m[0], f);
    for (const m of s.matchAll(HOST)) {
      const h = m[0];
      if (/\b(localhost|python\.org|github\.com|pypi\.org|w3\.org|googleapis\.com|qt\.io|example\.com)$/i.test(h)) continue;
      add("host", h, f);
    }
    for (const m of s.matchAll(WINPATH)) {
      const p = m[0];
      if (p.startsWith("C:\\Windows\\System32") || p.length < 6) continue;
      add("winpath", p, f);
    }
  }
  if (SECRET.test(s)) {
    // marca arquivo com possivel segredo (nao imprime valor)
    add("secret", "[arquivo contem keyword de segredo: " + path.relative(root, f) + "]", f);
  }
}

for (const k of ["url", "wss", "ip", "host", "reg", "secret", "winpath"]) {
  out.push(`\n===== ${k.toUpperCase()} (${cats[k].length}) =====`);
  const list = cats[k].slice(0, k === "winpath" ? 60 : 120);
  out.push(list.join("\n"));
  if (cats[k].length > list.length) out.push(`... +${cats[k].length - list.length}`);
}
console.log(out.join("\n"));
