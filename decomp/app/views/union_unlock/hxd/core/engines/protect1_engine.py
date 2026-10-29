'''
Engine de leitura e patch da parti├º├úo protect1 (SIM Lock).
Fabricante: MediaTek ÔÇö Realme / OPPO / OnePlus / Xiaomi MTK / Tecno / Infinix
Opera├º├úo: substitui├º├úo do filesystem EXT4 por template limpo
Risco: ALTO ÔÇö opera├º├úo destrutiva, substitui todo o filesystem
Mensagens de retorno s├úo amig├íveis e NUNCA exp├Áem offsets ou valores hex.
'''
import os
import time
import zlib
import struct
import base64
from .._cfg import (_PT_TAM, _PT_MG_OFF, _PT_MG_VAL, _PT_SB_OFF, _PT_BSZ, _PT_LABEL, _PT_MOUNT, _PT_INODES_LOCK, _PT_INODES_CLEAN, _PT_LABELS_MIN)
_TEMPLATE_B64 = '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'
def _reconstruir_template() -> bytes:
    '''Reconstr├│i a imagem EXT4 limpa de 8 MB a partir do template comprimido.'''
    raw = zlib.decompress(base64.b64decode(_TEMPLATE_B64))
    n_entries = struct.unpack_from('<I', raw, 0)[0]
    img = bytearray(_PT_TAM)
    off = 4
    for _ in range(n_entries):
        idx = struct.unpack_from('<I', raw, off)[0]
        off += 4
        img[idx * _PT_BSZ:(idx + 1) * _PT_BSZ] = raw[off:off + _PT_BSZ]
        off += _PT_BSZ
    try:
        _atualizar_timestamps(img)
    except Exception:
        pass
    return bytes(img)
def _atualizar_timestamps(img: bytearray) -> None:
    '''
    Atualiza timestamps dos inodes ativos para o momento atual.
    Dispositivos MediaTek podem rejeitar um filesystem cujos timestamps
    estejam defasados em rela├º├úo ao patch de seguran├ºa vigente. Esta
    fun├º├úo garante que cada inode reflita a data de execu├º├úo do patch,
    mantendo coer├¬ncia temporal com o firmware do aparelho.
    Tamb├®m substitui ocorr├¬ncias dos timestamps antigos no journal,
    evitando res├¡duos que possam disparar verifica├º├úo de integridade.
    '''
    agora = int(time.time())
    ts_bytes = struct.pack('<I', agora)
    sb = img[_PT_SB_OFF:_PT_SB_OFF + 1024]
    inode_size = struct.unpack('<H', sb[88:90])[0]
    total_inodes = struct.unpack('<I', sb[0:4])[0]
    block_size = 1024 << struct.unpack('<I', sb[24:28])[0]
    bg_inode_table = struct.unpack('<I', img[block_size + 8:block_size + 12])[0]
    it_off = bg_inode_table * block_size
    it_end = it_off + total_inodes * inode_size
    old_timestamps = set()
    for i in range(total_inodes):
        i_off = it_off + i * inode_size
        mode = struct.unpack('<H', img[i_off:i_off + 2])[0]
        if mode == 0 or mode == 65535:
            continue
        for field_off in (8, 12, 16):
            val = struct.unpack('<I', img[i_off + field_off:i_off + field_off + 4])[0]
            if val > 1000000000:
                old_timestamps.add(struct.pack('<I', val))
        img[i_off + 8:i_off + 12] = ts_bytes
        img[i_off + 12:i_off + 16] = ts_bytes
        img[i_off + 16:i_off + 20] = ts_bytes
        if not inode_size >= 256:
            continue
        cr_off = i_off + 130
        cr_val = struct.unpack('<I', img[cr_off:cr_off + 4])[0]
        if 1000000000 < cr_val:
            if not cr_val < 4294967295:
                continue
        else:
            continue
        old_timestamps.add(struct.pack('<I', cr_val))
        img[cr_off:cr_off + 4] = ts_bytes
        continue
    for old_ts in old_timestamps:
        pos = 0
        idx = img.find(old_ts, pos)
        if idx == -1:
            continue
        if not it_off <= idx < it_end:
            img[idx:idx + 4] = ts_bytes
        pos = idx + 4
        continue
