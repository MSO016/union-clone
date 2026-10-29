'''Reforco de protecao do dispositivo (anti-adware).
Aplica ajustes de seguranca reversiveis, sem privilegios elevados:
 - reforca a verificacao de aplicativos do sistema;
 - restringe instalacoes a partir de origens nao confiaveis, preservando as
   lojas oficiais.
Modulo isolado de proposito unico. As mensagens visiveis ao operador sao
genericas: nenhum detalhe operacional e exposto.
'''
import logging
import re
logger = logging.getLogger(__name__)
_ORIGENS_CONFIAVEIS = frozenset({'com.heytap.market', 'com.vivo.appstore', 'com.xiaomi.market', 'com.xiaomi.mipicks', 'com.android.vending', 'com.huawei.appmarket', 'com.android.packageinstaller', 'com.sec.android.app.samsungapps', 'com.google.android.packageinstaller'})
_RE_PACOTE = re.compile('[a-zA-Z][\\w]*(?:\\.[a-zA-Z0-9_]+)+')
class DeviceHardening:
    '''Operacoes de reforco aplicadas sobre um dispositivo conectado.'''
    def __init__(self, adb):
        self._adb = adb
    def _shell(self, *args):
        '''Executa uma instrucao no dispositivo e devolve a saida (ou vazio).
        Qualquer falha e contida aqui para nao interromper o fluxo nem expor
        detalhes ao operador.
        '''
        try:
            path = getattr(self._adb, 'adb_path', None)
            if not path:
                return ''
            saida = self._adb._run_adb_command([path, 'shell', *args])
            return (saida or '').strip()
        except Exception:
            logger.debug('Instrucao de reforco nao concluida.', exc_info=True)
            return ''
    def _sdk(self):
        valor = self._shell('getprop', 'ro.build.version.sdk')
        try:
            return int(valor)
        except (TypeError, ValueError):
            return 0
    def _reforcar_verificacao(self):
        '''Liga a verificacao de aplicativos do sistema. Retorna itens aplicados.'''
        aplicados = 0
        for chave in ('package_verifier_enable', 'verifier_verify_adb_installs', 'package_verifier_user_consent'):
            self._shell('settings', 'put', 'global', chave, '1')
            if self._shell('settings', 'get', 'global', chave) == '1':
                aplicados += 1
        return aplicados
    def _origens_com_permissao(self):
        '''Lista pacotes autorizados a instalar de origens externas.'''
        saida = self._shell('appops', 'query-op', 'REQUEST_INSTALL_PACKAGES', 'allow')
        if not saida or 'No operations' in saida:
            return []
        encontrados = set()
        for linha in saida.splitlines():
            linha = linha.strip()
            if not linha or linha.endswith(':'):
                continue
            for token in _RE_PACOTE.findall(linha):
                encontrados.add(token)
        return sorted(encontrados)
    def _restringir_origens(self):
        '''Restringe instalacao de origens externas, exceto lojas oficiais.
        Retorna a quantidade de origens restringidas.
        '''
        if self._sdk() and self._sdk() <= 25:
            self._shell('settings', 'put', 'global', 'install_non_market_apps', '0')
            return 1
        restringidas = 0
        for pkg in self._origens_com_permissao():
            if pkg in _ORIGENS_CONFIAVEIS:
                continue
            self._shell('appops', 'set', pkg, 'REQUEST_INSTALL_PACKAGES', 'ignore')
            restringidas += 1
        return restringidas
    def aplicar(self, progresso=None):
        '''Executa o reforco em camadas e devolve um resumo numerico.
        `progresso` (opcional) e um callback que recebe mensagens genericas
        para exibicao. Nenhuma informacao tecnica e transmitida.
        '''
        def _aviso(msg):
            if callable(progresso):
                try:
                    progresso(msg)
                    return
                except Exception:
                    pass
        resumo = {'verificacao': 0, 'origens': 0, 'ok': False}
        try:
            _aviso('Reforcando a verificacao de aplicativos...')
            resumo['verificacao'] = self._reforcar_verificacao()
            _aviso('Protegendo contra origens nao confiaveis...')
            resumo['origens'] = self._restringir_origens()
            resumo['ok'] = True
        except Exception:
            logger.debug('Reforco interrompido.', exc_info=True)
            resumo['ok'] = False
        return resumo
        return resumo
