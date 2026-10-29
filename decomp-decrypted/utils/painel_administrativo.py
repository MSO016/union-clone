from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
import os
import shutil
from app.utils.user_database import UserDatabaseManager
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED
class PainelAdministrativo(QMainWindow):
    def __init__(self):
        super().__init__()
        icon = QIcon('app/resources/icon.png')
        self.setWindowIcon(icon)
        self.user_db = UserDatabaseManager()
        self.setup_ui()
        self.load_users()
    def setup_ui(self):
        self.setWindowTitle('RESTORECELL - Painel Administrativo')
        self.setMinimumSize(1000, 600)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        header = QHBoxLayout()
        title = QLabel('Painel Administrativo')
        title.setStyleSheet('\n            font-size: 24px;\n            font-weight: bold;\n            color: #1976D2;\n            margin: 20px 0;\n        ')
        header.addWidget(title)
        header.addStretch()
        btn_update = QPushButton('­ƒôÑ Atualizar Base de Solu├º├Áes')
        btn_update.setStyleSheet('\n            QPushButton {\n                background-color: #4CAF50;\n                color: white;\n                padding: 10px 20px;\n                border-radius: 5px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #45a049;\n            }\n        ')
        btn_update.clicked.connect(self.update_solutions_db)
        header.addWidget(btn_update)
        btn_create_package = QPushButton('­ƒôª Criar Pacote de Atualiza├º├úo')
        btn_create_package.setStyleSheet('\n            QPushButton {\n                background-color: #2196F3;\n                color: white;\n                padding: 10px 20px;\n                border-radius: 5px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #1976D2;\n            }\n        ')
        btn_create_package.clicked.connect(self.criar_pacote_atualizacao)
        header.addWidget(btn_create_package)
        layout.addLayout(header)
        tabs = QTabWidget()
        users_tab = QWidget()
        users_layout = QVBoxLayout(users_tab)
        btn_new_user = QPushButton('Ô×ò Novo Usu├írio')
        btn_new_user.setStyleSheet('\n            QPushButton {\n                background-color: #1976D2;\n                color: white;\n                padding: 10px 20px;\n                border-radius: 5px;\n                font-weight: bold;\n                margin-bottom: 20px;\n            }\n            QPushButton:hover {\n                background-color: #1565C0;\n            }\n        ')
        btn_new_user.clicked.connect(self.create_user)
        users_layout.addWidget(btn_new_user)
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(7)
        self.users_table.setHorizontalHeaderLabels(['Usu├írio', 'Admin', 'Hardware ID', '├Ültimo Acesso', 'Reset HW', 'Reset Senha', 'A├º├Áes'])
        header = self.users_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        self.users_table.setColumnWidth(4, 100)
        self.users_table.setColumnWidth(5, 100)
        self.users_table.setColumnWidth(6, 100)
        users_layout.addWidget(self.users_table)
        tabs.addTab(users_tab, 'Usu├írios')
        logs_tab = QWidget()
        logs_layout = QVBoxLayout(logs_tab)
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        logs_layout.addWidget(self.logs_text)
        tabs.addTab(logs_tab, 'Logs')
        layout.addWidget(tabs)
    def create_user(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Novo Usu├írio')
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        username = QLineEdit()
        password = QLineEdit()
        password.setEchoMode(QLineEdit.Password)
        is_admin = QCheckBox('Usu├írio Administrador')
        form.addRow('Usu├írio:', username)
        form.addRow('Senha:', password)
        form.addRow('', is_admin)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        btn_save = QPushButton('Salvar')
        btn_cancel = QPushButton('Cancelar')
        buttons.addWidget(btn_save)
        buttons.addWidget(btn_cancel)
        layout.addLayout(buttons)
        def save():
            try:
                self.user_db.create_user(username.text(), password.text(), is_admin.isChecked())
                self.log_action(f'Usu├írio criado: {username.text()}')
                self.load_users()
                dialog.accept()
                return
            except Exception as e:
                QMessageBox.critical(dialog, 'Erro', str(e))
        btn_save.clicked.connect(save)
        btn_cancel.clicked.connect(dialog.reject)
        dialog.exec_()
    def reset_hardware(self, username):
        reply = QMessageBox.question(self, 'Confirmar Reset', f'Deseja realmente resetar o hardware do usu├írio {username}?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.user_db.reset_hardware(username)
                self.log_action(f'Hardware resetado: {username}')
                self.load_users()
                QMessageBox.information(self, 'Sucesso', 'Hardware resetado com sucesso!\nO usu├írio poder├í acessar de uma nova m├íquina.')
            except Exception as e:
                QMessageBox.critical(self, 'Erro', str(e))
    def update_solutions_db(self):
        try:
            file_name, _ = QFileDialog.getOpenFileName(self, 'Selecionar Nova Base', '', 'Banco SQLite (*.db)')
            if file_name:
                if os.path.exists('app/database/base.db'):
                    backup_path = 'app/database/base.db.backup'
                    shutil.copy2('app/database/base.db', backup_path)
                shutil.copy2(file_name, 'app/database/base.db')
                self.log_action('Base de solu├º├Áes atualizada')
                QMessageBox.information(self, 'Sucesso', 'Base de solu├º├Áes atualizada com sucesso!')
                return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', str(e))
    def load_users(self):
        try:
            users = self.user_db.get_all_users()
            self.users_table.setRowCount(len(users))
            btn_style = '\n                QPushButton {\n                    background-color: #2196F3;\n                    color: white;\n                    border: none;\n                    padding: 5px 10px;\n                    border-radius: 3px;\n                    font-weight: bold;\n                }\n                QPushButton:hover {\n                    background-color: #1976D2;\n                }\n            '
            delete_btn_style = '\n                QPushButton {\n                    background-color: #f44336;\n                    color: white;\n                    border: none;\n                    padding: 5px 10px;\n                    border-radius: 3px;\n                    font-weight: bold;\n                }\n                QPushButton:hover {\n                    background-color: #d32f2f;\n                }\n            '
            for row, user in enumerate(users):
                self.users_table.setItem(row, 0, QTableWidgetItem(user['username']))
                self.users_table.setItem(row, 1, QTableWidgetItem('Sim' if user['is_admin'] else 'N├úo'))
                self.users_table.setItem(row, 2, QTableWidgetItem(user['hardware_id'] or 'N├úo vinculado'))
                self.users_table.setItem(row, 3, QTableWidgetItem(user['last_login'] or 'Nunca'))
                btn_reset_hw = QPushButton('Reset')
                btn_reset_hw.setStyleSheet(btn_style)
                btn_reset_hw.clicked.connect((lambda checked, u=user['username']: self.reset_hardware(u)))
                self.users_table.setCellWidget(row, 4, btn_reset_hw)
                btn_reset_pwd = QPushButton('Reset')
                btn_reset_pwd.setStyleSheet(btn_style)
                btn_reset_pwd.clicked.connect((lambda checked, u=user['username']: self.reset_password(u)))
                self.users_table.setCellWidget(row, 5, btn_reset_pwd)
                btn_delete = QPushButton('ÔØî Excluir')
                btn_delete.setStyleSheet(delete_btn_style)
                btn_delete.clicked.connect((lambda checked, u=user['username']: self.delete_user(u)))
                self.users_table.setCellWidget(row, 6, btn_delete)
                if not user['is_admin']:
                    continue
                btn_reset_hw.setEnabled(False)
                btn_reset_pwd.setEnabled(False)
                btn_delete.setEnabled(False)
                continue
            return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao carregar usu├írios: {str(e)}')
    def reset_password(self, username):
        try:
            new_pass, ok = QInputDialog.getText(self, 'Nova Senha', f'Digite a nova senha para {username}:', QLineEdit.Password)
            if ok:
                if new_pass:
                    self.user_db.reset_password(username, new_pass)
                    self.log_action(f'Senha alterada: {username}')
                    QMessageBox.information(self, 'Sucesso', 'Senha alterada com sucesso!')
                    return
                return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', str(e))
    def log_action(self, action):
        timestamp = QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')
        log_entry = f'[{timestamp}] {action}\n'
        self.logs_text.append(log_entry)
        try:
            os.makedirs('logs', exist_ok=True)
            with open('logs/admin.log', 'a') as f:
                f.write(log_entry)
        except Exception as e:
            print(f'Erro ao salvar log: {e}')
    def criar_pacote_atualizacao(self):
        try:
            banco_path, _ = QFileDialog.getOpenFileName(self, 'Selecionar Banco de Dados', '', 'Banco SQLite (*.db)')
            if not banco_path:
                return
            password, ok = QInputDialog.getText(self, 'Senha do Pacote', 'Digite a senha para proteger o arquivo:', QLineEdit.Password)
            if not ok or not password:
                return
            save_path, _ = QFileDialog.getSaveFileName(self, 'Salvar Pacote de Atualiza├º├úo', 'update.zip', 'Arquivo ZIP (*.zip)')
            if not save_path:
                return
            if os.path.basename(save_path) != 'update.zip':
                save_path = os.path.join(os.path.dirname(save_path), 'update.zip')
            with ZipFile(save_path, 'w', compression=ZIP_DEFLATED) as zip_file:
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_db = os.path.join(temp_dir, 'base.db')
                    shutil.copy2(banco_path, temp_db)
                    zip_file.write(temp_db, arcname='base.db')
                    zip_file.setpassword(password.encode('utf-8'))
            self.log_action('Pacote de atualiza├º├úo criado')
            QMessageBox.information(self, 'Sucesso', 'Pacote de atualiza├º├úo criado com sucesso!')
        except Exception as e:
            QMessageBox.critical(self, 'Erro', str(e))
    def delete_user(self, username):
        try:
            reply = QMessageBox.question(self, 'Confirmar Exclus├úo', f'Tem certeza que deseja excluir o usu├írio {username}?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.user_db.delete_user(username)
                self.load_users()
                QMessageBox.information(self, 'Sucesso', f'Usu├írio {username} exclu├¡do com sucesso!')
                return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao excluir usu├írio: {str(e)}')
