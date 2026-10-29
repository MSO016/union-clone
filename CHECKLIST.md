# CHECKLIST — Verificação clone × SPEC (Fase 7)

> Cruzamento requisito a requisito entre o `SPEC.md` e o código do clone em
> `union-manager/`. Status verificado por leitura de código + suíte de testes
> (6/6 verde, offline, sem rede).
>
> Legenda: **✅** implementado e testado · **🔶** parcial · **❌** não implementado · **N/A** não aplicável

## 1. Requisitos funcionais — Gestão

| Req | Item | Status | Evidência / motivo |
|---|---|---|---|
| RF-CLI-1 | CRUD de cliente com campos obrigatórios e validação | ✅ | `cliente_service.criar/editar` (nome/telefone obrigatórios, "@" no e-mail); `cliente_form.py` |
| RF-CLI-2 | Duplicidade (nome+telefone) e bloqueio de exclusão com OS | 🔶 | Duplicidade ✅ e bloqueio ✅ (`cliente_service.excluir`); opção `forcar` existe no serviço mas **não há botão na UI** |
| RF-CLI-3 | Busca incremental + detalhes com histórico/estatísticas | 🔶 | Busca ✅ (`clientes_view`, por nome/telefone); **detalhes com histórico e atalho "Nova OS" não implementados** |
| RF-CLI-4 | Isolamento por usuário | 🔶 | `user_id` propagado no modelo/serviços; **multiusuário/login fora do escopo local** (sem efeito prático) |
| RF-OS-1 | Ciclo de vida de status + rótulos legados | ✅ | `StatusOrdem`, `ROTULOS_LEGADOS` (`models.py`), testado em `test_dominio` |
| RF-OS-2 | Criar OS (cliente, dispositivo, valores, fotos) | 🔶 | Criação ✅ (`ordem_form.py` + `ordem_service.criar`, validações); **gerenciamento de fotos na UI não implementado** (repo tem `adicionar_foto/remover_foto`) |
| RF-OS-3 | Editar OS e gerenciar fotos | 🔶 | `ordem_repo.atualizar` existe; **edição/fotos não expostas na UI** |
| RF-OS-4 | Encerramento com regras (sucesso→solução; sem solução→motivo) | ✅ | `ordem_service.encerrar` (testado) + `encerramento_dialog.py` com campos condicionais |
| RF-OS-5 | Auto-aprendizado ao encerrar com sucesso | ✅ | `ordem_service.encerrar` injeta na base; coberto por `test_services`; origem visível em `conhecimento_view` |
| RF-OS-6 | Reabertura por Garantia (nova OS vinculada) | ✅ | `ordem_service.reabrir_garantia` (testado) + botão na `ordens_view` |
| RF-OS-7 | PDF A4 e térmico 80 mm | 🔶 | `gerar_ordem_a4`/`gerar_ordem_termica` ✅ (botões na UI, testados em `test_pdf`, largura 80 mm verificada); **foto de encerramento e tratamento específico de "arquivo em uso" não implementados** (erro genérico exibido) |
| RF-OS-8 | Dashboard com cards + tabela + filtros | 🔶 | Cards de status ✅ e tabela ✅ (`ordens_view`); **"concluídas hoje", "últimas conclusões", "total clientes" e filtros não implementados** (`repo.recentes` existe, UI usa `listar_abertas`) |
| RF-KB-1 | Cadastrar solução (inclui taxa 0–100) | 🔶 | Cadastro ✅ (`conhecimento_view`); **campo de taxa de sucesso não editável na UI** (fica 100) |
| RF-KB-2 | Anexos (fotos/PDF/docs) com abrir/remover | ❌ | Repo (`conhecimento_repo.anexos_*`) pronto; **UI de anexos não implementada** |
| RF-KB-3 | Busca + filtro por tipo + detalhes | 🔶 | Busca e filtro ✅, detalhes de texto ✅; **detalhes com anexos ❌** (depende de RF-KB-2) |
| RF-SOL-1/2 | Vitrine "Soluções por marca" (cards, zoom, diagramas) | ❌ | Não implementado (módulo A4 do SPEC) |
| RF-MSO-1/2 | "Minhas soluções" (CRUD + mídia + filtros) | ❌ | Tabela `solucoes`/`solucao_midia` existe no esquema; **serviço/UI não implementados** |
| RF-MSO-3 | Backup/restauração local | ✅ | `backup_service.py` + aba Backup na ConfigView (testado em `test_backup`) |
| RF-REP-1 | Relatório diário | ✅ | `relatorio_service.resumo_diario` (testado) + `relatorios_view` |
| RF-REP-2 | Relatório mensal (inclui tempo de reparo) | 🔶 | Total/concluídas/taxa/faturamento ✅; **"tempo de reparo (dias)" não calculado** |
| RF-REP-3 | Exportação/impressão dos relatórios | 🔶 | `gerar_relatorio_pdf` ✅ (testado); **sem botão de exportação na view de relatórios** |
| RF-CFG-1 | Config da empresa (com termos de garantia) | 🔶 | Todos os campos ✅ (`config_view` aba Empresa); **seletor de logo não implementado** (campo `logo` no modelo/BD, sem UI) |
| RF-CFG-2 | Perfil do usuário local | 🔶 | Nome/telefone/e-mail/bio/notificações ✅; **foto e nascimento sem UI** |
| RF-CFG-3 | PDFs usam config da empresa | ✅ | `ordem_pdf.py` recebe `ConfigEmpresa` (cabeçalho/rodapé/garantia); `ordens_view` passa o config |

