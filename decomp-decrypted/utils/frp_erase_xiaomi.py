import sys
import os
import time
import logging
import threading
from datetime import datetime
from pathlib import Path
from PyQt5.QtCore import (Qt, pyqtSignal, QObject, pyqtSlot, QThread, QMetaType)
from PyQt5.QtGui import (QTextCursor, QFont, QColor)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel, QFileDialog, QMessageBox, QGroupBox, QProgressBar, QLineEdit, QCheckBox, QScrollArea)
try:
    from PyQt5.QtCore import qRegisterMetaType
    qRegisterMetaType('QTextCursor')
except:
    pass
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'app', 'views', 'mtk'))
try:
    from mtkclient.Library.mtk_class import Mtk
    from mtkclient.Library.DA.mtk_da_handler import DaHandler
    from mtkclient.Library.gpt import GptSettings
    from mtkclient.config.mtk_config import MtkConfig
except ImportError as e:
    print('================================================================================')
    print('ERRO CR├ìTICO: Depend├¬ncias do mtkclient n├úo encontradas!')
    print('================================================================================')
    print(f'Detalhe do erro: {e}')
    print('\nVerifique o path do mtkclient')
    print('================================================================================')
    sys.exit(1)
class DeviceHandler(QObject):
    sendToLogSignal = pyqtSignal(str)
    updateStatusSignal = pyqtSignal(str)
    sendToProgressSignal = pyqtSignal(int)
    def __init__(self, loglevel=logging.INFO):
        super().__init__(None)
        config = MtkConfig(loglevel=loglevel, gui=self.sendToLogSignal, guiprogress=self.sendToProgressSignal, update_status_text=self.updateStatusSignal)
        config.gpt_settings = GptSettings(gpt_num_part_entries='0', gpt_part_entry_size='0', gpt_part_entry_start_lba='0')
        config.reconnect = True
        config.uartloglevel = 2
        self.mtk = Mtk(config=config, loglevel=loglevel)
        self.da_handler = DaHandler(self.mtk, loglevel=loglevel)
class ConnectionThread(QThread):
    deviceConnectedSignal = pyqtSignal(dict)
    deviceErrorSignal = pyqtSignal(str)
    updateGuiSignal = pyqtSignal()
    def __init__(self, devhandler):
        super().__init__(None)
        self.devhandler = devhandler
        self.phone_info = {'chipset': '', 'bootMode': '', 'daInit': False, 'cdcInit': False}
    def run(self):
        try:
            mtk_class = self.devhandler.mtk
            da_handler = self.devhandler.da_handler
            self.devhandler.sendToLogSignal.emit('Aguardando dispositivo MTK...')
            self.devhandler.sendToLogSignal.emit('Conecte o aparelho em modo BROM/Download')
            if not mtk_class.port.cdc.connect():
                mtk_class.preloader.init()
            else:
                self.phone_info['cdcInit'] = True
            self.phone_info['chipset'] = str(mtk_class.config.chipconfig.name) + ' (' + str(mtk_class.config.chipconfig.description) + ')'
            try:
                hwcode = getattr(mtk_class.config, 'hwcode', 0)
                hw_sub = getattr(mtk_class.config, 'hw_sub_code', 0)
                hwver = getattr(mtk_class.config, 'hwver', 0)
                swver = getattr(mtk_class.config, 'swver', 0)
                self.devhandler.sendToLogSignal.emit('')
                self.devhandler.sendToLogSignal.emit('============================================================')
                self.devhandler.sendToLogSignal.emit('[DEVICE INFO] Dispositivo Conectado:')
                self.devhandler.sendToLogSignal.emit('============================================================')
                self.devhandler.sendToLogSignal.emit(f'  Chipset:       {mtk_class.config.chipconfig.name}')
                self.devhandler.sendToLogSignal.emit(f'  Descri├º├úo:     {mtk_class.config.chipconfig.description}')
                self.devhandler.sendToLogSignal.emit(f'  HW Code:       0x{hwcode:04X}')
                self.devhandler.sendToLogSignal.emit(f'  HW Version:    0x{hwver:04X}')
                self.devhandler.sendToLogSignal.emit(f'  SW Version:    0x{swver:04X}')
                self.devhandler.sendToLogSignal.emit('============================================================')
            except Exception as e:
                pass
            else:
                self.updateGuiSignal.emit()
                self.devhandler.sendToLogSignal.emit('Carregando Download Agent (DA)...')
                mtk_class = da_handler.configure_da(mtk_class, preloader=None)
                if mtk_class:
                    self.phone_info['daInit'] = True
                    self.phone_info['chipset'] = str(mtk_class.config.chipconfig.name) + ' (' + str(mtk_class.config.chipconfig.description) + ')'
                    if mtk_class.config.is_brom:
                        self.phone_info['bootMode'] = 'Bootrom mode'
                    elif mtk_class.config.chipconfig.damode:
                        self.phone_info['bootMode'] = 'DA mode'
                    else:
                        self.phone_info['bootMode'] = 'Preloader mode'
                    self.devhandler.sendToLogSignal.emit(f'Ô£à DA carregado com sucesso! ({self.phone_info['bootMode']})')
                    self.deviceConnectedSignal.emit(self.phone_info)
                    return
                self.phone_info['cantConnect'] = True
                self.deviceErrorSignal.emit('Falha ao carregar Download Agent')
        except Exception as e:
            self.deviceErrorSignal.emit(f'Erro na conex├úo: {str(e)}')
