# Union Manager

App desktop offline de gestão de oficina/bancada de reparos: clientes, ordens de
serviço, base de conhecimento de soluções, relatórios e ferramentas de
diagnóstico via ADB. Uso pessoal, 100% local (SQLite) — sem contas, sem nuvem,
sem licenças.

Projeto construído por engenharia reversa **clean-room** do instalador
"union v1.3.4.5": apenas a especificação funcional foi extraída
(`../REPORT.md` e `../SPEC.md`); nenhum código do alvo foi copiado.

## Requisitos

- Windows 10/11
- Python 3.11+ (testado em 3.14)
- Opcional: `adb` (Android platform-tools) no PATH para o módulo de ferramentas

## Instalação

Na pasta do projeto:

```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
```

O script usa **winget** (para instalar o Python, se faltar) e **pip** (para as
dependências). Ele cria o ambiente virtual `.venv` automaticamente.

Instalação manual, se preferir:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Execução

```powershell
.\.venv\Scripts\python.exe main.py
```

Opções:

- `--tema escuro|claro` — tema da interface (padrão: escuro)
- `--dados CAMINHO` — diretório de dados (padrão: `%LOCALAPPDATA%\UnionManager\data`)

O banco `union.db` é criado no diretório de dados, com migrações aplicadas
automaticamente na primeira execução.

## Módulos

| Módulo | O que faz |
|---|---|
| Clientes | Cadastro com busca incremental; exclusão bloqueada se houver OS vinculadas |
| Ordens de Serviço | Dashboard com cards de status, nova OS, encerramento com regras (sucesso exige solução; sem solução exige motivo), reabertura por garantia, exportação PDF (A4 e bobina 80 mm) |
| Base de Conhecimento | Soluções por marca/modelo/problema; soluções de OS encerradas com sucesso entram automaticamente (auto-aprendizado) |
| Relatórios | Resumo diário e mensal (contagens, taxa de sucesso, faturamento) |
| Ferramentas (ADB) | Lista aparelhos, diagnóstico de bateria e identidade via `adb shell`, exportação do laudo em PDF |
| Configurações | Dados da empresa (usados nos PDFs), perfil e **backup/restauração** do banco |

## Testes

Todos os testes rodam offline (a UI usa a plataforma `offscreen`):

```powershell
$py = ".\.venv\Scripts\python.exe"
$py -m tests.test_dominio    # modelos e regras de domínio
$py -m tests.test_services   # serviços (clientes, ordens, auto-aprendizado)
$py -m tests.test_diag       # parsers de diagnóstico (fixtures)
$py -m tests.test_pdf        # geração dos 4 formatos de PDF
$py -m tests.test_backup     # backup/restauração
$py -m tests.test_ui         # montagem da MainWindow (6 módulos)
```

## Backup

Em **Configurações → Backup**: gere um snapshot consistente do banco (`.db`)
ou restaure um backup anterior. Na restauração, o banco atual é preservado
como `.old-<data>` antes da substituição.

## Estrutura

```
union-manager/
├── main.py                  # entrada: QApplication, tema, instância única, migrações
├── setup.ps1                # setup via winget + pip
├── app/
│   ├── core/                # sem Qt: regras de negócio e persistência
│   │   ├── db/              # conexão (WAL), migrações, repositórios
│   │   ├── models/          # dataclasses de domínio
│   │   ├── services/        # clientes, ordens, relatórios, backup
│   │   ├── pdf/             # A4, térmico 80 mm, diagnóstico, relatórios
│   │   ├── device/          # porta DeviceGateway + implementação ADB
│   │   └── diag/            # parsers puros (bateria) + fixtures
│   └── ui/                  # PyQt6: MainWindow, i18n, tema, views por módulo
└── tests/                   # testes offline (exit 0 = verde)
```

## Limites deliberados

- 100% local: sem sincronização, contas, premium, download de firmware ou
  qualquer serviço remoto (requisitos negativos do SPEC).
- Não há bypass de licença/DRM/anti-cheat — o app é original e independente.
- O módulo ADB requer os platform-tools oficiais do Android instalados pelo
  usuário; o app apenas os invoca.