## 2. Requisitos funcionais — Bancada

| Req | Item | Status | Evidência / motivo |
|---|---|---|---|
| RF-DIA-1 | Detecção ADB com erros claros | ✅ | `AdbGateway.listar_dispositivos` + estados na UI (`device`/`offline`/`unauthorized` exibidos) |
| RF-DIA-2 | Coleta ampla (bateria, identidade, storage, CPU, …) | 🔶 | Bateria ✅ (parser + fixture + teste) e identidade ✅ (`ferramentas_view`); **storage/CPU/memória/sensores/rede/sinal/touch/câmera/áudio/partições não implementados** |
| RF-DIA-3 | Logcat ao vivo com cores | ❌ | Não implementado |
| RF-DIA-4 | PDF do diagnóstico | 🔶 | `gerar_diagnostico_pdf` ✅ com botão na UI; **assinatura do técnico não implementada** |
| RF-DIA-5 | bugreport com progresso | ❌ | Não implementado |
| RF-DIA-6 | Parsers puros testáveis | ✅ | `app/core/diag/bateria.py` + `fixtures/` + `test_diag` |
| RF-TOL-1 | Gerenciador de apps ADB | ❌ | Não implementado |
| RF-TOL-2 | Monitor de sistema em tempo real | ❌ | Não implementado |
| RF-TOL-3 | Ações ADB/fastboot (reboot, bootloader, IMEI) | ❌ | Não implementado (base `AdbGateway.executar_shell` disponível) |
| RF-TOL-4 | Espelhamento scrcpy | ❌ | Não implementado |
| RF-TOL-5 | Gerenciador de dependências USB | 🔶 | Detecção do `adb` no PATH ✅ (`disponivel()` + aviso na UI); **instalação guiada de platform-tools não implementada** |
| RF-TOL-6 | Manual embutido | ❌ | Não implementado (existe apenas o `README.md`) |
| RF-UNL-1 | Operações legítimas de desbloqueio com aviso | ❌ | Não implementado (não há nenhuma função de desbloqueio no clone) |
| RF-UNL-2 | Sem loaders/payloads/patches | ✅ | Nenhum binário proprietário nem payload existe no projeto (verificado por busca) |

## 3. Requisitos não-funcionais

