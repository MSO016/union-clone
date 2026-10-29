import sqlite3, os, sys

dbs = [
    r"D:\MSO\Projects\union-clone\extracted\app\app\database\base.db",
    r"D:\MSO\Projects\union-clone\extracted\app\app\database\service_orders.db",
    r"D:\MSO\Projects\union-clone\extracted\app\app\data\user_solutions_1.db",
    r"D:\MSO\Projects\union-clone\extracted\app\app\views\ordem_servico\instance\app.db",
    r"D:\MSO\Projects\union-clone\extracted\app\app\views\ordem_servico\app\database\servidor_arquivos_cache.db",
]

out = open(r"D:\MSO\Projects\union-clone\db-schemas.txt", "w", encoding="utf-8")
for d in dbs:
    out.write("=" * 20 + " " + os.path.basename(d) + " " + "=" * 20 + "\n")
    try:
        con = sqlite3.connect("file:" + d.replace("\\", "/") + "?mode=ro", uri=True)
        rows = con.execute(
            "SELECT type, name, sql FROM sqlite_master ORDER BY type, name"
        ).fetchall()
        for t, n, sql in rows:
            if sql:
                out.write(sql.rstrip().rstrip(";") + ";\n")
        # contagens por tabela (tamaho util para o SPEC)
        for t, n, sql in rows:
            if t == "table" and not n.startswith("sqlite_"):
                try:
                    c = con.execute(f'SELECT COUNT(*) FROM "{n}"').fetchone()[0]
                    out.write(f"-- rows: {n} = {c}\n")
                except Exception:
                    pass
        con.close()
    except Exception as e:
        out.write(f"ERRO: {e}\n")
    out.write("\n")
out.close()
print("ok")
