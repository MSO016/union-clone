import os
import html
import time
import tempfile
import logging
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QSpinBox, QLineEdit, QCheckBox, QPushButton, QGroupBox, QMessageBox)
from PyQt5.QtGui import (QTextDocument, QImage, QFont, QDesktopServices)
from PyQt5.QtCore import (Qt, QUrl, QTimer)
logger = logging.getLogger(__name__)
_DADOS_LOJA_FALLBACK = {'company_name': 'TECH UNION SOLUTIONS', 'trading_name': '', 'cnpj': '', 'address': '', 'city': '', 'state': '', 'phone': '', 'logo': None, 'footer_message': 'Sistema feito de tecnico para tecnicos'}
_SERVICOS = ['Verificacao/diagnostico de seguranca concluido', 'Remocao de aplicativos maliciosos/adware', 'Monitoramento de anuncios realizado', 'Blindagem do dispositivo aplicada', 'Limpeza de cache/dados de navegadores', 'Verificador de pacotes ativado']
def _carregar_loja():
    import sqlite3
    dados = dict(_DADOS_LOJA_FALLBACK)
    db = os.path.join('app', 'database', 'service_orders.db')
    if not os.path.exists(db):
        return dados
    conn = None
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='company_settings'")
        if cur.fetchone() is None:
            logger.info('Dados da empresa ainda nao cadastrados; usando padrao.')
            if conn is not None:
                conn.close()
                return dados
            return
    except Exception:
        logger.debug('Falha ao carregar dados da empresa.', exc_info=True)
    try:
        cur.execute('\n            SELECT company_name, trading_name, cnpj, address, city, state,\n                   phone, logo, footer_message\n            FROM company_settings ORDER BY updated_at DESC LIMIT 1\n        ')
        row = cur.fetchone()
        if row:
            dados.update({'company_name': row[0] or dados['company_name'], 'trading_name': row[1] or '', 'cnpj': row[2] or '', 'address': row[3] or '', 'city': row[4] or '', 'state': row[5] or '', 'phone': row[6] or '', 'logo': row[7], 'footer_message': row[8] or dados['footer_message']})
    except Exception:
        logger.debug('Falha ao carregar dados da empresa.', exc_info=True)
    finally:
        if conn is not None:
            conn.close()
    return dados
def _capturar_aparelho(adb):
    info = {}
    def prop(chave):
        try:
            out = adb._run_adb_command([adb.adb_path, 'shell', 'getprop', chave])
            return (out or '').strip()
        except Exception:
            return ''
    def secure(chave):
        try:
            out = adb._run_adb_command([adb.adb_path, 'shell', 'settings', 'get', 'secure', chave])
            out = (out or '').strip()
            if out.lower() in ('', 'null'):
                return ''
            return out
        except Exception:
            return ''
    info['brand'] = prop('ro.product.brand')
    info['model'] = prop('ro.product.model')
    info['android'] = prop('ro.build.version.release')
    info['security'] = prop('ro.build.version.security_patch')
    imei = _tentar_imei(adb)
    info['imei'] = imei
    if imei:
        info['id_tipo'], info['id_valor'] = 'IMEI', imei
        return info
    android_id = secure('android_id')
    if android_id:
        info['id_tipo'], info['id_valor'] = 'Android ID', android_id
        return info
    serial = prop('ro.serialno')
    info['id_tipo'], info['id_valor'] = ('Serie', serial) if serial else ('', '')
    return info
def _tentar_imei(adb):
    try:
        cmd = "service call iphonesubinfo 1 | grep -o '[0-9a-f]\\{8\\} ' | tail -n+3 | while read a; do echo -n \\\\u${a:4:4}\\\\u${a:0:4}; done"
        out = adb._run_adb_command([adb.adb_path, 'shell', cmd]) or ''
        digitos = ''.join((c for c in out if c.isdigit()))
        if len(digitos) >= 14:
            return digitos
        return ''
    except Exception:
        return ''
def _mascarar_imei(imei):
    if not imei:
        return 'Nao disponivel'
    digitos = ''.join((c for c in str(imei) if c.isdigit()))
    if len(digitos) < 6:
        return 'Nao disponivel'
    return f'{digitos[:2]}XXXX...{digitos[-4:]}'
