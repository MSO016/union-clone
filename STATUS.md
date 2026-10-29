# STATUS — union-clone (handoff)
> Atualizado em 2026-10-28. **CRYPTO RESOLVIDO** — keystream fechado, 310 .pyc decifrados e decompilados.

## 1. Objetivo
Clean-room: analisar o instalador **union v1.3.4.5** (Inno Setup 7 / PyInstaller onedir, Python 3.13, PyQt5)
e construir app próprio equivalente. Prompt completo: `PROMPT.md` (7 fases).

## 2. Progresso por fase (estimativa ~92% do total)
| Fase | Estado |
|---|---|
| 1 TRIAGEM | ✅ 100% — extraído (6.490 arquivos), Inno 7.0.0.3 + PyInstaller onedir |
| 2 INVENTÁRIO | ✅ 100% — `inventario-*.txt`, `inno-list.txt`, `app-tree.txt` |
| 3 MAPA | ✅ 100% — `REPORT.md` (239 linhas, 9 capítulos); `mapa-funcionalidades.txt` (4.140 linhas); 310 .pyc decifrados+decompilados; schemas SQLite |
| 4 SPEC | ✅ 100% — `SPEC.md` (117 linhas): A1–A12/B1–B6, RFs, RN-1..RN-6, critérios de aceite |
| 5 ARQUITETURA | ✅ 100% — `ARCHITECTURE.md` (132 linhas): stack (Python+PyQt6+SQLite), camadas, pastas, modelo de dados, fluxos, plano de implementação |
| 6 IMPLEMENTAÇÃO | ✅ ~98% — 6 módulos na UI, PDF, ADB, backup, README/setup; só falta ajuste fino |
| 7 VERIFICAÇÃO | ✅ 100% — `CHECKLIST.md` (cruzamento RF×código, RN-1..RN-6 verificados, lista única de 24 pendências) |
| 7 VERIFICAÇÃO | ❌ 0% |

### Progresso da Fase 6 (IMPLEMENTAÇÃO)
- ✅ Ambiente: venv `.venv` com PyQt6 6.12 + PyMuPDF 2.0 (ambos com wheel p/ Python 3.14 — premissa de risco resolvida).
- ✅ Camada de domínio: `models.py` (9 modelos), 5 repositórios, migrações (`m0001_init` com 9 tabelas), `connection.py`.
- ✅ Serviços: `cliente_service`, `ordem_service` (ciclo de vida + auto-aprendizado + garantia), `relatorio_service` (diário/mensal).
- ✅ UI base: `main.py`, `i18n` (pt_br), `tema.py` (claro/escuro), `MainWindow` (sidebar + stack, monta as views reais quando recebe conexão).
- ✅ Views de negócio: `clientes_view` + `cliente_form`; `ordens_view` (dashboard de cards + tabela de abertas) + `ordem_form` + `encerramento_dialog` (regras RF-OS-4 na UI).
- ✅ Views restantes (módulos 3–6 na MainWindow): `conhecimento_view` (busca + filtro por tipo + form + detalhes), `relatorios_view` (diário com date picker + mensal com cards), `ferramentas_view` (ADB: dispositivos + bateria/identidade + PDF do laudo), `config_view` (abas Empresa/Perfil/Backup).
- ✅ PDF (`app/core/pdf/`): A4, térmico 80 mm, diagnóstico e relatório via PyMuPDF `insert_htmlbox` com escape de HTML; botões "PDF (A4)"/"PDF (80 mm)" na view de OS.
- ✅ Backup/restauração (`backup_service.py`): API `conn.backup`, validação do arquivo, preservação `.old-<timestamp>`; aba Backup na ConfigView.
- ✅ `main.py` corrigido: agora passa `conexao` e `caminho_banco` à MainWindow (antes caía no fallback sem módulos).
- ✅ Setup/README: `setup.ps1` (winget+pip, sem Scoop), `README.md` completo.
- ✅ Dispositivo: `gateway.py` (porta), `adb_gateway.py` (subprocess), `diag/bateria.py` (parser puro).
- ✅ Testes (6/6 OK): `test_dominio`, `test_services`, `test_diag`, `test_pdf`, `test_backup`, `test_ui` (offscreen, monta as 6 views reais com conexão). ~3.720 linhas.
- ✅ Fase 7: `CHECKLIST.md` na raiz do projeto — status de cada RF, verificação dos RN-1..RN-6 (buscas: zero rede em app/, zero bypass/DRM/partições) e lista única de pendências.

