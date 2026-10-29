# SPEC — Union Manager (clone clean-room)
> Especificação de requisitos do app próprio, derivada do `REPORT.md` (engenharia reversa de "union v1.3.4.5").
> Este documento define o QUÊ o clone faz. O COMO (stack, módulos) fica para a Fase 5 (ARQUITETURA).
>
> **Princípios do produto**
> 1. **Clean-room**: implementação própria. Nenhum código do alvo é copiado.
> 2. **Offline-first / sem backend**: o clone roda 100% local (SQLite). **Não** reproduz API de licenças, MySQL remoto, sync de nuvem nem licenciamento — descartados de propósito (ver §1.2).
> 3. **Escopo de uso pessoal/oficina**: gestão de oficina + bancada de diagnóstico. **Sem** capacidade de bypass FRP/DRM/anti-cheat (ver §5, requisitos negativos).

## 0. Nomenclatura e personas
- **App**: "Union Manager" (marca própria; não reutiliza "RESTORECELL"/"Tech Union Solutions").
- **Persona principal**: técnico de assistência (dono da oficina). Multiusuário local opcional.
- **Contexto de uso**: Windows 10/11, tela 1200×700+, uso com aparelho Android conectado (ADB/fastboot) ou não.

## 1. Escopo
### 1.1 Incluído (o clone FARÁ)
- A1. Gestão de clientes (CRUD, PF/Lojista, busca).
- A2. Ordens de serviço (ciclo de vida, fotos, valores, PDF A4/térmico, garantia).
- A3. Base de conhecimento / soluções (CRUD, anexos, busca, auto-aprendizado ao encerrar OS com sucesso).
- A4. Soluções por marca (catálogo visual local com imagens/diagramas).
- A5. "Minhas soluções" (soluções próprias, backup/restauração local).
- A6. Relatórios diário e mensal (métricas + faturamento).
- A7. Configurações da empresa (logo, razão social, garantia padrão) e perfil do usuário.
- A8. Diagnóstico Android via ADB (bateria, identidade, storage, CPU, memória, sensores, sinal, rede, touch, câmera, áudio, partições, logcat) + relatório PDF.
- A9. Ferramentas de bancada ADB/fastboot (gerenciador de apps, monitor de sistema, reboot/modos, limpeza, espelhamento scrcpy).
- A10. Módulo de desbloqueio **apenas comandos legítimos de bancada** (fastboot/ADB padrão) — ver §5 para o que é excluído.
- A11. Backup/restauração dos dados locais.
- A12. UI em PT-BR com estrutura de i18n (PT/EN/ES), tema claro/escuro, instância única.

### 1.2 Excluído de propósito (o clone NÃO FARÁ)
- B1. **Qualquer bypass de FRP / Mi Account / MDM / Knox / PayJoy / anti-cheat** (apagamento de partições, injeção de payloads, device owner forçado, patch de `user_setup_complete`, etc.). **Requisito negativo obrigatório** — ver §5.
- B2. API de licenças / ativação / revalidação / fingerprint de máquina / detecção de VM / anti-debug / anti-captura de tela.
- B3. Backend MySQL remoto, sincronização de nuvem, serviços premium, downloads de firmware, catálogo de películas, servidor Flask "Union OS" em rede.
- B4. Painel administrativo com geração de `update.zip` e auditoria remota.
- B5. Qualquer uso de binários externos proprietários embutidos (mtk.exe, FRP_EDL, odin4, ExynosBridgeHost, spd_dump, loaders, etc.).
- B6. Segredos hardcoded do alvo (chaves, credenciais, tokens, NextDNS, chaves SLA). O clone não contém nenhum.

> **Racional**: reproduzir B1–B6 violaria a regra do usuário (não implementar bypass) e/ou dependia de infraestrutura/credenciais alheias. O clone é um produto autônomo de gestão + diagnóstico.

## 2. Requisitos funcionais — Gestão (A1–A7)
### 2.1 Clientes (A1)
- RF-CLI-1: criar/editar/excluir cliente com campos: nome*, telefone*, e-mail (valida "@"), endereço (rua/número/bairro/cidade), **tipo: Pessoa Física | Lojista**, observações.
- RF-CLI-2: impedir duplicidade por (nome+telefone); excluir bloqueado se houver OS vinculadas (com opção forçar e apagar fotos).
- RF-CLI-3: busca incremental por nome/telefone/e-mail; detalhes com histórico de OS e estatísticas; atalho "Nova OS para este cliente".
- RF-CLI-4: todos os dados isolados por usuário (quando multiusuário ativo).

