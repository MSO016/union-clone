import logging
_log = logging.getLogger(__name__)
def fetch_mysql_user_status(email):
    if not email:
        return
    try:
        import pymysql
        from app.utils._app_cfg import db_config
        conn = pymysql.connect(**db_config(cursorclass=pymysql.cursors.DictCursor, ssl={'ca': None}, ssl_verify_cert=False, connect_timeout=5))
        try:
            cur = conn.cursor()
            cur.execute('SELECT status FROM usuarios WHERE email = %s', (email,))
            row = cur.fetchone()
            cur.close()
        finally:
            conn.close()
    except Exception as exc:
        _log.debug('ci-sentinel mysql-fail: %s', type(exc).__name__)
    return row.get('status') or '' if row else None
class SectorSentinel:
    def __init__(self, main_window_ref):
        self._mw = main_window_ref
        self._mysql_user_blocked = False
    def check(self):
        try:
            if getattr(self._mw, 'is_admin', False):
                return True
            if getattr(self._mw, '_lic_blocked', False):
                return False
            if self._mysql_user_blocked:
                return False
        except Exception:
            pass
        return True
    def on_timer_result(self, payload):
        try:
            ms = payload.get('_mysql_status')
            if ms is None:
                return
            status = ms.lower().strip()
            if status in ('', 'ativo'):
                self._mysql_user_blocked = False
                return
            self._mysql_user_blocked = True
            _log.info('CI-SENTINEL-BLOCK: %s status=%s', getattr(self._mw, 'user_email', '?'), status)
            self._apply_block(status)
            return
        except Exception:
            return
    def _apply_block(self, status):
        try:
            mw = self._mw
            if getattr(mw, '_lic_blocked', False):
                return
            mw._lic_blocked = True
            try:
                if getattr(mw, '_lic_timer', None) is not None:
                    mw._lic_timer.stop()
            except Exception:
                pass
            else:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(mw, 'Acesso Indisponivel', 'Seu acesso esta temporariamente indisponivel.\n\nEntre em contato com o suporte para regularizar.\n\nWhatsApp Suporte: (85) 9412-9977 ou (85) 99750-7465')
                mw._fazer_logout_lic()
        except Exception:
            return
