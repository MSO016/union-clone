import os
from .._cfg import (_OP_BLOCO, _OP_OVERLAP, _OP_RE_NVERSION, _OP_RE_NPROJECT, _OP_RE_NDTSI, _OP_RE_NAUDIO, _OP_RE_NRF, _OP_RE_NPCB, _OP_RE_ENG_VER, _OP_RE_CONFIDENTIAL, _OP_RE_NPRJ, _OP_RE_ROM_BUILD, _OP_RE_ROM_VERSION, _OP_RE_FAB, _OP_RE_CDT_LINHA, _OP_RE_Q_PROJECT, _OP_RE_Q_PCB, _OP_RE_Q_BOARD, _OP_RE_Q_CDT)
def _primeiro_match(pattern, dados: bytes, grupo: int=1) -> str | None:
    m = pattern.search(dados)
    if not m:
        return
    try:
        g = m.group(grupo)
        if g:
            return g.decode('utf-8', 'replace').strip()
    except Exception:
        return
class OplusEngine:
    @staticmethod
    def ler_info(caminho: str, cb_progresso=None) -> dict:
        resultado = {'erro': None, 'tamanho': 0, 'nVersion': None, 'nProject': None, 'nPrj': None, 'nDtsi': None, 'nAudio': None, 'nRF': None, 'nPCB': None, 'eng_version': None, 'confidential': None, 'q_project': None, 'q_pcb': None, 'q_board': None, 'q_pcb_label': None, 'plataforma': None, 'rom_builds': [], 'rom_version': None, 'fab_id': None, 'fab_nv': None, 'fab_tool': None, 'fab_mac': None, 'fab_ip': None, 'fab_time': None, 'cdt_raw': []}
        try:
            tamanho = os.path.getsize(caminho)
            resultado['tamanho'] = tamanho
            with open(caminho, 'rb') as f:
                lido = 0
                tail = b''
                while True:
                    chunk = f.read(_OP_BLOCO)
                    if not chunk:
                        break
                    dados = tail + chunk
                    lido += len(chunk)
                    if not resultado['nVersion']:
                        resultado['nVersion'] = _primeiro_match(_OP_RE_NVERSION, dados)
                    if not resultado['nProject']:
                        resultado['nProject'] = _primeiro_match(_OP_RE_NPROJECT, dados)
                    if not resultado['nPrj']:
                        resultado['nPrj'] = _primeiro_match(_OP_RE_NPRJ, dados)
                    if not resultado['nDtsi']:
                        resultado['nDtsi'] = _primeiro_match(_OP_RE_NDTSI, dados)
                    if not resultado['nAudio']:
                        resultado['nAudio'] = _primeiro_match(_OP_RE_NAUDIO, dados)
                    if not resultado['nRF']:
                        resultado['nRF'] = _primeiro_match(_OP_RE_NRF, dados)
                    if not resultado['nPCB']:
                        m = _OP_RE_NPCB.search(dados)
                        if m:
                            g = m.group(1) or m.group(2)
                            if g:
                                resultado['nPCB'] = g.decode('utf-8', 'replace')
                    if not resultado['eng_version']:
                        resultado['eng_version'] = _primeiro_match(_OP_RE_ENG_VER, dados)
                    if not resultado['confidential']:
                        resultado['confidential'] = _primeiro_match(_OP_RE_CONFIDENTIAL, dados)
                    for m in _OP_RE_ROM_BUILD.finditer(dados):
                        v = m.group(1).decode('utf-8', 'replace')
                        if v not in resultado['rom_builds']:
                            resultado['rom_builds'].append(v)
                    if not resultado['rom_version']:
                        resultado['rom_version'] = _primeiro_match(_OP_RE_ROM_VERSION, dados)
                    if not resultado['fab_nv'] and b'download over' in dados:
                        m_dl = _OP_RE_FAB.search(dados)
                        if m_dl:
                            resultado['fab_id'] = m_dl.group(1).decode('utf-8', 'replace')
                            resultado['fab_nv'] = m_dl.group(2).decode('utf-8', 'replace')
                            resultado['fab_tool'] = m_dl.group(3).decode('utf-8', 'replace').strip()
                            macs = m_dl.group(4).decode('utf-8', 'replace').strip().split(';')
                            resultado['fab_mac'] = ' | '.join((x.strip() for x in macs if x.strip()))
                            resultado['fab_ip'] = m_dl.group(5).decode('utf-8', 'replace')
                            resultado['fab_time'] = m_dl.group(6).decode('utf-8', 'replace')
                    if not resultado['q_project']:
                        resultado['q_project'] = _primeiro_match(_OP_RE_Q_PROJECT, dados)
                    if not resultado['q_pcb']:
                        resultado['q_pcb'] = _primeiro_match(_OP_RE_Q_PCB, dados)
                    if not resultado['q_board']:
                        resultado['q_board'] = _primeiro_match(_OP_RE_Q_BOARD, dados)
                    if not resultado['q_pcb_label']:
                        m_cdt = _OP_RE_Q_CDT.search(dados)
                        if m_cdt:
                            resultado['q_pcb_label'] = m_cdt.group(4).decode('utf-8', 'replace')
                            if not resultado['nAudio']:
                                resultado['nAudio'] = m_cdt.group(2).decode('utf-8', 'replace')
                    if len(resultado['cdt_raw']) < 6:
                        for m in _OP_RE_CDT_LINHA.finditer(dados):
                            linha = m.group(0).decode('utf-8', 'replace').replace('\r', '').strip()
                            if not linha:
                                continue
                            if linha not in resultado['cdt_raw']:
                                resultado['cdt_raw'].append(linha)
                    tail = dados[-_OP_OVERLAP:]
                    if cb_progresso and tamanho > 0:
                        cb_progresso(min(lido / tamanho, 1.0))
        except PermissionError:
            resultado['erro'] = 'Sem permiss├úo para acessar o arquivo.'
        except Exception:
            resultado['erro'] = 'Erro ao processar a parti├º├úo.'
        try:
            if not resultado['nProject']:
                if resultado['q_project']:
                    resultado['nProject'] = resultado['q_project']
                    resultado['plataforma'] = 'Qualcomm'
            if not resultado['nPCB']:
                if resultado['q_pcb']:
                    resultado['nPCB'] = resultado['q_pcb']
            if not resultado['nPCB']:
                if resultado['q_pcb_label']:
                    resultado['nPCB'] = resultado['q_pcb_label']
            if not resultado['plataforma']:
                if any((resultado.get(k) for k in ('nVersion', 'nDtsi', 'eng_version', 'confidential'))):
                    resultado['plataforma'] = 'MediaTek'
                    return resultado
                if resultado.get('q_board'):
                    resultado['plataforma'] = 'Qualcomm'
        except PermissionError:
            resultado['erro'] = 'Sem permiss├úo para acessar o arquivo.'
        except Exception:
            resultado['erro'] = 'Erro ao processar a parti├º├úo.'
        return resultado
        return resultado