Entregável ainda NÃO escrito: `CHECKLIST.md`.

## 3. ✅ CRYPTO PYEN — RESOLVIDO (2026-10-28)
Formato: `[PYEN 4][NONCE 16][DATA N][TAG 16]` → plaintext = pyc completo (header 16 B + marshal 3.13).

### Fórmulas confirmadas (RE estático Ghidra + oráculo marshal 3.13, 930/930 pontos)
```
KEY   = sha256(_PYC_HALF_KEY + _PYC_BUILD_SALT)      # _pyc_derive_key()
A     = KEY + NONCE
ks0   = sha256(A).digest()                           # bloco 0 (pré-laço)
ks_i  = sha256(A + i.to_bytes(4, 'little')).digest() # i = 32, 64, 96, ... (offset byte)
out[i]= ct[i] ^ ks[i % 32]
```
Constantes: `_PYC_HALF_KEY`=`7a3f91c244b80ed5a16c28f355891de7`, `_PYC_BUILD_SALT`=`30072026cafebabedeadf00d12345678`,
`_KEY_CACHE`=`8001e0040b883590049043907198069863a012a034a074a832a853b003b031`.

### Evidência
- Bloco 0: plaintext conhecido `f30d0d0a00000000` + `0xe3` marshal.
- Bloco 1: oráculo de zeros do marshal 3.13 (`stacksize`/`flags` em offsets 30-36) → `block1_formula.py`
  testou 18 variantes × 310 arquivos: **`A+le32(i)` = 930/930** (próxima variant = 8/930).
- End-to-end: `decrypt_pyc.py` → **310/310 OK** (magic `f30d0d0a` + `0xe3`), 0 falhas.
- Oráculos textuais: `001_initial` → `CREATE TABLE ... company_settings`; `downloads_cache` → `class DownloadsCache`.

