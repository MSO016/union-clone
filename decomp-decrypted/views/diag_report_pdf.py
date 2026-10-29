import os
import html
import time
import tempfile
import logging
from datetime import datetime
logger = logging.getLogger(__name__)
def _carregar_empresa():
    import sqlite3
    dados = {'company_name': 'TECH UNION SOLUTIONS', 'trading_name': '', 'cnpj': '', 'address': '', 'city': '', 'state': '', 'phone': '', 'logo': None, 'footer_message': 'Diagnostico gerado automaticamente'}
    db = os.path.join('app', 'database', 'service_orders.db')
    if not os.path.exists(db):
        return dados
    conn = None
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='company_settings'")
        if cur.fetchone() is None:
            if conn:
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
        if conn:
            conn.close()
    return dados
def _numero_relatorio():
    agora = datetime.now()
    return f'DIAG-{agora.strftime('%Y%m%d')}-{int(time.time()) % 100000:05d}'
def _secao_html(titulo, linhas):
    e = html.escape
    rows = ''
    for label, valor, color in linhas:
        cor_css = f'color:{color};' if color else ''
        rows += f'<tr><td style="padding:2pt 8pt; font-size:10pt;">{e(label)}</td>'
        rows += f'<td style="padding:2pt 8pt; font-size:10pt; font-weight:bold; {cor_css}">{e(str(valor))}</td></tr>'
    return f'\n    <div style="margin:10pt 0 4pt 0;">\n        <p style="font-weight:bold; font-size:12pt; color:#1a365d; margin:0 0 4pt 0;\n                  border-bottom:1pt solid #cbd5e0; padding-bottom:3pt;">{e(titulo)}</p>\n        <table cellspacing="0" cellpadding="0" style="margin-left:8pt;">{rows}</table>\n    </div>'
def _montar_html_relatorio(empresa, dispositivo, secoes, relatorio_no):
    e = html.escape
    agora = datetime.now()
    cab = e(empresa.get('company_name', 'TECH UNION SOLUTIONS'))
    linha2 = e(empresa.get('trading_name') or '')
    cnpj = e(empresa.get('cnpj') or '')
    endereco = ' - '.join([p for p in (empresa.get('address'), empresa.get('city'), empresa.get('state')) if p])
    telefone = e(empresa.get('phone') or '')
    rodape = e(empresa.get('footer_message') or 'Diagnostico gerado automaticamente')
    logo_html = '<img src="mem://logo" width="110" />' if empresa.get('logo') else ''
    model = f'{dispositivo.get('brand', '')} {dispositivo.get('model', '')}'.strip() or 'Dispositivo'
    android = dispositivo.get('android_version', '')
    patch = dispositivo.get('security_patch', '')
    chipset = dispositivo.get('chipset_vendor', '')
    platform = dispositivo.get('platform', '')
    secoes_html = ''
    for titulo, linhas in secoes:
        if linhas:
            secoes_html += _secao_html(titulo, linhas)
    return ''.join(['\n    <div style="text-align:center; border-bottom:2pt solid #1a365d; padding-bottom:8pt; margin-bottom:10pt;">\n        ', f'{logo_html}', '\n        <h1 style="margin:4pt 0 0 0; color:#1a365d; font-size:18pt;">', f'{cab}', '</h1>\n        ', f'{f'<p style="margin:1pt 0; font-size:10pt;">{linha2}</p>' if linha2 else ''}', '\n        ', f'{f'<p style="margin:1pt 0; font-size:9pt;">CNPJ: {cnpj}</p>' if cnpj else ''}', '\n        ', f'{f'<p style="margin:1pt 0; font-size:9pt;">{e(endereco)}</p>' if endereco else ''}', '\n        ', f'{f'<p style="margin:1pt 0; font-size:9pt;">Tel: {telefone}</p>' if telefone else ''}', '\n    </div>\n\n    <h2 style="text-align:center; color:#2d3748; font-size:15pt; margin:4pt 0 8pt 0;">\n        Relatorio de Diagnostico\n    </h2>\n\n    <table width="100%" cellspacing="0" cellpadding="4"\n           style="background:#f7fafc; border:1pt solid #e2e8f0; border-radius:4pt; margin-bottom:10pt;">\n      <tr>\n        <td style="font-size:10pt; padding:6pt 10pt;">\n            <b>Dispositivo:</b> ', f'{e(model)}', '<br/>\n            <b>Android:</b> ', f'{e(android)}', ' ', f'{f'(Patch {e(patch)})' if patch else ''}', '<br/>\n            <b>Chipset:</b> ', f'{e(chipset)}', ' ', f'{f'({e(platform)})' if platform else ''}', '\n        </td>\n        <td style="font-size:10pt; padding:6pt 10pt; text-align:right;">\n            <b>Relatorio:</b> ', f'{e(relatorio_no)}', '<br/>\n            <b>Data:</b> ', f'{agora.strftime('%d/%m/%Y %H:%M')}', '<br/>\n            <b>Tecnico:</b> ___________________\n        </td>\n      </tr>\n    </table>\n\n    ', f'{secoes_html}', '\n\n    <div style="margin-top:20pt; padding-top:10pt; border-top:1pt solid #e2e8f0;">\n        <table width="100%">\n          <tr>\n            <td width="50%" style="font-size:9pt; padding-top:30pt; border-top:1pt solid #333; text-align:center;">\n                Assinatura do Tecnico\n            </td>\n            <td width="10%"></td>\n            <td width="50%" style="font-size:9pt; padding-top:30pt; border-top:1pt solid #333; text-align:center;">\n                Assinatura do Cliente\n            </td>\n          </tr>\n        </table>\n    </div>\n\n    <div style="margin-top:14pt; text-align:center;">\n        <p style="font-size:8pt; color:#718096; margin:0;">', f'{rodape}', '</p>\n        <p style="font-size:7pt; color:#a0aec0; margin:2pt 0 0 0;">\n            Emitido em: ', f'{agora.strftime('%d/%m/%Y %H:%M')}', ' | ', f'{e(relatorio_no)}', '\n        </p>\n    </div>\n    '])