def _mascarar_identificador(valor, tipo):
    if not valor:
        return 'Nao disponivel'
    if tipo == 'IMEI':
        return _mascarar_imei(valor)
    texto = str(valor).strip()
    if len(texto) <= 4:
        return 'XXXX'
    if len(texto) <= 8:
        return f'{texto[:2]}XX...{texto[-2:]}'
    return f'{texto[:4]}...{texto[-4:]}'
def _id_para_exibir(aparelho):
    tipo = aparelho.get('id_tipo') or ('IMEI' if aparelho.get('imei') else '')
    valor = aparelho.get('id_valor') or aparelho.get('imei') or ''
    rotulo = f'ID ({tipo})' if tipo else 'ID'
    return rotulo, _mascarar_identificador(valor, tipo)
def _numero_certificado():
    return str(int(time.time() * 1000))
def _montar_html(loja, aparelho, servicos, dias_garantia, cliente, cert_no):
    e = html.escape
    emissao = datetime.now()
    validade = emissao + timedelta(days=int(dias_garantia))
    cab = e(loja.get('company_name', 'TECH UNION SOLUTIONS'))
    linha2 = e(loja.get('trading_name') or '')
    cnpj = e(loja.get('cnpj') or '')
    endereco = ' - '.join([p for p in (loja.get('address'), loja.get('city'), loja.get('state')) if p])
    telefone = e(loja.get('phone') or '')
    rodape = e(loja.get('footer_message') or 'Sistema feito de tecnico para tecnicos')
    dispositivo = f'{aparelho.get('brand', '')} {aparelho.get('model', '')}'.strip() or 'Dispositivo Android'
    id_rotulo, id_valor = _id_para_exibir(aparelho)
    itens = ''.join((f'<p style="margin:4pt 0; color:#1e7e34; font-size:11pt;">[OK] {e(s)}</p>' for s in servicos)) or '<p style="color:#999;">-</p>'
    logo_html = '<img src="mem://logo" width="130" />' if loja.get('logo') else ''
    cliente_html = f'<p style="margin:4pt 0;"><b>Cliente:</b> {e(cliente)}</p>' if cliente else ''
    return ''.join(['\n    <div style="text-align:center; border-bottom:2pt solid #2c3e50; padding-bottom:10pt; margin-bottom:14pt;">\n        ', f'{logo_html}', '\n        <h1 style="margin:6pt 0 0 0; color:#2c3e50; font-size:22pt;">', f'{cab}', '</h1>\n        ', f'{f'<p style="margin:2pt 0; font-size:12pt;">{linha2}</p>' if linha2 else ''}', '\n        ', f'{f'<p style="margin:2pt 0; font-size:10pt;">CNPJ: {cnpj}</p>' if cnpj else ''}', '\n        ', f'{f'<p style="margin:2pt 0; font-size:10pt;">{e(endereco)}</p>' if endereco else ''}', '\n        ', f'{f'<p style="margin:2pt 0; font-size:10pt;">Tel: {telefone}</p>' if telefone else ''}', '\n    </div>\n    <h2 style="text-align:center; color:#b8860b; font-size:18pt; margin:6pt 0;">Certificado de Protecao</h2>\n    <p style="text-align:center; font-size:11pt; margin:0 0 14pt 0;">\n        Certificamos que o dispositivo <b>', f'{e(dispositivo)}', '</b> foi submetido a um processo\n        completo de protecao.\n    </p>\n    <table width="100%" cellspacing="0" cellpadding="8">\n      <tr valign="top">\n        <td width="50%" style="font-size:11pt; color:#2c3e50;">\n            ', f'{cliente_html}', '\n            <p style="margin:4pt 0;"><b>Dispositivo:</b> ', f'{e(dispositivo)}', '</p>\n            <p style="margin:4pt 0;"><b>', f'{e(id_rotulo)}', ':</b> ', f'{e(id_valor)}', '</p>\n            <p style="margin:4pt 0;"><b>Android:</b> ', f'{e(aparelho.get('android', 'N/A'))}', ' (patch ', f'{e(aparelho.get('security', 'N/A'))}', ')</p>\n            <p style="margin:4pt 0;"><b>Emissao:</b> ', f'{emissao.strftime('%d/%m/%Y')}', '</p>\n            <p style="margin:4pt 0;"><b>Validade:</b> ', f'{validade.strftime('%d/%m/%Y')}', '</p>\n            <p style="margin:4pt 0;"><b>Garantia:</b> ', f'{int(dias_garantia)}', ' dias</p>\n            <p style="margin:4pt 0;"><b>Certif. No.:</b> ', f'{e(cert_no)}', '</p>\n        </td>\n        <td width="50%">\n            <p style="font-weight:bold; color:#2c3e50; font-size:12pt; margin:0 0 6pt 0;">Protecoes aplicadas:</p>\n            ', f'{itens}', '\n        </td>\n      </tr>\n    </table>\n    <div style="margin-top:18pt; background:#1e7e34; color:#fff; text-align:center; padding:10pt;">\n        <span style="font-size:15pt; font-weight:bold;">** PROTECAO ATIVA **</span>\n    </div>\n    <div style="margin-top:22pt; border-top:1pt solid #ccc; padding-top:8pt; text-align:center;">\n        <p style="font-size:9pt; color:#666; margin:0;">', f'{rodape}', '</p>\n        <p style="font-size:8pt; color:#999; margin:4pt 0 0 0;">Emitido em: ', f'{emissao.strftime('%d/%m/%Y %H:%M')}', '</p>\n    </div>\n    '])