### Decriptografia/descompilação
- `decrypt_pyc.py` (src=`extracted\app\app`, dst=`decrypted\`) — 310 arquivos.
- `decompile-decrypted.ps1` → `decomp-decrypted\` — **ok=144, parcial=166, falhou=0**
  (parcial = pycdc avisa "incomplete Python 3.13", mas sai código útil).
- Anteriores: 197 módulos puros do PYZ em `decomp\` (build diferente do disco).

## 4. Mapa do `.pyd` (Ghidra) — referência
- Dump: `decomp\native\_security_crypto.c` (429 KB, 171 funções), script `ghidra-scripts\DumpAll.java`
- `decrypt_pyc` = FUN_180006080; core decrypt = FUN_180006260 (4056-5056)
- Loop decrypt: `range(len)` @4642, gate `i%32==0` @4706-4736, `sha256(A + i.to_bytes(4,'little'))` @4739-4855
  (tupla fixa `DAT_180016850` = `(4, 'little')` — `0x16c38`=4, idx 54='little'), XOR @4942, tag @4487.
- `DAT_180016c60`=32 (modulus), `DAT_180016a08`='hashlib', `DAT_180016b20`='sha256', `DAT_1800169b0`='digest', `DAT_180016b50`='to_bytes'.
- Strings: `cython-strings.txt`; tradutor `mapdats.py` (BASE 0x168b0).

## 5. Dados coletados na Fase 3 (base do SPEC)
- **Schemas SQLite**: `db-schemas.txt` (5 bancos):
  - `base.db`: `solucoes` (2.562 linhas, blobs de imagem/diagrama), `sync_control` (1.454)
  - `service_orders.db`: `users`, `clients`, `service_orders`, `knowledge_base` (+attachments),
    `company_settings` (warranty_text padrão PT-BR), `service_order_photos`, `service_orders_backup` — todos vazios
  - `user_solutions_1.db`: `user_solutions` (vazia)
  - `servidor_arquivos_cache.db`: `cache_servidor_arquivos` (305), `cache_marcas_resumo` (14), `cache_config` (4), `cache_sync_control`
  - `app.db` (ordem_servico/instance): sem tabelas (Flask/Alembic, `alembic.ini` presente)
- **Config**: `database\.key` = chave base64 32 B; `ordem_servico\.env` = Flask dev
  (SECRET_KEY, DATABASE_URL sqlite, COMPANY_NAME=RestoreCell, SYSTEM_NAME="Union OS Manager");
  SSL self-signed `ssl\cert.pem`/`key.pem` (CN=localhost, BR/SP, RestoreCell).
- **`termos_de_uso.txt`**: licença PT-BR "TECH UNION SOLUTIONS" v1.3.4.2, Tech Union Solutions / RestoreCell.
- **`translations\pt.py`** (23 KB): dict `translations` com ~centenas de chaves de UI (PT-BR).
- **`premium_services_manager.py`**: cliente MySQL (`pymysql`) p/ tabela `conteudos_dinamicos` (serviços premium), cache 300 s.
- **`.env`/`.key` no root do app: NÃO existem** (só nos subprojetos acima) — verificado.

## 6. Arquivos de trabalho
- Crypto: `block1_oracle.py`, `block1_formula.py` (**fechou o keystream**), `decrypt_pyc.py`, `decrypt_test.py`,
  `brute3.py`, `ks_*.py`, `discriminate.py`
- Descompilação: `decrypt_pyc.py`, `decompile-decrypted.ps1` → `decomp-decrypted\` (310 .py)
- Fase 3: `dump_db.py` → `db-schemas.txt`; `mapa.js` → `mapa-funcionalidades.txt`
- Ghidra: `ghidra-scripts\DumpAll.java`, `mapdats.py`, `parse_strings.py`, `cython-strings.txt`

## 7. Próximos passos (ordem)
1. Consolidar Fase 3 → escrever `REPORT.md` (o que o app faz, módulo a módulo).
2. Fase 4: escrever `SPEC.md` (requisitos funcionais/não-funcionais do clone).
3. Fase 5: ARQUITETURA (escolher stack — sugestão: Python 3.13 + PyQt5 p/ fidelidade).
4. Fase 6: IMPLEMENTAÇÃO do app (clean-room, sem código decompilado).
5. Fase 7: `CHECKLIST.md` + verificação.
6. Ao final: listar todas as pendências de uma vez (regra do PROMPT).

## 8. Pendências conhecidas
- `pycdc-new` marca 166/310 como "incomplete" (limitação da ferramenta p/ 3.13) — código sai utilizável, mas
  conferir trechos críticos quando forem base do SPEC.
- REA MCP inoperante p/ `.pyd`; Ghidra headless é o substituto. `websearch` fora do ar.
- Análise dinâmica do `.pyd` NÃO foi necessária (crypto resolvida por estática).

## 9. Regras do usuário (nunca violar)
- Clean-room: não colar código decompilado no projeto final.
- NÃO implementar bypass de licença/DRM/anti-cheat (só documentar).
- NUNCA executar o `.exe` do alvo fora de sandbox; avisar antes de análise dinâmica (sugerir VM).
- Nunca modificar originais (`D:\MSO\Downloads\...`); trabalhar em `D:\MSO\Projects\union-clone\`.
- Autonomia: usuário define o QUÊ, eu o COMO; pendências em lista única ao final.