def _dados_para_secoes(diagnosticos):
    secoes = []
    bat = diagnosticos.get('battery')
    if bat and bat.get('level') is not None:
        linhas = []
        if bat.get('health_pct') is not None:
            linhas.append(('Saude', f'{bat['health_pct']}% ({bat['health_label']})', bat.get('health_color')))
        if bat.get('cycles') is not None:
            linhas.append(('Ciclos de carga', str(bat['cycles']), None))
        if bat.get('capacity_now_mah') and bat.get('capacity_design_mah'):
            linhas.append(('Capacidade', f'{bat['capacity_now_mah']} / {bat['capacity_design_mah']} mAh', None))
        linhas.append(('Nivel atual', f'{bat['level']}%', None))
        if bat.get('temperature_c') is not None:
            linhas.append(('Temperatura', f'{bat['temperature_c']:.1f} C', bat.get('temp_color')))
        if bat.get('voltage_v') is not None:
            linhas.append(('Voltagem', f'{bat['voltage_v']:.3f}V', None))
        secoes.append(('Bateria', linhas))
    slots = diagnosticos.get('signal')
    if slots:
        linhas = []
        for slot in slots:
            prefix = f'SIM {slot['slot']}' if len(slots) > 1 else 'Rede'
            if slot['bars'] == 0 and slot['dbm'] is None:
                linhas.append((prefix, 'Sem sinal', 'gray'))
            else:
                gen = slot.get('network_gen') or 'Conectado'
                dbm_info = f' ({slot['dbm']} dBm)' if slot.get('dbm') else ''
                linhas.append((prefix, f'{gen}{dbm_info} - {slot['classification']}', slot.get('color')))
                if slot.get('operator'):
                    linhas.append(('  Operadora', slot['operator'], None))
        secoes.append(('Sinal Celular', linhas))
    sen = diagnosticos.get('sensors')
    if sen and sen.get('total', 0) > 0:
        linhas = []
        for name in sen.get('essenciais_presentes', {}):
            linhas.append((name, 'Presente', 'green'))
        for name in sen.get('essenciais_ausentes', []):
            linhas.append((name, 'Ausente', 'red'))
        if sen.get('gyro_type') == 'virtual':
            linhas.append(('Giroscopio', 'Virtual (software)', 'orange'))
        total_e = len(sen.get('essenciais_presentes', {}))
        total_all = total_e + len(sen.get('essenciais_ausentes', []))
        linhas.append(('Resumo', f'{total_e}/{total_all} essenciais', None))
        secoes.append(('Sensores', linhas))
    sto = diagnosticos.get('storage')
    if sto and sto.get('total_gb'):
        linhas = []
        if sto.get('type'):
            linhas.append(('Tipo', sto['type'], None))
        linhas.append(('Capacidade', f'{sto['total_gb']:.0f} GB', None))
        if sto.get('used_gb') is not None:
            linhas.append(('Usado', f'{sto['used_gb']:.1f} GB ({sto.get('used_pct', '?')}%)', sto.get('status_color')))
        if sto.get('free_gb') is not None:
            linhas.append(('Livre', f'{sto['free_gb']:.1f} GB', None))
        secoes.append(('Armazenamento', linhas))
    mem = diagnosticos.get('memory')
    if mem and mem.get('total_gb'):
        linhas = [('Total', f'{mem['total_gb']:.1f} GB', None)]
        if mem.get('available_gb'):
            linhas.append(('Disponivel', f'{mem['available_gb']:.1f} GB', None))
        if mem.get('used_pct') is not None:
            linhas.append(('Em uso', f'{mem['used_pct']}%', mem.get('status_color')))
        secoes.append(('Memoria RAM', linhas))
    thm = diagnosticos.get('thermal')
    if thm and thm.get('available'):
        linhas = []
        if thm.get('cpu') is not None:
            linhas.append(('CPU', f'{thm['cpu']:.1f} C', None))
        if thm.get('gpu') is not None:
            linhas.append(('GPU', f'{thm['gpu']:.1f} C', None))
        if thm.get('battery') is not None:
            linhas.append(('Bateria', f'{thm['battery']:.1f} C', None))
        if thm.get('skin') is not None:
            linhas.append(('Superficie', f'{thm['skin']:.1f} C', None))
        secoes.append(('Temperatura', linhas))
    cpu = diagnosticos.get('cpu')
    if cpu and cpu.get('core_count', 0) > 0:
        linhas = []
        if cpu.get('vendor'):
            linhas.append(('Fabricante', cpu['vendor'], None))
        linhas.append(('Nucleos', str(cpu['core_count']), None))
        if cpu.get('max_freq_ghz'):
            linhas.append(('Frequencia max', f'{cpu['max_freq_ghz']:.2f} GHz', None))
        if cpu.get('category'):
            linhas.append(('Categoria', cpu['category'], None))
        secoes.append(('Processador', linhas))
    tch = diagnosticos.get('touch')
    if tch and tch.get('display_resolution'):
        linhas = [('Resolucao', tch['display_resolution'], None), ('Multi-touch', f'{tch['multitouch_points']} pontos' if tch.get('multitouch_points') else 'N/A', None), ('Pressao', 'Sim' if tch.get('has_pressure') else 'Nao', None)]
        secoes.append(('Touch / Display', linhas))
    cam = diagnosticos.get('camera')
    if cam and cam.get('total', 0) > 0:
        linhas = [('Cameras detectadas', str(cam['total']), None)]
        secoes.append(('Camera', linhas))
    return secoes
