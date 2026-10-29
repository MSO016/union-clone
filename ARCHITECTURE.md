# ARCHITECTURE — Union Manager (clone clean-room)
> Fase 5 do fluxo. Define stack, camadas, estrutura de módulos, modelo de dados e plano de build.
> Derivado do `SPEC.md` (requisitos A1–A12, B1–B6, RF-*, RN-1..RN-6) e do `REPORT.md`.

## 0. Stack (justificativa em 3 linhas)
- **Python 3.11+** (o alvo usava 3.13; usamos 3.11+ p/ compatibilidade ampla de wheels, evitando 3.14 recém-saído): permite iteração rápida, ótimo ecossistema ADB/serial/PDF e baixa barreira de manutenção para uso pessoal.
- **PyQt6** para UI desktop (fiel ao alvo que era Qt/PyQt5, com widgets maduros, tema claro/escuro, alta densidade de informação e suporte a WebEngine só se necessário — aqui não usamos).
- **SQLite** (padrão `sqlite3` + camada fina) e **PyMuPDF** para PDF; subprocessos para `adb`/`fastboot`/`scrcpy` (ferramentas oficiais livres do usuário).
> Alternativa considerada e descartada: Electron (pesado, JS desnecessário) e Tkinter (UI pobre p/ densidade de oficina). Qt ganha por fidelidade e qualidade de widgets.

## 1. Princípios de desenho
1. **Clean-room**: implementação própria, sem qualquer referência a código decompilado.
2. **Offline-first**: zero rede para funcionalidade. Nenhum cliente HTTP/MySQL/Keygen.
3. **Camadas rígidas**: UI não toca banco diretamente; regras de negócio ficam em serviços; acesso a dados em repositórios; integração com dispositivo (ADB) atrás de uma porta adaptável.
4. **Testabilidade**: parsers e serviços puros (sem Qt) testáveis sem dispositivo e sem UI.
5. **Sem mecanismos anti-análise** (RN-13 do SPEC / §5): código aberto, logs transparentes.
6. **Conformidade**: os RNs (§5 do SPEC) são aplicados na revisão de módulo — nenhum pacote de bypass.

## 2. Visão em camadas
```
+-------------------------------------------------------------+
|  UI (PyQt6)  — views/, widgets/, dialogs/                   |
|    * só apresentação + validação visual                     |
+---------------------------▲---------------------------------+
                            | sinais / DTOs
+---------------------------▼---------------------------------+
|  Serviços (regras de negócio)  — core/services/             |
|    * OrdemServicoService, ClienteService, DiagnosticoService|
|    * RelatorioService, SolucaoService, ConfigService        |
+---------------------------▲---------------------------------+
                            | modelos de domínio
+---------------------------▼---------------------------------|
|  Persistência  — core/db/  (repositórios + migrações)       |
|    * SQLite, UoW simples, migrações versionadas             |
+---------------------------▲---------------------------------+
                            |
+---------------------------▼---------------------------------+
|  Integração dispositivo  — core/device/                     |
|    * DeviceGateway (porta) → AdbGateway (subprocess)         |
|    * parsers puros em core/diag/                             |
+-------------------------------------------------------------+
Camadas laterais transversais: core/pdf/ (relatórios), core/backup/ (backup)
```