def _gerar_pdf(loja, aparelho, servicos, dias_garantia, cliente, cert_no):
    from PyQt5.QtPrintSupport import QPrinter
    doc = QTextDocument()
    doc.setDefaultFont(QFont('Arial', 12))
    if loja.get('logo'):
        img = QImage()
        if img.loadFromData(loja['logo']):
            doc.addResource(QTextDocument.ImageResource, QUrl('mem://logo'), img)
    doc.setHtml(_montar_html(loja, aparelho, servicos, dias_garantia, cliente, cert_no))
    caminho = os.path.join(tempfile.gettempdir(), f'certificado_protecao_{cert_no}.pdf')
    printer = QPrinter(QPrinter.ScreenResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(caminho)
    printer.setPageSize(QPrinter.A4)
    printer.setPageMargins(20, 20, 20, 20, QPrinter.Millimeter)
    page_rect = printer.pageRect(QPrinter.Point)
    doc.setPageSize(page_rect.size())
    doc.print_(printer)
    return caminho
class CertificadoProtecaoDialog(QDialog):
    def __init__(self, adb, parent=None):
        super().__init__(parent)
        self._adb = adb
        self.setWindowTitle('Certificado de Protecao')
        self.setMinimumWidth(600)
        self.setStyleSheet('\n            QDialog { background-color: #f4f6f8; }\n            QGroupBox {\n                font-weight: bold; color: #2c3e50; font-size: 13px;\n                border: 1px solid #d6dbe0; border-radius: 8px;\n                margin-top: 12px; background-color: #ffffff; padding: 10px;\n            }\n            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; }\n            QLabel { color: #2c3e50; font-size: 13px; }\n            QCheckBox { color: #2c3e50; font-size: 13px; padding: 3px 0; }\n            QSpinBox, QLineEdit {\n                border: 1px solid #bdc3c7; border-radius: 5px; padding: 6px;\n                background: #fff; font-size: 13px; min-height: 18px;\n            }\n            QPushButton {\n                background-color: #27ae60; color: white; border: none;\n                padding: 10px 20px; border-radius: 6px; font-weight: bold; font-size: 13px;\n            }\n            QPushButton:hover { background-color: #219150; }\n            QPushButton#secundario { background-color: #95a5a6; }\n            QPushButton#secundario:hover { background-color: #7f8c8d; }\n        ')
        self._loja = None
        self._aparelho = {}
        self._dados_prontos = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        titulo = QLabel('­ƒÅå Certificado de Protecao')
        titulo.setStyleSheet('font-size:18px; font-weight:bold; color:#2c3e50;')
        layout.addWidget(titulo)
        box_dev = QGroupBox('Dispositivo (capturado automaticamente)')
        form = QFormLayout(box_dev)
        self._lbl_aparelho = QLabel('Capturando...')
        self._lbl_id = QLabel('Capturando...')
        self._lbl_android = QLabel('Capturando...')
        form.addRow('Aparelho:', self._lbl_aparelho)
        form.addRow('Identificador:', self._lbl_id)
        form.addRow('Android:', self._lbl_android)
        layout.addWidget(box_dev)
        box_cfg = QGroupBox('Dados do certificado')
        f2 = QFormLayout(box_cfg)
        self.spin_garantia = QSpinBox()
        self.spin_garantia.setRange(0, 365)
        self.spin_garantia.setValue(90)
        self.spin_garantia.setSuffix(' dias')
        f2.addRow('Garantia:', self.spin_garantia)
        self.edit_cliente = QLineEdit()
        self.edit_cliente.setMaxLength(60)
        self.edit_cliente.setPlaceholderText('Opcional (ex.: nome do cliente / OS)')
        f2.addRow('Cliente:', self.edit_cliente)
        layout.addWidget(box_cfg)
        box_chk = QGroupBox('Servicos realizados (marque o que foi feito)')
        vchk = QVBoxLayout(box_chk)
        self._checks = []
        for s in _SERVICOS:
            cb = QCheckBox(s)
            self._checks.append(cb)
            vchk.addWidget(cb)
        layout.addWidget(box_chk)
        h = QHBoxLayout()
        h.addStretch()
        btn_cancel = QPushButton('Fechar')
        btn_cancel.setObjectName('secundario')
        btn_cancel.clicked.connect(self.reject)
        btn_gerar = QPushButton('Gerar Certificado (PDF)')
        btn_gerar.setDefault(True)
        btn_gerar.clicked.connect(self._gerar)
        h.addWidget(btn_cancel)
        h.addWidget(btn_gerar)
        layout.addLayout(h)
        QTimer.singleShot(0, self._popular_dados)
    def _popular_dados(self):
        if self._dados_prontos:
            return
        try:
            self._loja = _carregar_loja()
            self._aparelho = _capturar_aparelho(self._adb) if self._adb else {}
        except Exception:
            logger.debug('Falha ao capturar dados do aparelho.', exc_info=True)
        if self._loja is None:
            self._loja = dict(_DADOS_LOJA_FALLBACK)
        self._dados_prontos = True
        dispositivo = f'{self._aparelho.get('brand', '')} {self._aparelho.get('model', '')}'.strip()
        self._lbl_aparelho.setText(dispositivo or 'Dispositivo Android')
        tipo = self._aparelho.get('id_tipo') or ('IMEI' if self._aparelho.get('imei') else '')
        _, valor = _id_para_exibir(self._aparelho)
        self._lbl_id.setText(f'{valor} ({tipo})' if tipo else valor)
        self._lbl_android.setText(f'{self._aparelho.get('android', 'N/A')} (patch {self._aparelho.get('security', 'N/A')})')
    def _gerar(self):
        if not self._dados_prontos:
            self._popular_dados()
        servicos = [cb.text() for cb in self._checks if cb.isChecked()]
        if not servicos:
            QMessageBox.warning(self, 'Atencao', 'Marque pelo menos um servico realizado.')
            return
        try:
            caminho = _gerar_pdf(self._loja, self._aparelho, servicos, self.spin_garantia.value(), self.edit_cliente.text().strip(), _numero_certificado())
            QDesktopServices.openUrl(QUrl.fromLocalFile(caminho))
            QMessageBox.information(self, 'Certificado', 'Certificado gerado e aberto no visualizador padrao.')
        except Exception:
            logger.debug('Falha ao gerar certificado.', exc_info=True)
            QMessageBox.warning(self, 'Certificado', 'Nao foi possivel gerar o certificado. Tente novamente.')
# WARNING: Decompyle incomplete
