'''
TECH UNION - Sistema de Impressao de Relatorios
Impressao de logs e relatorios de bateria.
Gera PDF automaticamente para facilitar uso.
'''
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QMessageBox, QFileDialog)
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtGui import (QTextDocument, QFont, QDesktopServices)
from PyQt5.QtCore import Qt, QUrl
from datetime import datetime
import logging
import os
import tempfile
logger = logging.getLogger(__name__)
class ReportPrinter:
    '''Gerenciador de impressao de relatorios'''
    def __init__(self, user_email: str=None):
        '''
Args:
    user_email: Email do usuario para buscar dados da empresa
'''
        self.user_email = user_email
        self._company_data = None
    @property
    def company_data(self):
        '''Carrega dados da empresa (lazy loading)'''
        if self._company_data is None:
            try:
                from app.utils.company_data_loader import get_company_data_by_email
                self._company_data = get_company_data_by_email(self.user_email)
            except:
                self._company_data = {'company_name': 'TECH UNION SOLUTIONS', 'footer_message': 'Sistema feito de tecnico para tecnicos'}
            return self._company_data
        return self._company_data
    def _get_header_html(self) -> str:
        '''Gera cabecalho HTML para o relatorio - fontes grandes e legiveis'''
        dados = self.company_data
        html = f'\n        <div style="text-align: center; margin-bottom: 25pt; border-bottom: 2pt solid #333; padding-bottom: 15pt;">\n            <h1 style="margin: 0; color: #2c3e50; font-size: 24pt; font-weight: bold;">{dados.get('company_name', 'TECH UNION SOLUTIONS')}</h1>\n        '
        if dados.get('trading_name') and dados['trading_name'] != dados.get('company_name'):
            html += f'<p style="margin: 5pt 0; font-size: 14pt;">{dados['trading_name']}</p>'
        if dados.get('cnpj'):
            html += f'<p style="margin: 5pt 0; font-size: 11pt;">CNPJ: {dados['cnpj']}</p>'
        endereco_parts = []
        if dados.get('address'):
            endereco_parts.append(dados['address'])
        if dados.get('city'):
            endereco_parts.append(dados['city'])
        if dados.get('state'):
            endereco_parts.append(dados['state'])
        if endereco_parts:
            html += f'<p style="margin: 5pt 0; font-size: 11pt;">{' - '.join(endereco_parts)}</p>'
        if dados.get('phone'):
            html += f'<p style="margin: 5pt 0; font-size: 11pt;">Tel: {dados['phone']}</p>'
        html += '</div>'
        return html
    def _get_footer_html(self) -> str:
        '''Gera rodape HTML para o relatorio - fontes legiveis'''
        dados = self.company_data
        footer_msg = dados.get('footer_message', 'Sistema feito de tecnico para tecnicos')
        html = f'\n        <div style="margin-top: 30pt; border-top: 1pt solid #ccc; padding-top: 10pt; text-align: center;">\n            <p style="font-size: 10pt; color: #666; margin: 0;">{footer_msg}</p>\n            <p style="font-size: 9pt; color: #999; margin: 6pt 0 0 0;">Impresso em: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>\n        </div>\n        '
        return html
    def print_log(self, log_content: str, title: str='Log do Sistema', parent=None, max_lines: int=500) -> bool:
        """
Gera PDF do log e abre automaticamente.
Filtra mensagem inicial de boas-vindas, comeca a partir de '=== Iniciando'.
Limita quantidade de linhas para evitar lentidao.
Args:
    log_content: Conteudo do log para imprimir
    title: Titulo do relatorio
    parent: Widget pai para o dialogo
    max_lines: Maximo de linhas (padrao 500, suficiente para maioria dos casos)
Returns:
    bool: True se gerou PDF, False se falhou
"""
        if not log_content or not log_content.strip():
            QMessageBox.warning(parent, 'Aviso', 'Nao ha conteudo para imprimir.')
            return False
        log_filtrado = log_content
        marcador = '=== Iniciando'
        if marcador in log_content:
            idx = log_content.find(marcador)
            log_filtrado = log_content[idx:]
        if not log_filtrado.strip():
            QMessageBox.warning(parent, 'Aviso', 'Nao ha dados de consulta para imprimir.\nExecute uma consulta primeiro.')
            return False
        linhas = log_filtrado.split('\n')
        total_linhas = len(linhas)
        log_truncado = False
        if total_linhas > max_lines:
            reply = QMessageBox.question(parent, 'Log Muito Grande', f'O log tem {total_linhas} linhas.\nPara evitar lentidao, serao impressas as ultimas {max_lines} linhas.\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.No:
                return False
            linhas = linhas[-max_lines:]
            log_filtrado = '\n'.join(linhas)
            log_truncado = True
        html = self._get_header_html()
        html += f'<h2 style="color: #34495e; font-size: 18pt; margin: 12pt 0;">{title}</h2>'
        html += f'<p style="font-size: 11pt; color: #666;">Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>'
        if log_truncado:
            html += f'<p style="font-size: 9pt; color: #e74c3c; margin: 5pt 0;">* Log truncado: exibindo ultimas {max_lines} de {total_linhas} linhas</p>'
        html += '<hr style="border: none; border-top: 1pt solid #ddd; margin: 12pt 0;">'
        log_escaped = log_filtrado.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
        html += f'<div style="font-family: Consolas, monospace; font-size: 10pt; background: #f5f5f5; padding: 12pt; line-height: 1.5;">{log_escaped}</div>'
        html += self._get_footer_html()
        return self._generate_pdf(html, 'log_dispositivo', parent)
    def print_battery_report(self, battery_info: dict, device_info: dict=None, parent=None) -> bool:
        '''
Gera PDF do relatorio de bateria e abre automaticamente.
Args:
    battery_info: Dicionario com informacoes da bateria
    device_info: Dicionario com informacoes do dispositivo (opcional)
    parent: Widget pai para o dialogo
Returns:
    bool: True se gerou PDF, False se falhou
'''
        html = self._get_header_html()
        html += '<h2 style="color: #34495e; font-size: 20pt; margin: 15pt 0; text-align: center; font-weight: bold;">RELATORIO DE BATERIA</h2>'
        html += f'<p style="font-size: 11pt; color: #666; text-align: center;">Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>'
        html += '<hr style="border: none; border-top: 1pt solid #ddd; margin: 15pt 0;">'
        if device_info:
            html += '<h3 style="font-size: 14pt; color: #2c3e50; margin: 15pt 0; font-weight: bold;">DISPOSITIVO</h3>'
            html += '<table style="width: 100%; font-size: 12pt; border-collapse: collapse;">'
            for key, value in device_info.items():
                html += f'<tr><td style="padding: 8pt; border-bottom: 1pt solid #ddd; width: 40%;"><b>{key}:</b></td><td style="padding: 8pt; border-bottom: 1pt solid #ddd;">{value}</td></tr>'
            html += '</table>'
        html += '<h3 style="font-size: 14pt; color: #2c3e50; margin: 20pt 0 12pt 0; font-weight: bold;">BATERIA</h3>'
        html += '<table style="width: 100%; font-size: 12pt; border-collapse: collapse;">'
        for key, value in battery_info.items():
            html += f'<tr><td style="padding: 8pt; border-bottom: 1pt solid #ddd; width: 40%;"><b>{key}:</b></td><td style="padding: 8pt; border-bottom: 1pt solid #ddd;">{value}</td></tr>'
        html += '</table>'
        html += '\n        <div style="margin-top: 30pt;">\n            <h3 style="font-size: 12pt; color: #2c3e50; font-weight: bold;">OBSERVACOES:</h3>\n            <div style="border: 1pt solid #ddd; min-height: 60pt; padding: 8pt; margin-top: 8pt;"></div>\n        </div>\n        <table style="width: 100%; margin-top: 40pt;">\n            <tr>\n                <td style="width: 45%; text-align: center;">\n                    <p style="font-size: 11pt; margin: 0;">Assinatura Cliente:</p>\n                    <div style="border-bottom: 1pt solid #333; margin-top: 30pt; width: 80%; margin-left: auto; margin-right: auto;"></div>\n                </td>\n                <td style="width: 10%;"></td>\n                <td style="width: 45%; text-align: center;">\n                    <p style="font-size: 11pt; margin: 0;">Assinatura Tecnico:</p>\n                    <div style="border-bottom: 1pt solid #333; margin-top: 30pt; width: 80%; margin-left: auto; margin-right: auto;"></div>\n                </td>\n            </tr>\n        </table>\n        '
        html += self._get_footer_html()
        return self._generate_pdf(html, 'relatorio_bateria', parent)
    def _generate_pdf(self, html: str, filename_prefix: str, parent=None) -> bool:
        '''
Gera PDF e abre automaticamente no visualizador padrao.
Args:
    html: Conteudo HTML para converter
    filename_prefix: Prefixo do nome do arquivo
    parent: Widget pai
Returns:
    bool: True se gerou e abriu, False se falhou
'''
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{filename_prefix}_{timestamp}.pdf'
            reports_dir = os.path.join(os.path.expanduser('~'), 'Documents', 'TechUnion_Relatorios')
            os.makedirs(reports_dir, exist_ok=True)
            pdf_path = os.path.join(reports_dir, filename)
            printer = QPrinter(QPrinter.ScreenResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(pdf_path)
            printer.setPageSize(QPrinter.A4)
            printer.setPageMargins(20, 20, 20, 20, QPrinter.Millimeter)
            doc = QTextDocument()
            doc.setDefaultFont(QFont('Arial', 12))
            page_rect = printer.pageRect(QPrinter.Point)
            doc.setPageSize(page_rect.size())
            doc.setHtml(html)
            doc.print_(printer)
            logger.info(f'PDF gerado: {pdf_path}')
            QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_path))
            QMessageBox.information(parent, 'PDF Gerado', f'Relatorio salvo em:\n{pdf_path}\n\nO arquivo foi aberto automaticamente.')
            return True
        except Exception as e:
            logger.error(f'Erro ao gerar PDF: {e}')
            QMessageBox.critical(parent, 'Erro', f'Erro ao gerar PDF:\n{str(e)}')
            return False