class Protect1Engine:
    '''Engine para leitura e modifica├º├úo da parti├º├úo protect1 (SIM Lock).'''
    @staticmethod
    def ler_info(caminho: str) -> dict:
        '''
        Extrai informa├º├Áes da parti├º├úo protect1.
        Retorna dict com inodes, blocos, labels e status.
        '''
        resultado = {'inodes': 0, 'blocks': 0, 'free_blocks': 0, 'block_size': 0, 'blocos_dados': 0, 'labels_selinux': 0, 'mount_point': False, 'erro': None}
        try:
            with open(caminho, 'rb') as f:
                data = f.read()
            sb = _PT_SB_OFF
            resultado['inodes'] = struct.unpack_from('<I', data, sb)[0]
            resultado['blocks'] = struct.unpack_from('<I', data, sb + 4)[0]
            resultado['free_blocks'] = struct.unpack_from('<I', data, sb + 12)[0]
            bsz_raw = struct.unpack_from('<I', data, sb + 24)[0]
            resultado['block_size'] = 1024 << bsz_raw
            bsz = resultado['block_size']
            resultado['blocos_dados'] = sum((1 for i in range(0, len(data), bsz) if any((b != 0 for b in data[i:i + bsz]))))
            resultado['labels_selinux'] = data.count(_PT_LABEL)
            resultado['mount_point'] = _PT_MOUNT in data
        except Exception:
            resultado['erro'] = 'N├úo foi poss├¡vel ler as informa├º├Áes da parti├º├úo.'
        return resultado
        return resultado
    @staticmethod
    def ler_status(caminho: str) -> str:
        '''
        Retorna o status atual do SIM Lock.
        "BLOQUEADO", "DESBLOQUEADO" ou "DESCONHECIDO".
        '''
        try:
            with open(caminho, 'rb') as f:
                data = f.read()
            sb = _PT_SB_OFF
            inodes = struct.unpack_from('<I', data, sb)[0]
            labels = data.count(_PT_LABEL)
            if labels > _PT_LABELS_MIN and inodes >= _PT_INODES_LOCK:
                return 'BLOQUEADO'
            if labels == 0 and inodes <= _PT_INODES_CLEAN:
                return 'DESBLOQUEADO'
        except Exception:
            return 'ERRO DE LEITURA'
        return 'DESCONHECIDO'
    @staticmethod
    def aplicar_patch(caminho: str) -> tuple:
        '''
        Aplica a remo├º├úo do SIM Lock substituindo o filesystem inteiro.
        Valida antes se o arquivo ├® uma protect1 v├ílida.
        '''
        try:
            tamanho = os.path.getsize(caminho)
            if tamanho != _PT_TAM:
                return (False, 'Arquivo n├úo corresponde ao formato esperado.')
            with open(caminho, 'rb') as f:
                f.seek(_PT_MG_OFF)
                magic = struct.unpack('<H', f.read(2))[0]
            if magic != _PT_MG_VAL:
                return (False, 'Arquivo n├úo ├® um filesystem EXT4 v├ílido.')
            status = Protect1Engine.ler_status(caminho)
            if status == 'DESBLOQUEADO':
                return (False, 'SIM Lock j├í removido. Nenhuma altera├º├úo necess├íria.')
            template = _reconstruir_template()
            if len(template) != _PT_TAM:
                return (False, 'Erro interno na gera├º├úo do template.')
            sb_magic = struct.unpack_from('<H', template, _PT_MG_OFF)[0]
            if sb_magic != _PT_MG_VAL:
                return (False, 'Erro na valida├º├úo do template.')
            with open(caminho, 'wb') as f:
                f.write(template)
            with open(caminho, 'rb') as f:
                verificacao = f.read()
            if verificacao == template:
                return (True, 'SIM Lock removido com sucesso.')
        except PermissionError:
            return (False, 'Sem permiss├úo para modificar o arquivo.')
        except Exception:
            return (False, 'Erro ao aplicar a modifica├º├úo.')
        return (False, 'Falha na verifica├º├úo p├│s-escrita.')
