import os
import struct
from ._cfg import (EXTENSOES_VALIDAS, EXTENSOES_PROIBIDAS, TAMANHO_MAX_ARQUIVO, _P1_TAM, _P1_TAM_MIN, _P1_TAM_MAX, _O1_TAM, _O1_TAM_MIN, _O1_TAM_MAX, _X1_TAM, _X1_MG_OFF, _X1_MG_VAL, _OP_TAM_MIN, _MD_TAM, _MD_MAGICS, _MD_PJ_TAM, _PT_TAM, _PT_TAM_MIN, _PT_TAM_MAX, _PT_MG_OFF, _PT_MG_VAL)
class Validador:
    @staticmethod
    def validar_arquivo(caminho: str) -> tuple[bool, str]:
        try:
            if not caminho or not caminho.strip():
                return (False, 'Nenhum arquivo selecionado.')
            if not os.path.exists(caminho):
                return (False, 'Arquivo n├úo encontrado.')
            if not os.path.isfile(caminho):
                return (False, 'O caminho informado n├úo ├® um arquivo.')
            tamanho = os.path.getsize(caminho)
            if tamanho == 0:
                return (False, 'Arquivo vazio (0 bytes).')
            if tamanho > TAMANHO_MAX_ARQUIVO:
                return (False, 'Arquivo excede o tamanho m├íximo permitido.')
            _, ext = os.path.splitext(caminho)
            ext = ext.lower()
            if ext in EXTENSOES_PROIBIDAS:
                return (False, 'Tipo de arquivo n├úo suportado.')
            if ext not in EXTENSOES_VALIDAS:
                return (False, 'Extens├úo de arquivo n├úo reconhecida.')
            tam_mb = tamanho / 1048576
            return True, f'{tam_mb:.1f} MB ({tamanho:,} bytes)'
        except PermissionError:
            return (False, 'Sem permiss├úo para acessar o arquivo.')
        except Exception:
            return (False, 'Erro ao validar o arquivo.')
    @staticmethod
    def validar_proinfo(caminho: str, estrito: bool=False) -> tuple[bool, str]:
        try:
            ok, msg = Validador.validar_arquivo(caminho)
            if not ok:
                return False, msg
            tamanho = os.path.getsize(caminho)
            if estrito:
                if tamanho != _P1_TAM:
                    return (False, 'Arquivo n├úo corresponde ao formato esperado para esta parti├º├úo.')
                return (True, 'Parti├º├úo v├ílida.')
            if not _P1_TAM_MIN <= tamanho <= _P1_TAM_MAX:
                return (False, 'Arquivo n├úo corresponde ao formato esperado para esta parti├º├úo.')
        except Exception:
            return (False, 'Erro ao validar a parti├º├úo.')
        return (True, 'Parti├º├úo v├ílida.')
    @staticmethod
    def validar_oeminfo(caminho: str, estrito: bool=False) -> tuple[bool, str]:
        try:
            ok, msg = Validador.validar_arquivo(caminho)
            if not ok:
                return False, msg
            tamanho = os.path.getsize(caminho)
            if estrito:
                if tamanho != _O1_TAM:
                    return (False, 'Arquivo n├úo corresponde ao formato esperado para esta parti├º├úo.')
                return (True, 'Parti├º├úo v├ílida.')
            if not _O1_TAM_MIN <= tamanho <= _O1_TAM_MAX:
                return (False, 'Arquivo n├úo corresponde ao formato esperado para esta parti├º├úo.')
        except Exception:
            return (False, 'Erro ao validar a parti├º├úo.')
        return (True, 'Parti├º├úo v├ílida.')
    @staticmethod
    def validar_persist(caminho: str) -> tuple[bool, str]:
        try:
            ok, msg = Validador.validar_arquivo(caminho)
            if not ok:
                return False, msg
            tamanho = os.path.getsize(caminho)
            margem = _X1_TAM * 0.1
            if not _X1_TAM - margem <= tamanho <= _X1_TAM + margem:
                return (False, 'Arquivo n├úo corresponde ao formato esperado para esta parti├º├úo.')
        except PermissionError:
            return (False, 'Sem permiss├úo para acessar o arquivo.')
        except Exception:
            return (False, 'Erro ao validar a parti├º├úo.')
        try:
            with open(caminho, 'rb') as f:
                f.seek(_X1_MG_OFF)
                magic = f.read(2)
            if magic != _X1_MG_VAL:
                return (False, 'Arquivo n├úo corresponde ao formato esperado para esta parti├º├úo.')
        except PermissionError:
            return (False, 'Sem permiss├úo para acessar o arquivo.')
        except Exception:
            return (False, 'Erro ao validar a parti├º├úo.')
        return (True, 'Parti├º├úo v├ílida.')
    @staticmethod
    def validar_miscdata(caminho: str) -> tuple[bool, str]:
        try:
            ok, msg = Validador.validar_arquivo(caminho)
            if not ok:
                return False, msg
            tamanho = os.path.getsize(caminho)
            if tamanho not in (_MD_TAM, _MD_PJ_TAM):
                return (False, 'Arquivo n├úo corresponde ao formato esperado para esta parti├º├úo.')
            with open(caminho, 'rb') as f:
                header = f.read(4)
            if header not in _MD_MAGICS:
                return (False, 'Arquivo n├úo corresponde ao formato esperado para esta parti├º├úo.')
        except PermissionError:
            return (False, 'Sem permiss├úo para acessar o arquivo.')
        except Exception:
            return (False, 'Erro ao validar a parti├º├úo.')
        return (True, 'Parti├º├úo v├ílida.')
    @staticmethod
    def validar_protect1(caminho: str, estrito: bool=False) -> tuple[bool, str]:
        try:
            ok, msg = Validador.validar_arquivo(caminho)
            if not ok:
                return False, msg
            tamanho = os.path.getsize(caminho)
            if estrito:
                if tamanho != _PT_TAM:
                    return (False, 'Arquivo n├úo corresponde ao formato esperado para esta parti├º├úo.')
            elif not _PT_TAM_MIN <= tamanho <= _PT_TAM_MAX:
                return (False, 'Arquivo n├úo corresponde ao formato esperado para esta parti├º├úo.')
        except PermissionError:
            return (False, 'Sem permiss├úo para acessar o arquivo.')
        except Exception:
            return (False, 'Erro ao validar a parti├º├úo.')
        try:
            with open(caminho, 'rb') as f:
                f.seek(_PT_MG_OFF)
                magic = struct.unpack('<H', f.read(2))[0]
            if magic != _PT_MG_VAL:
                return (False, 'Arquivo n├úo corresponde ao formato esperado para esta parti├º├úo.')
        except PermissionError:
            return (False, 'Sem permiss├úo para acessar o arquivo.')
        except Exception:
            return (False, 'Erro ao validar a parti├º├úo.')
        return (True, 'Parti├º├úo v├ílida.')
    @staticmethod
    def validar_oplusreserve2(caminho: str) -> tuple[bool, str]:
        try:
            ok, msg = Validador.validar_arquivo(caminho)
            if not ok:
                return False, msg
            tamanho = os.path.getsize(caminho)
            if tamanho < _OP_TAM_MIN:
                return (False, 'Arquivo n├úo corresponde ao formato esperado para esta parti├º├úo.')
        except Exception:
            return (False, 'Erro ao validar a parti├º├úo.')
        return (True, 'Parti├º├úo v├ílida.')