### 2.2 Ordens de serviço (A2)
- RF-OS-1: status `em_reparo` → `concluido_sucesso` | `concluido_sem_solucao`; rótulos legados exibíveis em histórico.
- RF-OS-2: criar OS com cliente (autocomplete), dispositivo (tipo: Notebook/Smartphone/Desktop/Tablet/Impressora/Outro, marca*, modelo*, série, valor com validação em tempo real), diagnóstico (problema*, diagnóstico inicial, múltiplas fotos). Salva já em reparo, com pasta própria de fotos.
- RF-OS-3: editar OS e gerenciar fotos (adicionar/remover).
- RF-OS-4: encerrar OS: sucesso exige solução; ambos exigem passos; sem solução exige motivo. Valor final + foto de conclusão.
- RF-OS-5: **auto-aprendizado**: encerrar com sucesso injeta solução na base de conhecimento (taxa 100%).
- RF-OS-6: reabrir OS (Garantia) cria nova OS vinculada, copiando cliente/dispositivo/problema e citando a original.
- RF-OS-7: PDF em **A4** e **térmico 80 mm** (cabeçalho/rodapé da empresa, foto de encerramento opcional, trata arquivo em uso).
- RF-OS-8: dashboard: cards (em reparo, concluídas hoje, últimas conclusões, total clientes), tabela das 50 mais recentes, filtros.

### 2.3 Base de conhecimento (A3)
- RF-KB-1: cadastrar solução (tipo dispositivo, marca, modelo, problema, solução, passos, taxa de sucesso 0–100).
- RF-KB-2: anexos (fotos, PDF, doc/docx/txt/rtf) com descrição; abrir/remover (remove arquivo do disco).
- RF-KB-3: busca por marca/modelo/problema + filtro por tipo; detalhes com anexos.

### 2.4 Soluções por marca (A4)
- RF-SOL-1: vitrine por marca com cards responsivos, busca com debounce, filtro por categorias de problema.
- RF-SOL-2: visualização de imagem e diagrama (PDF ou imagem) com zoom e navegação; render de 1ª página de PDF.

### 2.5 Minhas soluções (A5)
- RF-MSO-1: CRUD das próprias soluções (marca, modelo, descrição, observações, até 3 imagens, até 2 diagramas) em SQLite local.
- RF-MSO-2: filtros (marca/status/texto) e estatísticas; exibição de mídia.
- RF-MSO-3: backup/restauração manual local (ver A11).

### 2.6 Relatórios (A6)
- RF-REP-1: diário (por data): OS abertas, concluídas sucesso, sem solução, faturamento + tabela.
- RF-REP-2: mensal (mês/ano): total, concluídas, em reparo, taxa de sucesso %, faturamento, tempo de reparo (dias).
- RF-REP-3: exportação/impressão dos relatórios.

### 2.7 Empresa e perfil (A7)
- RF-CFG-1: config da empresa (logo, razão social, CNPJ, nome fantasia, contato, mensagem de rodapé, **termos de garantia** padrão 90 dias) gravadas em SQLite.
- RF-CFG-2: perfil do usuário local (nome, telefone, e-mail, foto, bio, nascimento, preferências) — **sem** saldo de créditos/nível/nuvem.
- RF-CFG-3: PDF de OS e relatórios usam as configurações da empresa.

## 3. Requisitos funcionais — Bancada (A8–A10)
### 3.1 Diagnóstico Android (A8)
- RF-DIA-1: detectar aparelho via ADB com tratamento claro de erros (unauthorized/offline/not found/defender).
- RF-DIA-2: coletar e exibir: bateria (nível/saúde/temp/voltagem/ciclos/ASOC), identidade (marca/modelo/Android/patch/build/fingerprint/baseband/kernel/bootstate), storage (eMMC/UFS), CPU (SoC/freq), memória, sensores, térmica, WiFi/rede, sinal (dBm por geração, barras por SIM), USB, touch (chip/ressolução), câmera, áudio, eventos (logcat erros + uptime), partições.
- RF-DIA-3: logcat ao vivo com coloração por severidade e captura.
- RF-DIA-4: gerar **relatório PDF** do diagnóstico com cabeçalho da oficina e assinatura do técnico.
- RF-DIA-5: bugreport (`adb bugreport`) opcional com progresso.
- RF-DIA-6: parsers puros (separados da UI) para tornar testável sem dispositivo.