def gerar_relatorio_pdf(diagnosticos, dispositivo_info):
    try:
        from PyQt5.QtPrintSupport import QPrinter
        from PyQt5.QtGui import (QTextDocument, QImage, QFont)
        from PyQt5.QtCore import QUrl
    except ImportError:
        logger.warning('PyQt5 indisponivel para gerar PDF.')
    try:
        empresa = _carregar_empresa()
        relatorio_no = _numero_relatorio()
        secoes = _dados_para_secoes(diagnosticos)
        if not secoes:
            logger.info('Nenhum dado de diagnostico para gerar relatorio.')
            return
        html_content = _montar_html_relatorio(empresa, dispositivo_info, secoes, relatorio_no)
        doc = QTextDocument()
        doc.setDefaultFont(QFont('Arial', 10))
        if empresa.get('logo'):
            img = QImage()
            if img.loadFromData(empresa['logo']):
                doc.addResource(QTextDocument.ImageResource, QUrl('mem://logo'), img)
        doc.setHtml(html_content)
        caminho = os.path.join(tempfile.gettempdir(), f'relatorio_diagnostico_{relatorio_no}.pdf')
        printer = QPrinter(QPrinter.ScreenResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(caminho)
        printer.setPageSize(QPrinter.A4)
        printer.setPageMargins(15, 15, 15, 15, QPrinter.Millimeter)
        page_rect = printer.pageRect(QPrinter.Point)
        doc.setPageSize(page_rect.size())
        doc.print_(printer)
    except Exception:
        logger.warning('Falha ao gerar PDF de diagnostico.', exc_info=True)
    return caminho
# WARNING: Decompyle incomplete
