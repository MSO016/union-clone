# REPORT — Engenharia Reversa "union v1.3.4.5"
> Relatório consolidado da Fase 3 (MAPA). App-alvo: **union v1.3.4.5** (Inno Setup 7.0.0.3 → PyInstaller onedir, Python 3.13, PyQt5/QtWebEngine). Empresas: Tech Union Solutions / RestoreCell Soluções Tecnológicas (restorecellsolucoes.com, techunionservices.com). Ficha PT-BR: `extracted\app\termos_de_uso.txt`.
>
> **Clean-room:** este relatório descreve funcionalidades em prosa. Nenhum trecho de código decompilado é reproduzido. Bypass de licença/DRM/anti-cheat é apenas documentado, nunca implementado.

## 0. Fonte da informação
- `decomp\` (199 módulos puros do PYZ) e `decomp-decrypted\` (310 módulos decifrados do disco, PYEN→marshal 3.13). 509 módulos, ~107k linhas decompiladas.
- `db-schemas.txt` (5 SQLite), `mapa-funcionalidades.txt` (4.140 linhas de classes/métodos), `translations\pt.py` (dicionário de UI), `premium_services_manager.py`.
- Leitura distribuída em 6 analistas (núcleo/boot, views de OS, diagnóstico, unlock EDL/SPD/Xiaomi, unlock Samsung/moto/hxd/exy, utils/database).

## 1. Visão geral do produto
Desktop Windows para técnicos de assistência técnica de smartphones. Combina **gestão de oficina** (clientes, ordens de serviço, relatórios, base de conhecimento) com **bancada de diagnóstico/reparo** (ADB, fastboot, UART, diagnóstico Android) e um grande **kit de desbloqueio** (FRP/MDM/Mi Account/Flash) por chipset: MediaTek (BROM), Qualcomm (EDL 9008), Spreadtrum/Unisoc (SPD/BSL), Samsung Exynos, e fluxos MTP/factory/ADB.

### 1.1 Boot e janelas (`entry_app.py`)
1. DPI awareness (ctypes); no modo frozen redireciona cache `gen_py`/win32com para `%LOCALAPPDATA%\RESTORECELL`.
2. Ativa hook de importação (`app.utils._import_hook.activate`) — aparenta filtrar/interceptar imports; o corpo não foi recuperado, sobrevive só a lista de módulos permitidos (stdlib, PyQt5/6, numpy, PIL, cv2, cryptography, flask/waitress, mysql/pymysql, boto3, requests).
3. Instância única via `QSharedMemory "UNION_TECHNICAL_SINGLE_INSTANCE"`.
4. Guard pré-login `_cfg_probe` (scan de ambiente + debugger) e timer de guard a cada 10 s.
5. Ordem das janelas: **LoginWindow** → (opcional) **WelcomeWizard** (modal, 1ª vez) → **MainWindow** (QSplashScreen interno) → popup de anúncio após 3 s. No caminho admin abre também o **PainelAdministrativo**.
6. Estilo Fusion, tema escuro opcional (qdarkstyle, QSettings "TechUnion"/"UNION" chave `theme/dark_mode`), WebEngine se disponível.
7. Falha de import distingue bloqueio de política/Defender (INIT-001, dicas: admin, `C:\UNION\`, desativar Smart App Control) de erro genérico (INIT-002); log em `%LOCALAPPDATA%\RESTORECELL\startup_error.log`. Elevação "gentil" a Administrador (runas).

### 1.2 Autenticação e licença
- **Login por licença** (aba "LICENÇA", email + chave): checagem de versão/manutenção → validação da chave na API de licenças → status em MySQL `usuarios` → cria/atualiza usuário → wizard/MainWindow.
- **API estilo Keygen** (URL/account/produto/token em `REFS` de `app\utils\_app_cfg.py`, módulo **só existe como `.pyd`**): POST `/accounts/{acc}/licenses/actions/validate-key`, `/licenses/{id}/machines`, `/machines`; JSON:API com Bearer do produto; mapeia erros EXPIRED/SUSPENDED/INVALID/PRODUCT/USER/MACHINE/NO_MACHINE para mensagens com contatos. Também `REFS.LIC_RENEW_URL`, `REFS.LIC_SUPPORT_WHATSAPP`.
- **Fingerprint de máquina**: MachineGuid (lib `machineid`) + serial de volume de C: (kernel32) → SHA256; migradores v2–v5 em `%LOCALAPPDATA%\TechniciansUnion` limpam cache antigo; detecção de VM via WMI/SMBIOS (bloqueia ativação; fail-open se WMI falhar).
- **Armazenamento local**: email/chave em QSettings "UNION TECHNICAL"/"License"; cache de validação Fernet (chave derivada de hardware) em `%LOCALAPPDATA%\TechniciansUnion\cache\validation_*.enc` com TTL; admin em QSettings "TECHNICIANS UNION"/"Login".
- **Admin**: aba oculta revelada por atalhos secretos (Ctrl+Shift+3, Ctrl+Alt+Shift+A, Ctrl+Shift+F3); `verify_login` local (banco) + tipo 'admin'; abre MainWindow(is_admin=True) + PainelAdministrativo.
- **Revalidação contínua**: worker QThread repete validação; SUSPENDED/BANNED/PRODUCT/POLICY = bloqueio imediato (LIC-201/202/206/207), EXPIRED = bloqueio após N tentativas (LIC-203), OVERDUE = aviso (LIC-208), desconhecido = fail-open; falha de rede → logout offline.
- **`_ci_sentinel` (SectorSentinel)**: consulta `usuarios.status` no MySQL; ≠ 'ativo' força logout (CI-SENTINEL-BLOCK); é o gate `check()` antes de abrir janelas; admin passa direto.
- `login_controller.py`/`main_controller.py` são código de template Tkinter não relacionado ao fluxo real — **ignorar no SPEC**.

### 1.3 MainWindow
- Dimensão mínima 1200×700; `SectorSentinel`; timer de revalidação; tiers por domínio do email (`*.com` = "com user"; `*.com.br`/admin = premium); flag `ui/dashboard_v2` (padrão ligado).
- **Barra lateral** (`app.views.ui.sidebar.Sidebar`): header TECH UNION SOLUTIONS + slogan, chips de usuário, saldo de créditos, dias de licença, "Modo Administrador"/"Plano Premium"; badges "NOVO" em hxd_tools, exy_tools, os_manager (premium/admin).
- **Menu superior**: Android (Diagnóstico, UART Monitor, Manual), Arquivos, Ordens de Serviço, Parceiros, Usuário, Licença, Servidor OS (premium/admin), Idioma, Opções (F11, dark, Sobre, qtd soluções, Sair), Ajuda, Assistentes IA.
- **Grade de cards**: 20 categorias (SAMSUNG, APPLE, MOTOROLA, XIAOMI, REALME, OPPO, VIVO, HUAWEI, INFINIX, TECNO, ANDROID COMANDOS, SOFTWARE, CPU, ESTUDO, JUMPER DE TELAS, EMMC UFS, ESQUEMAS ELÉTRICOS, TEST POINTS, DESBLOQUEIO, DRILL); grid responsivo (`UI_DASHBOARD_RESPONSIVE_GRID`) e card v2 (`UI_DASHBOARD_NEW_CARDS`).
- **Dados**: SQLite `base.db` (`sync_control`, `solucoes` com blobs de diagramas/imagens) sincronizado a cada 5 min com MySQL `solucoes` (diff insert/update/delete + log).
- **Popup de anúncio**: banner blob do MySQL, clique registado, auto-fecho 15 s, anti-captura.

## 2. Gestão de oficina (views de OS, clientes, conhecimento)
Tudo particionado por `user_id` em SQLite local (`app\database\service_orders.db`).

### 2.1 Clientes
- **ClientForm**: diálogo modal 1000×700; campos nome (obrig.), telefone (obrig., máscara), e-mail (só exige "@"), endereço, **Tipo de Cliente = Pessoa Física | Lojista** (`pessoa_fisica`/`lojista`; não há PF/PJ jurídico), observações. Verifica duplicidade por nome+telefone+user_id. Migração automática de colunas via PRAGMA.
- **EditClientDialog**: mesmos campos + Excluir (bloqueia se houver OS vinculadas).
- **ClientDetailsDialog**: ficha + histórico de OS (colorido por status) + cards (total, concluídas, abertas, em reparo) + atalhos "Nova OS para este cliente"/"Editar".
- **ListClientsDialog**: tabela com contagem de OS, ações por linha, busca incremental.

### 2.2 Ordens de serviço — ciclo de vida
- **Status**: `em_reparo` (criação) → `concluido_sucesso` | `concluido_sem_solucao` (encerramento). Rótulos legados (Aberto/Em Andamento/Cancelado) só em histórico/detalhes.
- **ServiceOrderForm**: cliente (autocomplete + cadastro rápido), dispositivo (tipo Note/Smartphone/Desktop/Tablet/Impressora/Outro, marca*, modelo*, série, valor com validação em tempo real), diagnóstico (problema*, diagnóstico inicial, múltiplas fotos). Salva já em reparo; pasta `app\data\fotos\<os_id>`; oferece PDF (A4 ou térmico 80 mm).
- **EditServiceOrderDialog**: edição + gerenciamento de fotos + exclusão com remoção das fotos.
- **ServiceOrderDetailsDialog**: somente-leitura; PDF A4/térmico; **"Reabrir OS (Garantia)"** cria nova OS vinculada com diagnóstico prefixado citando a original.
- **OpenServiceOrdersDialog**: só OS em reparo, com editar/encerrar/excluir/PDF.
- **CloseServiceOrderDialog**: status final + solução + passos + motivo da falha + observações + valor final + foto de conclusão. Regras: sucesso exige solução; ambos exigem passos; sem solução exige motivo. **Sucesso injeta a solução na base de conhecimento (taxa 100%)**.
- **ServiceOrderHistoryDialog**: histórico completo com filtro por status e busca.
- **ServiceOrderWindow**: dashboard (cards: em reparo, concluídas hoje, últimas conclusões, total clientes), tabela 50 OS recentes, sidebar de atalhos, "zerar sistema" com backup prévio.

### 2.3 Base de conhecimento / soluções
- **AddKnowledgeDialog**: tipo de dispositivo, marca, modelo, problema, solução, passos, taxa de sucesso (0–100). Anexos: fotos, PDFs, documentos (doc/docx/txt/rtf) → `app\attachments\knowledge_base`.
- **KnowledgeBaseSearchDialog**: busca por marca/modelo/problema + filtro por tipo; detalhes com anexos abríveis.
- **SolucoesWindow**: vitrine por marca (cards responsivos, busca com debounce, avisos da nuvem, visualização de diagramas PDF/imagem com zoom). Blobs baixados sob demanda, gravados **criptografados** no cache local com hash + data de sync; anti-captura.
- **ViewSolutionDialog/ImageViewerDialog**: imagem + diagrama lado a lado, zoom independente, render da 1ª página de PDF via PyMuPDF, anti-captura para não-admin.

### 2.4 Relatórios
- **DailyReportDialog**: por data — OS abertas, concluídas com sucesso, sem solução, faturamento (soma dos valores concluídos) + tabela.
- **MonthlyReportDialog**: por mês/ano — total, concluídas sucesso/solução, em reparo, taxa de sucesso %, faturamento, tempo de reparo (dias).

### 2.5 Configurações e perfil
- **CompanySettingsDialog**: logo (BLOB), razão social, CNPJ, nome fantasia, contato, **mensagem de rodapé** e **termos de garantia** (padrão 90 dias) → tabela `company_settings` (UPDATE com fallback INSERT).
- **PerfilWindow** (MySQL): foto (base64, recorte circular), e-mail (só leitura), saldo de créditos, nível, nome, telefone, localização, website, redes sociais, bio (contador), nascimento, visibilidade, notificações.
- **VisualizarPerfilWindow**: modo somente-leitura com badge de nível.

### 2.6 Parceiros e "Minhas Soluções"
- **ParceirosWindow**: vitrine **estática/embutida** (lista fixa com nome, endereço, telefone, Instagram, logo em `app\resources\parceiros`); card abre Instagram. Sem banco — conteúdo editorial.
- **MinhasSolucoesWindow**: CRUD das próprias soluções (marca, modelo, descrição, observações, até 3 imagens, até 2 diagramas) em SQLite `user_solutions_1.db`; filtros, estatísticas, backup/restauração (BackupManager), anti-captura. **Compartilhar** envia à nuvem exige Instagram no perfil, valida hash, aplica limite diário, marca "Compartilhada".

### 2.7 Componentes de UI reutilizáveis
- `solution_filters_widget.py`: filtros por categoria de problema (energia, carregamento, tela, sinal, software, segurança, câmera, áudio, armazenamento, hardware, boot, desempenho, backup, rede, sistema) → conjunto fixo de palavras-chave seguras.
- `image_preview_label.py`: preview 200×200 mantendo proporção.
- `_upd_dialog.py`: diálogo de download/instalação de atualização com worker em thread e execução do instalador no final.

## 3. Diagnóstico Android e ferramentas de bancada
### 3.1 `diagnostico_android.py` (hub em abas)
Abas: Diagnóstico, Motorola, Xiaomi, Samsung, QCOM EDL, SPD, Tira Vírus, Tools/HXD, Exynos (premium/admin), Apps, Monitor. Executa via `ADBManager` em `CommandThread` (lock único por comando, tratamento centralizado de erros ADB).
- **Bateria**: `dumpsys battery` (nível, saúde, temperatura °C, voltagem, tecnologia, fonte), ciclos, ASOC Samsung, reset `batterystats`.
- **Identidade**: `getprop` (marca, modelo, Android, patch, hardware, plataforma, build, fingerprint, baseband, kernel, bootstate/flash lock).
- **Armazenamento**: `df -h` + checagem de blocos → classifica eMMC/UFS. **CPU**: `/proc/cpuinfo` + freq. máxima + `ro.board.platform`. Memória, sensores (`sensorservice`), térmica, WiFi, rede (`connectivity` + `pm list packages -U`), sinal (`telephony.registry`), USB, touch (`getevent -p`), câmera, áudio, eventos (`logcat -t 100 *:E` + uptime), partições.
- **Panic Android**: gera `adb bugreport` (ZIP) com barra de progresso.
- **Logcat ao vivo**: timer 100 ms, coloração por severidade, impressão via `ReportPrinter`; menu: manual ADB, seleção de dispositivo, dependências USB (UsbDk/WinFsp), correção Defender, reinstalação platform-tools, drivers não assinados, scrcpy.

### 3.2 Parsers e formatadores
- `diag_parser_v2.py`: parsers **puros** (sem PyQt/ADB) que convertem saída bruta em dicts — bateria, sinal (dBm por geração RSRP/RSCP/RSSI + barras por SIM), sensores, touch, df, meminfo, térmica, cpuinfo (SoC: Exynos/Snapdragon/Helio/Dimensity/UNISOC), identidade, câmera, WiFi, USB, partições, eventos, rede, áudio. Valida sentinela 2147483647.
- `diag_formatters.py` (v1 legado) e `diag_formatters_v2.py` (canônico): montam texto exibido com cabeçalho/rodapé da marca, barras de sinal, tradução de pacotes.
- `diag_report_pdf.py`: relatório PDF/HTML do diagnóstico com dados de `company_settings`, código datado, seções, assinatura do técnico.

### 3.3 Ferramentas por marca
- `tools_android.py` (aba Motorola): status (modelo, CPU, bootloader, FRP, A/B), desbloqueio de bootloader (site oficial), download firmware (mirror lolinet), remoção MDM, correção "Comm Server", FRP MTK/SPD (beta), **FlashRomDialog** (parseia XML rawprogram/firehose, seleção de partições, flash com progresso).
- `samsung_tools.py`: **aba Padrão** (pyserial COM, factory reset, reboot, Download, IMEI, "Turbo Clean" bloatware, teste de comunicação) + **aba Advanced** (FRP por método: Android 9–10 Exynos, 11+, ADB puro, ROM eng, método "UNION", Android 16, QR codes, FRP por modelo EDL/BROM/MTP, análise, DVIF, FRP por ID/IMEI até Android 14).
- `xiaomi_tools.py`: status MIUI/HyperOS, bootloader, FRP por modelo MTK/SPD, identificação completa, unlock bootloader, bypass anti-rollback, disable DM-Verity, firmware (mifirm.net), remover Mi Cloud/Account, temas de terceiros, desativar anúncios, desativar otimizações, remover OTA, permissões, otimização de bateria, 2 FRP remoto premium.

### 3.4 Tira Vírus (adware)
`adware_tools.py`: coleta overlays, apps do usuário, admins, acessibilidade, boot, APK/DEX soltos, pastas suspeitas; compara com lista embutida + **blacklist JSON** (`blacklist_union_apps_v2.json`); MIUI ads. Modos: tempo real, monitor 60 s, enhanced, "CSI", monitor de tela, "blindar dispositivo", **certificado de proteção em PDF**, gerenciamento USB (reautorizar/reset ADB/regenerar chaves), tutorial (blob MySQL).

### 3.5 UART
- `uart_monitor.py`: pyserial UART para log de boot de placas (não ADB/scrcpy). Auto-detecta baudrate (921600 MediaTek, 115200/230400 Qualcomm), classifica linhas (PLL/clock, PMIC/PWRAP, DDR, GPIO, estágios de boot, motivo de reset), estatísticas, "passos de reparo" sugeridos.
- `_uart_health_widget.py`: cards de subsistemas (bateria, power key, PMIC, RAM, storage, I2C, RTC, CPU, PWRAP, SPMI, clocks, watchdog, ATF/TEE, boot) com badge de estado.

### 3.6 Apps e Monitor
- `adb_app_manager_view.py`: listagem de pacotes (normais e MDM), operações em lote (force-stop, cache, desinstalar, instalar APK, restaurar launcher, congelar, disable-user).
- `adb_system_monitor_view.py`: CPU/RAM em tempo real via `top`, processos (PID/CPU/RAM), kill multi-método, alertas com limiares, exportação, diagnóstico completo.

### 3.7 Downloads e Películas
- **Downloads** (`views\downloads\`, 5 arquivos): DownloadsWindow → CategoriasWindow → ArquivosListaWindow → DetalheArquivoWindow / ArquivoGratuitoDialog. Modelo: id, título, marca, modelo, categoria, tipo (gratuito/pago), preço, tamanho, datas, downloads, avaliação, versão, verificado, solução, descrição, link, WhatsApp. Pagos por **crédito** ou **WhatsApp**; acesso validado por e-mail; cache `DownloadsCache`.
- **Películas** (`peliculas_cache.py` + `peliculas_window.py`): catálogo consultável offline de películas compatíveis; SQLite `pc_data.db` em `%LOCALAPPDATA%\.tus_data\pc`, sync rate-limited 24 h do MySQL (`peliculas_compatibilidade`), busca sem acentos.

## 4. Kit de desbloqueio — `views\union_unlock\`
> **Observação de segurança (clean-room):** todo o módulo é um kit de **bypass FRP/MDM/Knox/Mi Account/PayJoy**. Contorna proteções de conta e política do fabricante por apagamento/patch de partições, payloads que desligam `secure_hardware`, adulteração de `user_setup_complete` e injeção de device owner. **Isto é documentado, NÃO será implementado no clone.** Risco de brick reconhecido pelo próprio código (listas negras de partições, avisos de "MODO DE TESTE").

### 4.1 EDL — Qualcomm (`edl\`, 15 arquivos)
- **Tela** (`edl_main.py`): abas "Auto"/"Manual"/"Partições" + uma aba por marca (Samsung, Xiaomi, Oppo, Vivo, Realme, Honor, Huawei) criada do cache local. Scan de COM a cada 3 s (pyserial, VID `05c6`/PID `9008` QDLoader).
- **Sync/DB** (`edl_sync.py`): SQLite `edl_qcom.db` (modelos, loaders auto por HWID/pkhash, testpoints, auth VIP, cache de ops). Dados de **MySQL remoto** (pymysql via `db_config`), sync 24 h/debounce 30 min; blobs comprimidos (zlib) e cifrados XOR com chave derivada de hostname+MAC. SSL sem verificação de certificado.
- **Auth firehose** (`firehose_ops.py`): envia XML `<sig>` + assinaturas de 256 B (de `edl_auth.get_auth_signatures`, **módulo ausente**). Modos: genérico, Xiaomi, OnePlus (via `fh_loader`), VIP (migrou para `--signeddigests`).
- **Upload loader**: `QSaharaServer.exe -u <porta> -v 0 -s 13:<loader>` ou Sahara nativo (`_qcom_io.py`: HELLO/READ_DATA/END_IMAGE/DONE → Firehose XML configure/read/write/patch/erase/power, payloads até 4 MB).
- **Firehose ops**: GPT, storage info (emmc/ufs/nand, LUNs), leitura/escrita/erase/patch/reset via `fh_loader.exe`, XMLs em `%LOCALAPPDATA%\.union_edl` (hidden+system). Log sanitizado.
- **Parser GPT** (`gpt_parser.py`): "EFI PART", fallback 512/4096, UTF-16LE, classifica critical/safe/caution.
- **FRP por marca**: `frp_samsung.py` (persistent), `frp_xiaomi_auth.py` (frp/userdata + auth), `frp_oppo_vip.py` (VIP 4 passos), `_qcom_io.executar_frp_serial` (VIP2 nativo). Fluxo: detectar porta → upload loader → auth → detectar storage → ler GPT → validar alvo → apagar. Listas brancas/negras rígidas.
- **Mi Cloud** (`micloud_edl.py`): lê `modem`/`NON-HLOS` + `persist`, backup em `Documents\UNION_Backups`, substitui byte-strings de Mi Account por variantes de mesmo tamanho, apaga `frp`/`config`.
- **Auto** (`auto.py`): identifica por HWID `00<msm><oem><model>` + pkhash, mappa chipset (tabela Snapdragon), busca loader em `loaders_auto`, executa FRP por marca. **Manual** (`manual.py`): operador escolhe loader/memória/ferramenta (edl-ng, qcomview). **Partições** (`partitions.py`): dump/gravar/zerar/apagar/reset.

### 4.2 SPD — Spreadtrum/Unisoc (`spd\`)
- **Tela** (`spd_main.py`): abas Operações/Partições, terminal, "Autorização Avancada", "Force" (`--kick`: boot_diag→cali_diag→dl_diag), aviso "MODO DE TESTE — RISCO DE BRICK". Engine nativa desativada (`ENABLE_NATIVE_ENGINE=False`).
- **Detecção** (`device_detect.py`): varredura por VID Spreadtrum e palavras-chave SPRD/SPREADTRUM/UNISOC, classifica por PID.
- **Transporte** (`transport.py`): pyserial, frames HDLC (delimitador 0x7E), fallback raw.
- **Protocolo BSL** (`protocol.py`): check_baud, connect, start/midst/end/exec data, erase, read, enable write, reset. Interpreta ACK/VER/erros. Depende de `constants`/`checksum`/`hdlc` (**ausentes no decomp**).
- **FDL** (`loader.py`): FDL1 com CRC16 → FDL2 com checksum ADD → `enable_flash`. Binários do servidor ou `fdl1-dl.bin`/`fdl2-dl.bin`.
- **Operações** (`operations.py`): erase/write (chunks 1016 B), recovery em `misc`, apagar `persist` (FRP), `userdata`, "FULL FRP REMOVE".
- **Binário** (`bin_spd.py`): encapsula `spd_dump.exe` interativo (stdin/stdout), extrai versões BSL, partições, progresso.
- **GUI** (`partition_tab.py` + `workers.py` + `model_data.py`): marcas/modelos do MySQL (endereços FDL hex, ops JSON, memória), connect via spd_dump, ler/gravar/apagar.

### 4.3 Xiaomi (`xiaomi\` + `sideload\xiaomi\`)
- **`brom_base.py`**: executa **`mtk.exe`** com `e frp,persist,userdata` (opção `--loader`), parseia stdout, taskkill no cancelamento (erro 740 = exigir admin).
- **`edl_base.py`**: executa **`edl.exe`** com `e <partição> --loader <loader> --memory=emmc`.
- **`xiaomi.py`**: container/lista com busca → widgets de modelo + Fastboot FRP.
- **`xiaomi_fastboot_frp.py`**: casca do `FastbootFrpWidget`.
- **Modelos específicos** (~40 arquivos, não detalhados): `redmi_9/9c/9a/10a/10_2022/12c/13c/14c/15c/12_fire/a1/a1_plus/a2/a3/note8pro/note9/note10_5g/note10s/note11s/note_12s`, `poco_c50/c55/m3_pro/m4_pro_4g/m4_pro_5g` + pastas `*_mods` — todos sobre `mtk.exe`/`edl.exe`.
- **Sideload** (`xiaomi_sideload_gui.py`): ADB sideload/recovery — format-data, factory reset, wipe cache, reboot, "Mi Bypass" (extrai `persist`+modem via `adb pull`, substitui strings com `replace.exe`, regrava, empurra `frp`).

### 4.4 Samsung (`samsung\`)
- **`samsung.py`**: sidebar de busca + `QStackedWidget`; ~25 modelos na UI (A02–A32, A05s×3, A055M B13 [TP], A12, A20s, A22 5G, A23×3, S20 FE G780G/G781B, Tab A T295, "Galaxy Android 16 (Todos)"); ~27–35 arquivos de modelo + `*_mods`.
- **BROM** (MediaTek, ex. A05): valida `mtk.exe` + script do modelo (`galaxy_a05.exe`), test point, worker roda `mtk.exe e persistent` + script, streaming de stdout. Aviso "SEC Ctrl = 0 / eFuse queimado".
- **EDL** (Qualcomm): (a) `edl_frp_worker.py` → `FRP_EDL.exe -m ufs -l <loader .elf> resetfrp`; (b) Tab A T295 usa ferramenta genérica (`--loader ... --memory Sdcc erase-part persistent` + reset, loader `t295_prog_emmc_firehose_8937.mbn`). Test point obrigatório.
- **MTP "Galaxy Android 16"** (`mtp_all_android_16.py`): (1) habilitar ADB via `ATCommandConsole.exe`, (2) push `base.apk`+`classes.dex` para `/data/log/` + `app_process` (classe "Exploit") com `nc -lp 1234`, (3) `dd if=/dev/zero` em `by-name/frp`+`persistent` (ou via `com.shell` com `nc -lp 8080`).

### 4.5 Motorola (`moto\`)
- **`motorola.py`**: 12 entradas (E6s, E7, E7 Power, E22, E22i, G05, G06, G15, G17, G22, MDM SPD/MTK, Moto Antigos) + `*_mods`.
- **BROM por modelo**: `mtk.exe e frp [--loader <Moto-X.bin>]` (loader próprio: `Moto-E22.bin`, `Moto-G05.bin`, etc.).
- **FRP antigos** (`moto_frp_old.py` / `frp_old.py`, "Factory Mode"): descobre aparelho em factory via IPs fixos (192.168.137.2, 192.168.42.129/1, 192.168.1.1) + `arp -a`, testa TCP 11000, injeta payloads binários ("karnel") por socket (um contém `androidboot.secure_hardware=0`), ativa ADB (5555), conclui marcando `user_setup_complete` e reinicia.
- **MDM** (`mdm_spd_mtk.py`): "Fastboot Mode" — `fastboot flash userdata`/`cache` com `empty_file` + reboot.

### 4.6 hxd — editor de partições
- **GUI** (`main_widget.py`): abas; engines `proinfo`, `oeminfo`, `persist`, `oplus`, `protect1`, `miscdata` (alguns só `.pyd`); backup antes; disclaimer de brick. **`log_seguro.py`** sanitiza (mascara hex, trunca caminhos).
- **`core\validador.py`**: valida por tipo com faixas de tamanho. **`core\backup_manager.py`**: timestamp → `Documents\UNION_HXD_Backups`.
- **`oplus_engine.py`**: parser OPPO/OnePlus/Realme (nVersion/nProject/nDtsi/nPCB/eng_version, MACs, IP), classifica MTK vs Qualcomm.
- **`protect1_engine.py`**: analisa imagem ext4 (inodes/blocos/SELinux), determina BLOQUEADO/DESBLOQUEADO; "patch" substitui por template embutido e **reescreve timestamps de inodes** (evasão).
- **`newsec_engine.py`** ("SPD/MTK New Sec 2026"): via ADB desinstala OTA, bypass Knox/KG (`com.samsung.android.kgclient`) ou `com.scorpio.securitycom`, remove apps MDM, instala `techunion_admin.apk` + `dpm set-device-owner`, bloqueia factory reset, força Private DNS NextDNS. `fix_playstore` equivalente.
- **`moto_frp_engine.py` + `moto_frp_sync.py`**: FRP Moto via fastboot — vars, baixa imagens **LK** do servidor (`moto_frp_lks` via MySQL), gera chave MFK local do serial+lote, grava/restaura LK, `oem unlock <chave>` + `erase frp`. Cache SQLite cifrado (XOR da máquina+zlib+base64), sync 24 h.

### 4.7 mit (MediaTek META) / dmiti (UNISOC) / exy (Exynos)
- **`mit\`**: `mit_engine.py` acha portas VCOM META (pyserial), boot para META, handshake, ops (read info, hw diagnostics: bateria/temp/corrente, erase FRP, factory reset, remove PayJoy). `mit_engine_2026.py` adiciona segredos SLA embutidos (`METAMETA`/`SLASTART`, variantes "nosha"/"Tecno"), escrita BCB, reset 08/2026. `mit_partition_engine.py` lê GPT via META e faz read/write/erase com backups. Binários verificados por SHA-256. GUIs `mit_widget.py`, `mit_partition_widget.py`.
- **`dmiti\`** (Itel/Tecno/Infinix): engine de diag serial (frames, init, privilege elevate, AT), ops (read info, factory reset, enable ADB, reboot, remove PYJ, "sec_plugin" que patcha setores de segurança). `_dmiti_partition_core.py`+`dmiti_partition_engine.py` dão backup/gravação/zerar via diag. Também instala `techunion_admin.apk`+device owner+NextDNS.
- **`exy\`** (Samsung Exynos, "TESTE"): detecção WMI (modem Samsung/COM), ações (detectar, reboot download, enable ADB, "ADB + FRP One-Click", remover FRP via ADB). Coração: **`ExynosBridgeHost.exe`** (CLI com senha por argumento/env `_EXY_K`, porta COM + preset JSON por chipset); `exynos_tools_loader.py` extrai ferramentas e **adiciona exclusões no Defender**; `preset_manager.py`+`exynos_sync.py` sincronizam presets (`exynos_presets` no MySQL, JSON cifrado em SQLite local).

### 4.8 flash / honor / fmgr
- **`flash\motorola`**: flash fastboot com seleção de partições, verificação/restauração de `fastboot.exe` (de `tools_backup.zip`), sanitização, detecção de device locked/anti-rollback.
- **`flash\samsung`**: chama **`odin4.exe`** com slots BL/AP/CP/CSC, MD5, verificação/restauração do Odin.
- **`flash\xiaomi`**: fastboot `flash_all`/`flash_all_except_data_storage`/`flash_all_lock` (`.bat`).
- **`honor\`**: `honor_frp_engine.py` lê info via fastboot e aplica unlock com **chave fornecida pelo usuário**, gerada no site Tech Union Services a partir da serial.
- **`fmgr\`**: file manager sobre imagens de partição (`fmgr_engine.py`: ext4/erofs/raw/sparse/NVRAM, listagem, cópia, permissões, auditoria ext4, anti-sensível de DLLs/subprocessos), `fmgr_widget.py` (editor hex, backup), `nvram_parser.py` (indexa LDI, extrai IMEIs BCD+Luhn com tentativa de decrypt AES, Wi-Fi/BT/serial).

### 4.9 Binários externos do unlock
`mtk.exe`, `edl.exe`, `edl-ng.exe`, `FRP_EDL.exe`, `emmcdl.exe`, `qcomview.exe`, `QSaharaServer.exe`, `fh_loader.exe`, `spd_dump.exe`+`Channel9.dll`, `ATCommandConsole.exe`, `ExynosBridgeHost.exe`, `odin4.exe`, `adb.exe`/`fastboot.exe`/`fastboot2.exe`, `replace.exe`, `ext4.dll`/WinFsp, `powershell`, `taskkill`; scripts por modelo `galaxy_*.exe`; recursos: loaders ELF/mbn, `techunion_admin.apk`, `base.apk`+`classes.dex`, `empty_file`, `persist*.img`, fdl1/fdl2. Boxes detectados por processo (Octoplus, UMT, NCK, SamFW, QPST, MiFlash, Easy JTAG, Medusa, Chimera, Z3X, Miracle).

### 4.10 Lacunas do decomp em unlock
Ausentes (só `.pyd` ou nunca distribuídos): `edl_auth.py`, `spd\constants.py`, `checksum.py`, `hdlc.py`, `spd_sync.py`, `app\utils\_app_cfg.py` (creds MySQL/REFS). Alguns engines hxd (proinfo/oeminfo/miscdata) só `.pyd`.

## 5. Camada de infraestrutura (`utils\`)
### 5.1 Gerenciadores de dispositivo
- **adb_manager.py** (singleton, 3.760 linhas com trechos duplicados 4× por ofuscação): localiza/valida `adb.exe`+`fastboot.exe` (dir local, `C:\platform-tools`, PATH, Program Files), detecta bloqueio Defender (erro 3221225477), **baixa platform-tools do repositório oficial do Google**, reinicia servidor adb, regenera chaves, aguarda autorização, coleta bateria/rede/logcat, reboot, bootloader unlock via fastboot, `pm grant`, kill de processos, parser de `adb devices -l`.
- **adb_app_manager.py**: apps sem root (Android 9–14) — lista (`pm list packages` + `dumpsys package`), force-stop, cache (modo inteligente para navegadores), dados, instala/desinstala APK, congela/descongela, busca por tipo.
- **adb_system_monitor.py**: `top -n 1 -b`, `ps -A`, `/proc/stat|meminfo|loadavg|<pid>/*`, histórico em deque, níveis de alerta, identificação por getprop, bateria/wi-fi.
- **mtk_manager.py**: extrai ZIP **AES-256** (chave `REFS.PK_Z`) para temp aleatório, executa `MTK_TOOLS_V1.3.4.exe`, auto-limpeza (`.union_cache/mtk`), fallback a `C:\Python39..313` para GUIs .py.
- **frp_mtk_manager.py**: mesmo padrão para `frp_erase_xiaomi.py` (spawn via pythonw, sem janela).
- **samsung_manager.py**: pyserial COM Samsung, autodetect baudrate (115200/9600/38400), comandos AT.
- **samsung_advanced.py** (1.807 linhas): detecção por VID Samsung (04E8), comando proprietário **DVIF**, testes AT, FRP bypass por versão (Android 9/10, 11+, "FRP recovery union", Android 16 métodos 1 e 2), continuação via ADB (push, root, zeros na FRP).
- **samsung_android16_frp.py**: método "definitivo" (Galaxy Tab S9 FE), não exige ADB pós-reset; porta série Samsung + APK base64 + fases de init/instalação/reset.
- **xiaomi_manager.py**: ADB — info MIUI/HyperOS, bootloader/conta, porta diag (setprop USB diag), token `/data/miui/unlock_token`, unlock rápido, remove anúncios MIUI, anti-rollback, HAL3, `getvar`/disable-verity, remove apps Xiaomi, flash recovery; cache TTL 60 s.
- **os_manager.py**: servidor web local **"Union OS" (Flask)** — LOCAL (127.0.0.1) / REDE (0.0.0.0), porta 5000, provisiona runtime Python embutido (`union_os_runtime.zip`), token **HMAC** (segredo fixo), mata processos da porta, detecta cache de películas.
- **unlock_tools_manager.py**: extrai `unlock_tools.zip` (AES `REFS.PK_Z`) para `union_unlock\tools`, garante mtk.exe/emmcdl.exe/adb.exe/edl-ng.exe, limpa ao fechar.
- **tools_android.py**: `FastbootManager` + Motorola (dados de unlock, correção "comm server", flash ROM stock por XML, MDM, bootloader, dm-verity, conta Xiaomi).

### 5.2 Backup / relatórios / compartilhamento / correção
- **backup_manager.py**: backup/restauração ZIP de `service_orders.db`+`user_solutions_1.db`, progresso, verificação PRAGMA, backup pré-operación, README no ZIP, códigos BR-001..BR-006, correção de dono/user_id (lê id no MySQL), detecção de "email irmão".
- **report_printer.py**: relatórios (log do sistema, bateria) HTML→PDF A4 via QPrinter, cabeçalho/rodapé da empresa (fallback TECH UNION SOLUTIONS).
- **compartilhamento_seguro.py**: compartilha soluções no MySQL — converte e-mail→id, perfil (instagram), cota diária, evita duplicatas em `minhas_solucoes`, insere com blobs, flags aprovação/visibilidade.
- **correcao_wdef.py**: detecção/correção de bloqueio Defender sobre ADB — PowerShell oculto com timeouts, sanitização agressiva (nenhum detalhe técnico vaza), detecta antivírus, verifica ADB bloqueado (0xC0000005), adiciona exclusões, remove mitigações de Exploit Protection, restaura da quarentena (Get-MpThreat/Remove-MpThreat), baixa platform-tools frescos; trata adb, fastboot, mtk, edl, FRP_EDL, emmcdl, fh_loader, ATCommandConsole, ExynosBridgeHost.

### 5.3 Adware
- **adware_advanced_detector.py**: detector comportamental com pontuação — overlays, admins, boot, acessibilidade, CPU, permissões, netstat, serviços, bateria, logcat; blacklist JSON (`blacklist_union_apps_v2.json`), lista de confiança, permissões perigosas, adware de fabricante (`_pkg_defs`).
- **adware_csi.py**: forense "CSI" — instalação ≤10 dias, abuso de foreground/bateria/overlay/acessibility/boot, combinações perigosas com bônus, varredura logcat por SDKs de anúncios, triagem por limiar.
- **adware_hardening.py**: reforço reversível sem elevação — liga verificador de pacotes (`package_verifier*`), restringe instalação de origens externas via `appops` (mantém lojas oficiais), ou `install_non_market_apps=0` (SDK ≤25).

### 5.4 scrcpy / USB / navegador / QR / pacotes
- **scrcpy_manager.py**: QProcess isolado, cooldown, timeout 120 s, extrai scrcpy de ZIP AES (pyzipper), env `SCRCPY_SERVER_PATH`, atexit.
- **usb_requirements_manager.py**: instala UsbDk/WinFsp (winget→GitHub MSI→msiexec silencioso), drivers (MTK VCOM, QDLoader 9008, SPD/Unisoc) via `pnputil /enum-drivers`, VC++ Redist, .NET 8 (aka.ms/builds.dotnet), lista dispositivos via `UsbDkController.exe`, abre Gerenciador de Dispositivos.
- **web_view_widget.py**: navegador interno QWebEngineView (home mifirm.net, inicial google.com, abertura externa opcional).
- **samsung_qrcode_viewer.py**: consulta assíncrona ao MySQL (título contém "qrcode"), mostra thumbnail/blob em diálogo.
- **_pkg_defs.py**: proteção de pacotes em 3 camadas (launcher ativo via `resolve-activity`, todos com HOME, lista estática); cruza com `test.json` (base UAD-ng, remove "Unsafe"/"Expert"); adware de fabricante MIUI/Xiaomi. `pkg_utils.py`/`adb_pkg_utils.py` variações.

### 5.5 Banco de dados e caches
- **Schemas** (`db-schemas.txt`, 5 SQLite):
  - `base.db`: `solucoes` (marca, modelo, descrição, observações, status, blobs diagrama/imagem ×3, hash, versão) — **2.562 linhas**; `sync_control` — **1.454 linhas**.
  - `service_orders.db`: `users`, `clients`, `service_orders`, `service_order_photos`, `knowledge_base`+attachments, `company_settings` (garantia padrão 90 dias) — vazias.
  - `user_solutions_1.db`: `user_solutions` (vazia).
  - `servidor_arquivos_cache.db`: `cache_servidor_arquivos` (**305**), `cache_marcas_resumo` (**14**), `cache_categorias`, `cache_arquivos_populares`, `cache_sync_control`, `cache_config`, `cache_estatisticas`.
  - `app.db` (ordem_servico/instance): sem tabelas (Flask/Alembic, `alembic.ini` presente).
- **Caches por espelho do MySQL**: `downloads_cache.py` (WAL, backup, recuperação; 15 dias, só metadados), `conteudos_widget_cache.py` (sync 5 min), `peliculas_cache.py` (24 h), `implementar_cache_servidor_arquivos.py` (timeout 15 min), `servidor_arquivos_cache_manager.py` (timeout 21600 min; lotes, resumos por marca, top 100, remove inativos).
- **Migrations** (`database\migrations\`): `001_initial.py` cria `company_settings`; `add_warranty_text.py` idempotente (PRAGMA + ALTER TABLE); `run_migrations.py` executa lista ordenada.
- **`database_manager.py`** (só decrypted): SQLite `base.db` com soluções + login local com senha **SHA-256 sem salt** (tabela `users`); `solucoes_window.py` é a UI.

### 5.6 Config e dados embutidos (Fase 3)
- `database\.key` = chave base64 32 B (`6doKwDJrTMBjPKig0u4rBgEaW57vjxY9vq06MxuBbwU=`).
- `ordem_servico\.env` (Flask dev): `SECRET_KEY`, `DATABASE_URL=sqlite:///data/os_system_dev.db`, `COMPANY_NAME=RestoreCell`, `COMPANY_CNPJ=00000000000000`, `SYSTEM_NAME="Union OS Manager"`.
- SSL self-signed `ssl\cert.pem`/`key.pem` (CN=localhost, BR/SP, RestoreCell).
- `translations\pt.py`/`en.py`/`es.py`: dict `translations` (pt 23 KB, centenas de chaves de UI PT-BR).
- **Não existe `.env`/`.key` no root do app** (só nos subprojetos acima) — verificado.
- Binários externos (mtk.exe, edl-ng.exe, fh_loader, QSaharaServer, spd_dump, odin4, adb/fastboot, scrcpy, ExynosBridgeHost) em ZIPs **AES protegidos por `REFS.PK_Z`** (chave no `.pyd`).

## 6. Integrações externas (inventário único)
> Para o SPEC: o clone **não** deve reproduzir esses endpoints/servidores. Servem apenas para entender o que o app original fazia. Credenciais ficam no `.pyd` não descompilado.

### 6.1 API de licenças (Keygen)
- `REFS.VK_URL` (de `_app_cfg.py`, não no decomp): `/accounts/{acc}/licenses/actions/validate-key`, `/licenses/{id}/machines`, `/machines`; JSON:API + Bearer do produto. Mais `LIC_RENEW_URL`, `LIC_SUPPORT_WHATSAPP`.

### 6.2 MySQL remoto (pymysql, SSL sem verificação de certificado; host/senha no `.pyd`)
Tabelas citadas: `usuarios`, `perfil`, `configuracoes`, `solucoes`, `minhas_solucoes`, `conteudos_dinamicos`, `conteudos_interacoes`, `servidor_arquivos`, `peliculas_compatibilidade`, `loaders`, `loaders_auto`, `moto_frp_lks`, `exynos_presets`.

### 6.3 SQLite local
`base.db`, `service_orders.db`, `user_solutions_1.db`, `downloads_cache.db`, `servidor_arquivos_cache.db`, `edl_qcom.db`, `pc_data.db` (películas), `app.db` (Flask), `users_path` (login local), + cache Fernet `%LOCALAPPDATA%\TechniciansUnion\cache`.

### 6.4 Domínios / URLs / IPs
- **Oficiais**: restorecellsolucoes.com, techunionservices.com. **Suporte**: wa.me/558594129977, wa.me/5585997507465, instagram.com/restorecell10, youtube.com/@RestorecellST e @ramoncell, linktr.ee/techunionsolutions. Telefones (85) 9412-9977 / 99750-7465.
- **Firmware/downloads**: mifirm.net, samfw.com, lgrom.com, ipsw.me, mirrors.lolinet.com.
- **Dependências**: dl.google.com (platform-tools), adb.clockworkmod.com (drivers), github.com/daynix/UsbDk, github.com/winfsp/winfsp, aka.ms (vc_redist), builds.dotnet.microsoft.com (.NET 8).
- **Motorola**: en-us.support.motorola.com, motorola-global-portal.custhelp.com.
- **DNS/serviço**: **NextDNS `a687f8.dns.nextdns.io`** (Private DNS forçado por newsec_engine e dmiti_engine; config key `4641d586b3d0c165a1c5d52a4372545e`), one.one.one.one (teste de VPN).
- **IPs/fabrication mode (Moto)**: 192.168.137.2, 192.168.42.129/1, 192.168.1.1; TCP 11000 (payloads), 5555 (ADB TCP), `nc -lp 1234`/`8080` no aparelho. **DNS públicos p/ teste**: 8.8.8.8, 8.8.4.4, 1.1.1.1.
- **Honor**: `techunionservices.com/service/honor-frp-key-ww-via-sn-maximo-24-hrs-usuarios-union`.
- **Union OS**: Flask em 127.0.0.1:5000 (rede 0.0.0.0:5000).

### 6.5 Armazenamento QSettings (Windows registry)
"TechUnion"/"UNION" (tema, dashboard_v2), "UNION TECHNICAL"/"License", "TECHNICIANS UNION"/"Login", "Union"/"ServiceOrderSystem" (idioma).

## 7. Segredos e mecanismos hardcoded (documentar, NÃO implementar)
- **API Keygen** (`_app_cfg.py`/`.pyd`): URL/account/produto/token.
- **MySQL** host/senha: em `db_config` do `_app_cfg.pyd` — não em texto plano.
- **`REFS.PK_Z`**: chave de descriptografia dos ZIPs AES-256 (unlock_tools, MTK_TOOLS, scrcpy) — no `.pyd`.
- **os_manager.py**: segredo HMAC-SHA256 fixo `TUS_OS_INTEGRATED_2025` para token do subprocesso Flask.
- **database\.key**: chave base64 32 B.
- **ordem_servico\.env**: Flask SECRET_KEY + CNPJ.
- **mit_engine_2026.py**: segredos SLA MediaTek embutidos (bytes/b64, variantes "nosha"/"Tecno").
- **protect1_engine.py**: template de partição embutido (base64+zlib) + reescrita de timestamps de inodes (evasão).
- **exy**: senha da CLI Exynos via argumento/env `_EXY_K` + exclusões automáticas do Defender.
- **database_manager.py**: senha local SHA-256 **sem salt**.
- **samsung_android16_frp.py / newsec_engine / dmiti**: APK/explot embutido em base64 (`techunion_admin.apk`, `base.apk`+`classes.dex`).
- **Mecanismos anti-análise/ofuscação**: import hook, SectorSentinel, `_cfg_probe` (detecção de debugger/VM, self-cleanup), sanitização agressiva de logs (`log_seguro`, `_LOG_BLOCK_*`), cache cifrado por máquina, Anti-captura (WDA_EXCLUDEFROMCAPTURE).

## 8. Pendências / lacunas conhecidas
- Módulos só `.pyd` (não descompiláveis por esta via): `_app_cfg.py` (creds), engines hxd (proinfo/oeminfo/miscdata), `_security_crypto` (já contornado por Ghidra).
- Módulos ausentes: `edl_auth.py`, `spd\constants|checksum|hdlc.py`, `spd_sync.py`, corpo do `_import_hook.py`.
- 166/310 decompilações marcadas "incomplete" pelo pycdc (limitação p/ Python 3.13) — código utilizável, conferir trechos críticos ao especificar.
- Controllers (`login_controller`, `main_controller`) são template Tkinter não relacionado — ignorar.
- **Análise dinâmica do `.pyd` desnecessária** (crypto resolvida por estática). Regra mantida: nunca executar o `.exe` do alvo fora de sandbox; avisar antes de análise dinâmica (sugerir VM).