### 3.2 Ferramentas de bancada (A9)
- RF-TOL-1: gerenciador de apps ADB (listar sistema/usuário/MDM, force-stop, limpar cache/dados, instalar/desinstalar, congelar/descongelar, em lote).
- RF-TOL-2: monitor de sistema em tempo real (CPU/RAM/processos, kill, alertas por limiar, exportar).
- RF-TOL-3: ações ADB/fastboot padrão: reboot (sistema/fastboot/recovery), status de bootloader, obter IMEI/info, concessão de permissões.
- RF-TOL-4: espelhamento de tela (scrcpy), se disponível no sistema; detectar/instanciar de forma independente.
- RF-TOL-5: **gerenciador de dependências USB** (checar/instalar platform-tools, drivers) — apenas componentes livres/oficiais, com transparência do que é instalado.
- RF-TOL-6: manual de uso embutido (instalação de platform-tools, uso dos diagnósticos).

### 3.3 Desbloqueio (A10) — escopo reduzido e legítimo
- RF-UNL-1: expor **apenas** operações que delegam a ferramentas oficiais do ecossistema (ex.: `fastboot oem unlock` com aviso de wipe, `fastboot getvar`, reboot para download/recovery), sempre com **aviso de risco e responsabilidade do usuário**.
- RF-UNL-2: **não** inclui loaders proprietários, autenticação de firehose, patch de partições, payloads de bypass nem scripts de modelo. (Ver §5.)

## 4. Requisitos não-funcionais
### 4.1 Dados e persistência
- RF-NF-1: SQLite local por módulo (`service_orders.db`, `solutions.db`, `knowledge.db` ou único centralizado — decisão na Fase 5), com migrações versionadas.
- RF-NF-2: backup/restauração ZIP integro (PRAGMA check) com progresso; backup automático antes de operação destrutiva.
- RF-NF-3: blobs de imagem/diagrama armazenados de forma eficiente (compressão) e cache local com expiração.
- RF-NF-4: **nenhum dado sai da máquina** (sem rede para sincronização). Telemetria: nenhuma.

### 4.2 UI/UX
- RF-NF-5: tema claro/escuro, estilo moderno, janela mínima 1200×700, instância única.
- RF-NF-6: i18n PT-BR (padrão), EN, ES; troca em runtime com fallback (chave → PT → chave).
- RF-NF-7: feedback de erro amigável (sem vazar stack trace/paths internos).
- RF-NF-8: operações longas em thread com progresso e cancelamento (não bloquear a UI).

### 4.3 Segurança e robustez
- RF-NF-9: senhas locais (se houver login) com hash adequado (não SHA-256 puro sem salt).
- RF-NF-10: validação de entrada (sanitização, limites de tamanho, caminhos seguros).
- RF-NF-11: tratamento centralizado de falhas ADB/fastboot com mensagens acionáveis.
- RF-NF-12: logs locais úteis para suporte, sem expor segredos (não há segredos).
- RF-NF-13: **sem** mecanismos anti-análise, anti-debug, ofuscação ou anti-captura. Código aberto e auditável por definição.

## 5. Requisitos NEGATIVOS (obrigatórios — nunca implementar)
- RN-1: **Não implementar bypass** de FRP, Mi Account, MDM, Knox, PayJoy, anti-rollback, bootloader remoto, nem qualquer contorno de verificação de conta/política do fabricante por patch de partição ou injeção de payload.
- RN-2: Não implementar **licenciamento/DRM/anti-cheat** (validação de chave, revalidação, fingerprint de máquina, bloqueio por VM/debugger, anti-captura).
- RN-3: Não incluir **binários proprietários de terceiros** embutidos nem chaves para extraí-los.
- RN-4: Não reproduzir **credenciais, tokens, endpoints ou chaves** do alvo (API Keygen, MySQL, NextDNS, segredos HMAC/SLA, `.key`).
- RN-5: Não executar/apoiar operação destrutiva de partição (erase/program/patch de flash) a partir do clone.
- RN-6: Qualquer funcionalidade sensível de bancada que dependa de ferramentas externas deve **delegar às ferramentas oficiais** e deixar claro o que roda, sem ocultar caminhos/comandos.

> Estes requisitos negativos são o guard-rail de compliance da Fase 6 (IMPLEMENTAÇÃO) e serão verificados na Fase 7.

## 6. Critérios de aceite (resumo)
- AC-1: cada RF acima é implementado, testável offline, sem rede.
- AC-2: nenhum RN é violado (revisão de código + checklist na Fase 7).
- AC-3: o app gerencia um ciclo completo de oficina: criar cliente → criar OS → diagnosticar aparelho conectado → encerrar com sucesso → solução entra na base → relatório mensal mostra o faturamento → backup restaura tudo.
- AC-4: relatórios (OS e diagnóstico) saem em PDF A4 e térmico com dados da empresa.
- AC-5: UI PT-BR completa, tema claro/escuro, multi-janelas sem travamento em operações longas.