| Req | Item | Status | Evidência / motivo |
|---|---|---|---|
| RF-NF-1 | SQLite + migrações versionadas | ✅ | `connection.py` (WAL, FK) + `migrations/runner.py` + `m0001_init` (9 tabelas) |
| RF-NF-2 | Backup íntegro + automático antes de destrutivos | 🔶 | Backup manual consistente (API `conn.backup`) + validação + `.old` ✅; **formato é .db (não ZIP) e não há backup automático antes de exclusões** |
| RF-NF-3 | Armazenamento eficiente de blobs + cache | ❌ | Sem blobs de imagem ainda (fotos/anexos não implementados na UI) |
| RF-NF-4 | Nenhum dado sai da máquina; sem telemetria | ✅ | Sem rede no código (busca por sockets/requests: nenhum); app 100% local |
| RF-NF-5 | Tema claro/escuro, 1200×700, instância única | ✅ | `tema.py`, `MainWindow.setMinimumSize(1200,700)`, `QSharedMemory` em `main.py` |
| RF-NF-6 | i18n PT/EN/ES com fallback | 🔶 | Infraestrutura ✅ (`translation_manager` com fallback chave→PT→chave) mas **só o dicionário PT-BR existe** |
| RF-NF-7 | Erros amigáveis sem stack trace | ✅ | `ValidacaoError` com mensagens em PT; QMessageBox nas views |
| RF-NF-8 | Operações longas em thread | ❌ | Chamadas ADB/PDF rodam na thread da UI (rápidas no uso típico, mas **sem worker/progresso**) |
| RF-NF-9 | Hash adequado de senhas | N/A | Sem login/senhas no escopo local |
| RF-NF-10 | Validação de entrada | ✅ | Serviços validam nomes/telefones/e-mail; valores com `QDoubleSpinBox` limitado |
| RF-NF-11 | Falhas ADB com mensagens acionáveis | 🔶 | Timeouts/FinderError viram saída vazia + avisos; **mensagens mais específicas (permissão, daemon) pendentes** |
| RF-NF-12 | Logs locais úteis | ❌ | Sem arquivo de log |
| RF-NF-13 | Sem anti-análise/anti-debug/ofuscação | ✅ | Código puro e legível; nenhuma dessas técnicas existe |

## 4. Requisitos NEGATivos (guard-rail de compliance)

Verificados por revisão de código + busca no projeto inteiro (`union-manager/app`, `tests`):

| Req | Item | Status | Verificação |
|---|---|---|---|
| RN-1 | Nenhum bypass FRP/Mi Account/MDM/Knox/PayJoy/anti-rollback | ✅ **CUMPRIDO** | Nenhum código de bypass; comandos ADB do clone são apenas `dumpsys`, `getprop` e `devices` (somente leitura) |
| RN-2 | Nenhum licenciamento/DRM/anti-cheat/fingerprint/VM-check | ✅ **CUMPRIDO** | Busca por `license/keygen/ativacao/fingerprint`: zero ocorrências; `main.py` declara explicitamente "sem login de licença" |
| RN-3 | Nenhum binário proprietário de terceiros embutido | ✅ **CUMPRIDO** | Projeto contém apenas `.py`, fixtures de texto e docs; sem `.exe`/`.dll`/loaders |
| RN-4 | Nenhuma credencial/token/endpoint/chave do alvo | ✅ **CUMPRIDO** | Sem MySQL, sem API keys, sem NextDNS, sem HMAC/SLA, sem `.key`; nenhuma string do alvo foi copiada |
| RN-5 | Nenhuma operação destrutiva de partição (erase/program/patch) | ✅ **CUMPRIDO** | Nenhum `flash/erase/program` no código; fastboot não é invocado |
| RN-6 | Delegação transparente a ferramentas oficiais | ✅ **CUMPRIDO** | O único binário externo é o `adb` oficial do usuário (platform-tools), invocado por `subprocess` com o comando visível no código; o README declara a dependência |

## 5. Critérios de aceite

