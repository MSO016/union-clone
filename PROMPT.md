# PROMPT DO PROJEITO — Engenharia Reversa → Clone (referência para retomada)

> Salvo de/user em 2026-10-27. Usar como roteiro nas retomadas.

## OBJETIVO
Fazer engenharia reversa do aplicativo abaixo para entender TODAS as suas funcionalidades e construir, do zero, um aplicativo próprio equivalente (uso pessoal).

## ALVO
- Pasta: `D:\MSO\Downloads\union_v1.3.4.5-17-09-2026-BT08U`
- Executável: `D:\MSO\Downloads\union_v1.3.4.5-17-09-2026-BT08U\union_v1.3.4.5-17-09-2026-BT08U.exe`

## FERRAMENTAS
- REA via MCP + Ghidra: `C:\Tools\Ghidra\ghidra_12.1.4_PUBLIC`
- Se algum MCP/ferramenta não responder: informar exatamente o que falhou e seguir com o que estiver disponível, sem parar.

## REGRAS
1. Autonomia: usuário define o "o quê"; eu decido o "como" técnico.
2. **Clean-room**: análise → ESPECIFICAÇÃO de comportamento → implementação própria. NUNCA colar código decompilado no projeto final.
3. NÃO implementar bypass de licença, ativação, DRM ou anti-cheat. Se existir verificação de licença: documentar e deixar como config/stub.
4. NÃO executar o .exe fora de sandbox. Análise dinâmica só avisando antes e sugerindo VM/sandbox.
5. NUNCA modificar os arquivos originais; trabalhar em cópias (`D:\MSO\Projects\union-clone\`).

## FASES (executar todas em sequência, sem pedir confirmação entre elas)
1. **TRIAGEM**: tecnologia (nativo/.NET/Electron/Python/Java...), compilador, packers/proteções, arquitetura, dependências (DLLs, assets, configs, recursos), bibliotecas de terceiros, versão.
2. **INVENTÁRIO**: strings, imports/exports, recursos (ícones, UI, textos), chamadas de rede (URLs, endpoints, portas, protocolos), arquivos/registro/banco lidos e escritos.
3. **MAPA DE FUNCIONALIDADES**: a partir do entry point e handlers de UI, mapear cada funcionalidade, fluxo de telas, entradas, saídas, regras de negócio. Renomear funções importantes no Ghidra com nomes legíveis.
4. **ESPECIFICAÇÃO**: gerar `SPEC.md` com funcionalidades, fluxos, formatos de dados/arquivos, protocolos de rede, configurações, e o que NÃO foi possível determinar (confiança: alto/médio/baixo).
5. **ARQUITETURA**: propor stack e estrutura. Se o usuário não indicar: escolher a mais adequada e justificar em 3 linhas.
6. **IMPLEMENTAÇÃO**: app completo, arquivos inteiros (nunca trechos/diffs), dependências, instruções de build/execução e script de setup.
7. **VERIFICAÇÃO**: comparar clone × SPEC; listar igual / parcial / ausente.

## ENTREGAS
- `REPORT.md` (triagem + inventário + limitações)
- `SPEC.md` (especificação funcional)
- Projeto completo do app, executável pelo comando indicado
- `CHECKLIST.md` (funcionalidade × status)

## BLOQUEIOS
Listar TODAS as pendências de uma vez no final (não perguntar uma a uma) e entregar o máximo possível até lá.

## Campos do usuário (ficaram em branco no prompt)
- O que o app faz: ___
- Stack desejada: ___ ("você escolhe" por padrão)
- Plataforma alvo: ___
- Prioridades de funcionalidade: ___
- Depende de servidor/conta online: ___