## 3. Estrutura de pastas (plano de projeto)
```
union-manager/
├─ main.py                     # bootstrap: QApplication, tema, instância única
├─ requirements.txt
├─ setup.ps1 / setup.sh        # cria venv, instala deps, checa platform-tools
├─ README.md                   # build/execução
│
├─ app/
│  ├─ __init__.py
│  ├─ core/
│  │  ├─ db/
│  │  │  ├─ connection.py      # factory de conexão, PRAGMAs (WAL, foreign_keys)
│  │  │  ├─ migrations/        # 0001_init.py, 0002_*.py (runner versionado)
│  │  │  └─ repos/             # cliente_repo, ordem_repo, kb_repo, solucao_repo, config_repo
│  │  ├─ models/               # dataclasses/pydantic: Cliente, OrdemServico, Solucao, ...
│  │  ├─ services/             # regras de negócio (sem Qt)
│  │  ├─ device/
│  │  │  ├─ gateway.py         # porta abstrata (interfaces)
│  │  │  ├─ adb_gateway.py     # subprocess adb/fastboot, parsers de erro
│  │  │  └─ scrcpy.py          # espelhamento (opcional, detecta binário)
│  │  ├─ diag/                 # parsers puros: battery, identity, cpu, mem, sensors,
│  │  │                        #   signal, storage, touch, camera, audio, partitions, logcat
│  │  ├─ pdf/                  # ordem_pdf (A4), ordem_thermal (80mm), diag_pdf, relatorio_pdf
│  │  └─ backup/               # backup_manager (ZIP + PRAGMA check)
│  │
│  ├─ ui/
│  │  ├─ theme/                # qss claro/escuro, paleta, ícones
│  │  ├─ i18n/                 # pt_br.py, en.py, es.py + translation_manager
│  │  ├─ main_window.py        # sidebar + menu + área central
│  │  ├─ views/
│  │  │  ├─ dashboard/         # cards de categorias + status
│  │  │  ├─ clientes/          # form, list, details, edit
│  │  │  ├─ ordens/            # form, details, edit, open, close, history, window
│  │  │  ├─ conhecimento/      # add, search, view_solution
│  │  │  ├─ solucoes/          # vitrine por marca, minhas_solucoes
│  │  │  ├─ relatorios/        # daily, monthly
│  │  │  ├─ diagnostico/       # hub de abas (battery/identity/... + logcat + pdf)
│  │  │  ├─ ferramentas/       # apps_manager, system_monitor, dependencias_usb
│  │  │  └─ config/            # empresa, perfil
│  │  ├─ widgets/              # sidebar, cards, image_preview, filtros, progresso
│  │  └─ dialogs/              # confirmacao, viewer de imagem/pdf, sobre
│  │
│  └─ resources/               # ícones, logo placeholder, manual embutido
│
├─ data/                       # criado em runtime (LOCALAPPDATA ou ao lado)
│  ├─ union.db                 # SQLite central (ou dbs por módulo)
│  ├─ fotos/<os_id>/           # fotos das ordens
│  ├─ attachments/kb/          # anexos da base de conhecimento
│  └─ backups/
│
└─ tests/
   ├─ test_diag_parsers.py     # parsers puros com fixtures de saída ADB
   ├─ test_services.py         # regras de OS/KB/relatórios
   └─ test_repos.py            # persistência + migrações
```

## 4. Modelo de dados (SQLite)
> Unificado em um `union.db` com `user_id` nullable (multiusuário local futuro). Chaves estrangeiras + índices por marca/modelo/status.

- **clientes**(id, user_id, nome, telefone, email, rua, numero, bairro, cidade, tipo(`pessoa_fisica`|`lojista`), observacoes, criado_em, atualizado_em)
- **ordens_servico**(id, user_id, cliente_id FK, tipo_dispositivo, marca, modelo, serie, valor, problema, diagnostico, status(`em_reparo`|`concluido_sucesso`|`concluido_sem_solucao`), solucao, passos, motivo_falha, observacoes_tecnicas, valor_final, foto_conclusao, os_original_id FK (garantia), data_entrada, data_conclusao)
- **ordem_fotos**(id, ordem_id FK, caminho, ordem, criado_em)
- **conhecimento**(id, user_id, tipo_dispositivo, marca, modelo, problema, solucao, passos, taxa_sucesso, origem(`manual`|`os_encerrada`), ordem_origem_id, criado_em)
- **conhecimento_anexos**(id, conhecimento_id FK, tipo, caminho, descricao)
- **solucoes**(id, user_id, marca, modelo, descricao, observacoes, status, hash, versao, criado_em, atualizado_em)
- **solucao_midia**(id, solucao_id FK, tipo(`imagem`|`diagrama`), caminho, posicao)
- **config_empresa**(user_id PK, logo, razao_social, cnpj, nome_fantasia, endereco, cidade, estado, telefone, email, website, mensagem_rodape, termos_garantia)
- **perfil_usuario**(user_id PK, nome, telefone, email, foto, bio, nascimento, notif_email, notif_push)
- **migrations**(version PK, aplicado_em)