| AC | Estado | Nota |
|---|---|---|
| AC-1 | 🔶 | Núcleo (gestão + relatórios + backup) implementado e offline; módulos de bancada ampla (RF-TOL/RF-DIA-2 completo) e vitrines (RF-SOL/RF-MSO) pendentes — ver §6 |
| AC-2 | ✅ | Nenhum RN violado (§4) |
| AC-3 | 🔶 | Ciclo completo funciona (cliente→OS→bateria/identidade→encerrar→auto-aprendizado→relatório→backup, todos testados); **etapa de "diagnosticar" cobre bateria/identidade apenas** |
| AC-4 | ✅ | PDF A4/térmico de OS e de diagnóstico com dados da empresa (`test_pdf` valida os 4 formatos) |
| AC-5 | 🔶 | UI PT-BR completa e tema claro/escuro ✅; **sem operações longas em thread** (RF-NF-8 pendente) |

## 6. Pendências (lista única)

1. **UI de fotos de OS** (RF-OS-2/3): adicionar/remover fotos na UI usando `ordem_repo.adicionar_foto/remover_foto`.
2. **Edição de OS na UI** (RF-OS-3): diálogo de edição usando `ordem_repo.atualizar`.
3. **Detalhes do cliente** (RF-CLI-3): histórico de OS, estatísticas e atalho "Nova OS para este cliente".
4. **Botão "forçar exclusão"** de cliente com OS vinculadas (RF-CLI-2, já previsto no serviço).
5. **Cards extras do dashboard** (RF-OS-8): concluídas hoje, últimas conclusões, total de clientes; tabela das 50 recentes (`repo.recentes`) e filtros.
6. **Campo de taxa de sucesso** no form de solução (RF-KB-1).
7. **Anexos de conhecimento** (RF-KB-2/3): UI de adicionar/abrir/remover anexos.
8. **Vitrine "Soluções por marca"** (RF-SOL-1/2) e **"Minhas soluções"** (RF-MSO-1/2) — módulos inteiros.
9. **Tempo de reparo (dias)** no relatório mensal (RF-REP-2).
10. **Botão de exportação PDF** na view de relatórios (RF-REP-3, função já pronta).
11. **Seletor de logo** da empresa e campos foto/nascimento do perfil (RF-CFG-1/2).
12. **Diagnóstico amplo** (RF-DIA-2): storage, CPU, memória, sensores, rede, sinal, touch, câmera, áudio, partições (parsers puros + fixtures).
13. **Logcat ao vivo** (RF-DIA-3) e **bugreport** (RF-DIA-5).
14. **Assinatura do técnico** no PDF de diagnóstico (RF-DIA-4).
15. **Ferramentas de bancada** (RF-TOL-1..4): gerenciador de apps, monitor de sistema, reboot/info, scrcpy; **instalação guiada de platform-tools** (RF-TOL-5) e **manual embutido** (RF-TOL-6).
16. **Módulo de desbloqueio legítimo** (RF-UNL-1): apenas `fastboot oem unlock`/`getvar`/reboots com aviso de risco — ou descontinuar o item no SPEC com justificativa.
17. **Operações longas em thread** com progresso (RF-NF-8).
18. **Dicionários EN e ES** do i18n (RF-NF-6; infraestrutura já pronta).
19. **Backup em ZIP** com `PRAGMA check` e **backup automático antes de exclusões** (RF-NF-2; hoje é .db manual).
20. **Armazenamento/cache de blobs** quando fotos/anexos forem implementados (RF-NF-3).
21. **Arquivo de log local** sem segredos (RF-NF-12).
22. **Tratamento específico de PDF em uso** (fechado por outro programa) e foto de conclusão no PDF (RF-OS-7).
23. **Mensagens ADB mais específicas** (unauthorized/daemon/permissão) (RF-NF-11).
24. **Multiusuário real** (RF-CLI-4) — hoje `user_id` é sempre 0; decidir se fica fora do escopo permanente.
