'''
Gerenciador de backups para o editor de parti├º├Áes HXD.
Cria c├│pias de seguran├ºa antes de qualquer opera├º├úo de patch,
com timestamp no nome para rastreabilidade.
Mensagens NUNCA exp├Áem caminhos completos do sistema ÔÇö apenas o nome do arquivo.
'''
import os
import shutil
import datetime
class BackupManager:
    '''Gerencia cria├º├úo e listagem de backups de parti├º├Áes.'''
    def __init__(self, pasta_backup: str=None):
        '''
        Inicializa o gerenciador de backups.
        Se pasta_backup for None, utiliza Documents/UNION_HXD_Backups
        no diret├│rio home do usu├írio.
        '''
        if pasta_backup:
            self._pasta = pasta_backup
        else:
            home = os.path.expanduser('~')
            self._pasta = os.path.join(home, 'Documents', 'UNION_HXD_Backups')
        self._pronto = False
        try:
            os.makedirs(self._pasta, exist_ok=True)
            self._pronto = os.path.isdir(self._pasta)
            return
        except Exception:
            self._pronto = False
    @property
    def pronto(self) -> bool:
        '''Indica se a pasta de backups est├í acess├¡vel.'''
        return self._pronto
    @property
    def pasta(self) -> str:
        '''Retorna o caminho da pasta de backups.'''
        return self._pasta
    def criar_backup(self, caminho_original: str, tipo_operacao: str) -> str:
        '''
        Cria um backup do arquivo original antes de aplicar um patch.
        Retorna o nome do arquivo de backup (sem o caminho completo)
        ou string de erro amig├ível.
        '''
        try:
            if not os.path.isfile(caminho_original):
                return ''
            os.makedirs(self._pasta, exist_ok=True)
            nome_base = os.path.basename(caminho_original)
            nome_sem_ext, ext = os.path.splitext(nome_base)
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            tipo_limpo = tipo_operacao.replace(' ', '_').lower()
            nome_backup = f'backup_{timestamp}_{tipo_limpo}_{nome_sem_ext}{ext}'
            destino = os.path.join(self._pasta, nome_backup)
            shutil.copy2(caminho_original, destino)
            tam_orig = os.path.getsize(caminho_original)
            tam_dest = os.path.getsize(destino)
            if tam_orig != tam_dest:
                pass
            try:
                os.remove(destino)
            except OSError:
                return ''
            else:
                return ''
        except PermissionError:
            return ''
        except Exception:
            return ''
        return nome_backup
    def listar_backups(self) -> list[dict]:
        '''
        Lista os backups existentes na pasta de backups.
        Retorna uma lista de dicts com:
        - nome: nome do arquivo (sem caminho completo)
        - tamanho: tamanho em bytes
        - data: data de modifica├º├úo formatada
        '''
        resultado = []
        try:
            if not os.path.isdir(self._pasta):
                return resultado
            for nome in sorted(os.listdir(self._pasta), reverse=True):
                caminho = os.path.join(self._pasta, nome)
                if os.path.isfile(caminho):
                    pass
            try:
                stat = os.stat(caminho)
                dt = datetime.datetime.fromtimestamp(stat.st_mtime)
                resultado.append({'nome': nome, 'tamanho': stat.st_size, 'data': dt.strftime('%d/%m/%Y %H:%M:%S')})
            except Exception:
                pass
        except Exception:
            pass
        return resultado