class FRPEraseGUI(QMainWindow):
    showSuccessSignal = pyqtSignal(str)
    showErrorSignal = pyqtSignal(str)
    enableFrpButtonSignal = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.setWindowTitle('XIAOMI FRP MTK - TECH UNION SOLUTIONS')
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet('background-color: #2b2b2b;')
        self.device_connected = False
        self.backup_dir = str(Path.home() / 'Desktop')
        self.devhandler = None
        self.connection_thread = None
        self.partition_checkboxes = {}
        self.guid_gpt = None
        self.showSuccessSignal.connect(self.show_success_message)
        self.showErrorSignal.connect(self.show_error_message)
        self.enableFrpButtonSignal.connect((lambda: self.frp_btn.setEnabled(True)))
        self.setup_ui()
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        header = QLabel('­ƒöº XIAOMI FRP MTK--Ferramenta em teste - Use por sua conta e risco')
        header.setStyleSheet('\n            font-size: 20px;\n            font-weight: bold;\n            color: #00ff00;\n            background-color: #1e1e1e;\n            padding: 15px;\n        ')
        main_layout.addWidget(header)
        log_group = QGroupBox('­ƒôï Logs da Opera├º├úo')
        log_group.setStyleSheet('\n            QGroupBox {\n                color: #ffffff;\n                font-size: 14px;\n                font-weight: bold;\n                border: 2px solid #00ff00;\n                border-radius: 5px;\n                margin-top: 10px;\n                padding-top: 10px;\n            }\n            QGroupBox::title {\n                subcontrol-origin: margin;\n                left: 10px;\n                padding: 0 5px;\n            }\n        ')
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("\n            background-color: #1e1e1e;\n            color: #00ff00;\n            font-family: 'Consolas', 'Courier New', monospace;\n            font-size: 11px;\n            border: 1px solid #444;\n        ")
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        backup_group = QGroupBox('­ƒÆ¥ Configura├º├úo de Backup')
        backup_group.setStyleSheet('\n            QGroupBox {\n                color: #ffffff;\n                font-size: 12px;\n                border: 2px solid #ffa500;\n                border-radius: 5px;\n                margin-top: 10px;\n                padding-top: 10px;\n            }\n        ')
        backup_layout = QHBoxLayout()
        self.backup_path_edit = QLineEdit(self.backup_dir)
        self.backup_path_edit.setReadOnly(True)
        self.backup_path_edit.setStyleSheet('\n            background-color: #333;\n            color: #fff;\n            padding: 8px;\n            border: 1px solid #555;\n        ')
        select_backup_btn = QPushButton('Selecionar Pasta')
        select_backup_btn.clicked.connect(self.select_backup_directory)
        select_backup_btn.setStyleSheet('\n            QPushButton {\n                background-color: #ffa500;\n                color: #000;\n                font-weight: bold;\n                padding: 8px 15px;\n                border-radius: 5px;\n            }\n            QPushButton:hover {\n                background-color: #ffb533;\n            }\n        ')
        backup_layout.addWidget(self.backup_path_edit)
        backup_layout.addWidget(select_backup_btn)
        backup_group.setLayout(backup_layout)
        main_layout.addWidget(backup_group)
        partition_group = QGroupBox('­ƒùé´©Å Parti├º├Áes do Dispositivo')
        partition_group.setStyleSheet('\n            QGroupBox {\n                color: #ffffff;\n                font-size: 14px;\n                font-weight: bold;\n                border: 2px solid #0099ff;\n                border-radius: 5px;\n                margin-top: 10px;\n                padding-top: 10px;\n            }\n            QGroupBox::title {\n                subcontrol-origin: margin;\n                left: 10px;\n                padding: 0 5px;\n            }\n        ')
        partition_layout = QVBoxLayout()
        self.partition_scroll = QScrollArea()
        self.partition_scroll.setWidgetResizable(True)
        self.partition_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.partition_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.partition_scroll.setStyleSheet('\n            QScrollArea {\n                background-color: #1e1e1e;\n                border: 1px solid #444;\n            }\n        ')
        self.partition_scroll.setMinimumHeight(200)
        self.partition_scroll.setMaximumHeight(300)
        self.partition_container = QWidget()
        self.partition_layout_inner = QVBoxLayout()
        self.partition_container.setLayout(self.partition_layout_inner)
        self.partition_scroll.setWidget(self.partition_container)
        partition_layout.addWidget(self.partition_scroll)
        partition_group.setLayout(partition_layout)
        main_layout.addWidget(partition_group)
        button_layout = QHBoxLayout()
        self.connect_btn = QPushButton('­ƒöî Conectar Dispositivo')
        self.connect_btn.clicked.connect(self.start_connection)
        self.connect_btn.setStyleSheet('\n            QPushButton {\n                background-color: #0066cc;\n                color: #fff;\n                font-size: 14px;\n                font-weight: bold;\n                padding: 12px 20px;\n                border-radius: 5px;\n            }\n            QPushButton:hover {\n                background-color: #0080ff;\n            }\n            QPushButton:disabled {\n                background-color: #555;\n                color: #888;\n            }\n        ')
        self.frp_btn = QPushButton('­ƒùæ´©Å Apagar FRP')
        self.frp_btn.clicked.connect(self.erase_frp)
        self.frp_btn.setEnabled(False)
        self.frp_btn.setStyleSheet('\n            QPushButton {\n                background-color: #cc0000;\n                color: #fff;\n                font-size: 14px;\n                font-weight: bold;\n                padding: 12px 20px;\n                border-radius: 5px;\n            }\n            QPushButton:hover {\n                background-color: #ff0000;\n            }\n            QPushButton:disabled {\n                background-color: #555;\n                color: #888;\n            }\n        ')
        button_layout.addWidget(self.connect_btn)
        button_layout.addWidget(self.frp_btn)
        main_layout.addLayout(button_layout)
        self.log('================================================================================', 'INFO')
        self.log('TECH UNION SOLUTIONS - XIAOMI FRP MTK', 'INFO')
        self.log('­ƒº¬ Ferramenta em teste - Use por sua conta e risco', 'WARNING')
        self.log('================================================================================', 'INFO')
        self.log(f'­ƒôü Backups ser├úo salvos em: {self.backup_dir}', 'INFO')
        self.log("­ƒÆí Voc├¬ pode alterar a pasta de backup clicando em 'Selecionar Pasta'", 'INFO')
        self.log('Aguardando comando para conectar...', 'INFO')
    def log(self, message, level='INFO'):
        timestamp = datetime.now().strftime('%H:%M:%S')
        color_map = {'INFO': '#00ff00', 'WARNING': '#ffaa00', 'ERROR': '#ff0000', 'SUCCESS': '#00ff00'}
        color = color_map.get(level, '#ffffff')
        self.log_text.append(f'<span style="color: {color};">[{timestamp}] [{level}] {message}</span>')
        self.log_text.moveCursor(QTextCursor.End)
    def select_backup_directory(self):
        directory = QFileDialog.getExistingDirectory(self, 'Selecionar Pasta de Backup', self.backup_dir)
        if directory:
            self.backup_dir = directory
            self.backup_path_edit.setText(directory)
            self.log(f'Diret├│rio de backup alterado: {directory}', 'INFO')
    def start_connection(self):
        if self.device_connected:
            self.log('Dispositivo j├í conectado!', 'WARNING')
            return
        self.log('================================================================================', 'INFO')
        self.log('­ƒÄ» INICIANDO ESCUTA DE DISPOSITIVO MTK', 'INFO')
        self.log('================================================================================', 'INFO')
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText('ÔÅ│ Aguardando...')
        self.devhandler = DeviceHandler(loglevel=logging.INFO)
        self.devhandler.sendToLogSignal.connect((lambda msg: self.log(msg, 'INFO')))
        self.devhandler.updateStatusSignal.connect((lambda msg: self.log(f'Status: {msg}', 'INFO')))
        self.connection_thread = ConnectionThread(self.devhandler)
        self.connection_thread.deviceConnectedSignal.connect(self.on_device_connected)
        self.connection_thread.deviceErrorSignal.connect(self.on_device_error)
        self.connection_thread.start()
    @pyqtSlot(dict)
    def on_device_connected(self, phone_info):
        self.device_connected = True
        self.log('================================================================================', 'SUCCESS')
        self.log('Ô£à DISPOSITIVO CONECTADO COM SUCESSO!', 'SUCCESS')
        self.log('================================================================================', 'SUCCESS')
        self.log(f'Chipset: {phone_info['chipset']}', 'INFO')
        self.log(f'Modo: {phone_info['bootMode']}', 'INFO')
        self.connect_btn.setText('Ô£à Conectado')
        self.connect_btn.setEnabled(False)
        self.frp_btn.setEnabled(True)
        self.get_partitions()
    @pyqtSlot(str)
    def on_device_error(self, error_msg):
        self.log(f'ÔØî ERRO: {error_msg}', 'ERROR')
        self.connect_btn.setText('­ƒöî Conectar Dispositivo')
        self.connect_btn.setEnabled(True)
    def get_partitions(self):
        try:
            self.log('\n================================================================================', 'INFO')
            self.log('­ƒô▒ LENDO PARTI├ç├òES DO DISPOSITIVO', 'INFO')
            self.log('================================================================================', 'INFO')
            data, self.guid_gpt = self.devhandler.da_handler.mtk.daloader.get_gpt()
            if self.guid_gpt is None:
                self.log('ÔØî Erro ao ler tabela de parti├º├Áes (GPT)!', 'ERROR')
                return
            self.log(f'Ô£à GPT lida com sucesso! {len(self.guid_gpt.partentries)} parti├º├Áes encontradas.', 'SUCCESS')
            for i in reversed(range(self.partition_layout_inner.count())):
                self.partition_layout_inner.itemAt(i).widget().deleteLater()
            self.partition_checkboxes = {}
            for partition in self.guid_gpt.partentries:
                self.partition_checkboxes[partition.name] = {}
                self.partition_checkboxes[partition.name]['size'] = partition.sectors * self.guid_gpt.sectorsize
                checkbox = QCheckBox()
                size_str = self.convert_size(partition.sectors * self.guid_gpt.sectorsize)
                checkbox.setText(f'{partition.name} ({size_str})')
                part_name_lower = partition.name.lower()
                if part_name_lower == 'frp':
                    checkbox.setChecked(True)
                    checkbox.setEnabled(True)
                    checkbox.setStyleSheet('\n                        QCheckBox {\n                            color: #00ff00;\n                            font-size: 12px;\n                            font-weight: bold;\n                            padding: 5px;\n                        }\n                        QCheckBox::indicator {\n                            width: 18px;\n                            height: 18px;\n                        }\n                        QCheckBox::indicator:checked {\n                            border: 2px solid #00ff00;\n                            background-color: #00ff00;\n                        }\n                    ')
                    self.log(f'­ƒÄ» Parti├º├úo FRP encontrada e marcada: {size_str}', 'SUCCESS')
                elif part_name_lower == 'userdata':
                    checkbox.setChecked(False)
                    checkbox.setEnabled(True)
                    checkbox.setStyleSheet('\n                        QCheckBox {\n                            color: #ffaa00;\n                            font-size: 12px;\n                            padding: 5px;\n                        }\n                        QCheckBox::indicator {\n                            width: 18px;\n                            height: 18px;\n                        }\n                        QCheckBox::indicator:unchecked {\n                            border: 2px solid #ffaa00;\n                            background-color: #1e1e1e;\n                        }\n                        QCheckBox::indicator:checked {\n                            border: 2px solid #ffaa00;\n                            background-color: #ffaa00;\n                        }\n                    ')
                    self.log(f'ÔÜá´©Å Userdata dispon├¡vel (opcional): {size_str}', 'WARNING')
                else:
                    checkbox.setChecked(False)
                    checkbox.setEnabled(False)
                    checkbox.setStyleSheet('\n                        QCheckBox {\n                            color: #666666;\n                            font-size: 12px;\n                            padding: 5px;\n                        }\n                        QCheckBox::indicator {\n                            width: 18px;\n                            height: 18px;\n                        }\n                        QCheckBox::indicator:disabled {\n                            border: 2px solid #333333;\n                            background-color: #1e1e1e;\n                        }\n                    ')
                self.partition_checkboxes[partition.name]['box'] = checkbox
                self.partition_layout_inner.addWidget(checkbox)
                continue
            self.log(f'\nÔ£à {len(self.guid_gpt.partentries)} parti├º├Áes listadas!', 'SUCCESS')
            self.log('­ƒÄ» FRP: Marcada para apagar (obrigat├│ria)', 'INFO')
            self.log('ÔÜá´©Å Userdata: Dispon├¡vel para marcar (opcional)', 'INFO')
            self.log('­ƒöÆ Outras parti├º├Áes: Protegidas (n├úo podem ser marcadas)', 'INFO')
            return
        except Exception as e:
            self.log(f'ÔØî Erro ao ler parti├º├Áes: {e}', 'ERROR')
            import traceback
            self.log(traceback.format_exc(), 'ERROR')
    def convert_size(self, size_bytes):
        if size_bytes <= 0:
            return '0B'
        import math
        size_name = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f'{s} {size_name[i]}'
    @pyqtSlot(str)
    def show_success_message(self, message):
        QMessageBox.information(self, 'Sucesso', message)
    @pyqtSlot(str)
    def show_error_message(self, message):
        QMessageBox.critical(self, 'Erro', message)
    def erase_frp(self):
        reply = QMessageBox.question(self, 'Confirmar Apagamento de FRP', 'ÔÜá´©Å ATEN├ç├âO!\n\nEsta opera├º├úo ir├í:\n1. Fazer backup da parti├º├úo FRP\n2. Apagar completamente o FRP\n\nDeseja continuar?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            self.log('Opera├º├úo cancelada pelo usu├írio.', 'WARNING')
            return
        self.log('\n================================================================================', 'INFO')
        self.log('­ƒùæ´©Å INICIANDO APAGAMENTO DE FRP', 'INFO')
        self.log('================================================================================', 'INFO')
        self.frp_btn.setEnabled(False)
        frp_thread = threading.Thread(target=self._erase_frp_thread)
        frp_thread.daemon = True
        frp_thread.start()
    def _erase_frp_thread(self):
        try:
            from unittest import mock
            partitions_to_erase = []
            for part_name, part_data in self.partition_checkboxes.items():
                if part_data['box'].isChecked():
                    partitions_to_erase.append({'name': part_name, 'size': part_data['size']})
            if not partitions_to_erase:
                self.log('ÔØî ERRO: Nenhuma parti├º├úo marcada para apagar!', 'ERROR')
                self.enableFrpButtonSignal.emit()
                return
            self.log(f'­ƒôï Parti├º├Áes marcadas para apagar: {len(partitions_to_erase)}', 'INFO')
            for part in partitions_to_erase:
                size_str = self.convert_size(part['size'])
                self.log(f'   - {part['name']} ({size_str})', 'INFO')
            for idx, part in enumerate(partitions_to_erase, 1):
                self.log(f'\n[{idx}/{len(partitions_to_erase)}] Processando: {part['name']}', 'INFO')
                needs_backup = part['name'].lower() != 'userdata'
                if needs_backup:
                    self.log(f"1´©ÅÔâú Fazendo backup da parti├º├úo '{part['name']}'...", 'INFO')
                    backup_folder = os.path.join(self.backup_dir, f'FRP_Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}')
                    os.makedirs(backup_folder, exist_ok=True)
                    backup_file = os.path.join(backup_folder, f'{part['name']}.bin')
            try:
                variables = mock.Mock()
                variables.partitionname = part['name']
                variables.parttype = None
                variables.filename = backup_file
                self.log(f'   Lendo {self.convert_size(part['size'])}...', 'INFO')
                self.devhandler.da_handler.handle_da_cmds(self.devhandler.mtk, 'r', variables)
                if os.path.exists(backup_file) and os.path.getsize(backup_file) > 0:
                    self.log(f'   Ô£à Backup salvo: {backup_file}', 'SUCCESS')
            except Exception as e:
                self.log(f'   ÔØî Erro no backup: {e}', 'ERROR')
                self.log('   ÔÜá´©Å Continuando sem backup...', 'WARNING')
        except Exception as e:
            self.log(f'\nÔØî ERRO CR├ìTICO ao apagar FRP: {e}', 'ERROR')
            import traceback
            self.log(traceback.format_exc(), 'ERROR')
            error_msg = f'Erro cr├¡tico ao apagar FRP:\n{e}\n\nVerifique os logs para mais detalhes.'
            self.showErrorSignal.emit(error_msg)
        self.log('\n================================================================================', 'SUCCESS')
        self.log('Ô£à OPERA├ç├âO DE FRP CONCLU├ìDA COM SUCESSO!', 'SUCCESS')
        self.log('================================================================================', 'SUCCESS')
        has_backups = any((part['name'].lower() != 'userdata' for part in partitions_to_erase))
        if has_backups:
            self.log('\n­ƒôü Backups salvos em:', 'INFO')
            self.log(f'   {backup_folder}', 'INFO')
            self.log('\n­ƒÆí DICA: Backups ficaram no Desktop (ou pasta escolhida)', 'INFO')
        else:
            self.log('\nÔÜá´©Å Nenhum backup criado (userdata = factory reset)', 'WARNING')
        if has_backups:
            success_msg = f'Ô£à Opera├º├úo conclu├¡da com sucesso!\n\n­ƒôü Backups salvos em:\n{backup_folder}\n\n­ƒÆ¥ Localiza├º├úo: Desktop (ou pasta escolhida)\n\nO dispositivo est├í pronto para uso.'
        else:
            success_msg = 'Ô£à Opera├º├úo conclu├¡da com sucesso!\n\nFactory reset aplicado (sem backup).\n\nO dispositivo est├í pronto para uso.'
        self.showSuccessSignal.emit(success_msg)
        self.enableFrpButtonSignal.emit()
def main():
    app = QApplication(sys.argv)
    window = FRPEraseGUI()
    window.show()
    sys.exit(app.exec_())
if __name__ == '__main__':
    main()