## 5. Fluxos-chave (referência p/ Fase 6)
1. **Boot**: `main.py` → QApplication + tema + instância única (`QSharedMemory`) → migrações → MainWindow (sem login de licença — opcional login local simples, sem DRM).
2. **Criar OS**: OrdemWindow → form (autocomplete cliente, validação de valor) → `OrdemServicoService.criar()` → repo insere + cria pasta de fotos → oferece PDF.
3. **Diagnosticar**: DiagnosticoHub → `DeviceGateway.listar_dispositivos()` → coleta via `AdbGateway` (thread) → parsers puros → formatters → exibição → `DiagPdf.gerar()`.
4. **Encerrar OS**: CloseDialog → validações (sucesso exige solução, etc.) → `OrdemServicoService.encerrar()` → se sucesso, `SolucaoService.criar_da_ordem()` (RF-OS-5) → PDF.
5. **Relatórios**: `RelatorioService.diario(data)` / `.mensal(ano,mes)` → agregações SQL → tabela + PDF.
6. **Backup**: `BackupManager.criar_zip()` (PRAGMA check) / `.restaurar()`.

## 6. Integrações de dispositivo (limite permitido)
- `adb` / `fastboot` / `scrcpy`: ferramentas **oficiais livres**; o app as **delega** por subprocess com timeout, captura de stdout/stderr e mapeamento de erros comuns (unauthorized/offline/not found). Se ausentes, orienta instalação (RF-TOL-5) — sem embutir binários proprietários (RN-3).
- **Nenhum** loader proprietário, autenticação de firehose, patch de partição ou binário de terceiros embutido (RN-1/RN-3/RN-5).
- Desbloqueio limitado a comandos legítimos de fastboot/ADB com aviso de risco (RF-UNL-1/2).

## 7. Plano de implementação (ordem da Fase 6)
1. Esqueleto: projeto, `main.py`, tema, i18n, instância única, migrações + `union.db`.
2. Persistência: models + repos (clientes, ordens, KB, soluções, config).
3. Serviços de gestão: Cliente, OrdemServico (ciclo de vida + auto-aprendizado), Solucao, Relatorio.
4. UI de gestão: MainWindow/sidebar, clientes, ordens, KB, relatórios, config empresa/perfil.
5. PDF: A4, térmico 80mm, diagnóstico, relatórios.
6. Device layer: AdbGateway + parsers puros + testes com fixtures.
7. UI bancada: DiagnosticoHub, gerenciador de apps, monitor, dependências USB.
8. Soluções por marca + minhas soluções + backup.
9. Polish: tema dark, atalhos, tratamento de erros, README/setup, `CHECKLIST.md`.

## 8. Premissas de ambiente (verificado 2026-10-28)
- **Scoop NÃO está instalado** no ambiente-alvo (sem `scoop.cmd`, `~/.scoop`, variável `SCOOP`, bucket `main`, shims ou entrada de registro). Qualquer script de setup deve usar **winget** para deps de GUI/sistema e **pip** para libs Python.
- Disponível no ambiente: `winget v1.29.380`, `Python 3.14.7` (`C:\Python314`, pip 26.2.1). O alvo original era Python 3.13; o clone será desenvolvido/testado em 3.14, o que exige PyQt6 e PyMuPDF com wheels p/ 3.14.

## 9. Fora do escopo desta fase
- Empacotamento final (PyInstaller) — decisão posterior; a Fase 6 entrega execução por `python main.py` + `setup`.
- Nenhum backend/servidor (B3/B6 do SPEC).
