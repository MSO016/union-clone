import logging
import re
logger = logging.getLogger(__name__)
_ORIGENS_CONFIAVEIS = frozenset({'com.heytap.market', 'com.vivo.appstore', 'com.xiaomi.market', 'com.xiaomi.mipicks', 'com.android.vending', 'com.huawei.appmarket', 'com.android.packageinstaller', 'com.sec.android.app.samsungapps', 'com.google.android.packageinstaller'})
_RE_PACOTE = re.compile('[a-zA-Z][\\w]*(?:\\.[a-zA-Z0-9_]+)+')
class DeviceHardening:
    def __init__(self, adb):
        self._adb = adb
    def _shell(self, *args):
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
        aplicados = 0
        for chave in ('package_verifier_enable', 'verifier_verify_adb_installs', 'package_verifier_user_consent'):
            self._shell('settings', 'put', 'global', chave, '1')
            if self._shell('settings', 'get', 'global', chave) == '1':
                aplicados += 1
        return aplicados
    def _origens_com_permissao(self):
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
