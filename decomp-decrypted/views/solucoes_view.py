from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QScrollArea, QFrame, QGridLayout, QMessageBox, QDialog, QGroupBox, QApplication, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QSizePolicy, QMenuBar, QAction, QProgressDialog, QShortcut)
from PyQt5.QtCore import (Qt, QRectF, QTimer)
from PyQt5.QtGui import (QPixmap, QTransform, QPainter, QIcon, QKeySequence)
import sqlite3
import os
import tempfile
import subprocess
import pymysql
import fitz
from app.utils._app_cfg import db_config
from app.utils._security_crypto import encrypt_blob, decrypt_blob_safe
import webbrowser
from ..utils.translation_manager import TranslationManager
from .components.solution_filters_widget import SolutionFiltersWidget
from app.utils.window_protection import protect_window_from_capture_extended
from app.utils.screen_protection_config import pode_gravar_tela
class ImagemDialog(QDialog):
    def __init__(self, imagem_blob, parent=None, lista_imagens=None, indice_atual=0):
        super().__init__(parent)
        self.translation_manager = TranslationManager.get_instance()
        self.setWindowTitle(self.translation_manager.get_text('enlarged_preview'))
        self.setModal(True)
        self.is_admin = parent.is_admin if hasattr(parent, 'is_admin') else False
        self._lista_imagens = lista_imagens
        self._indice_atual = indice_atual
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        if not self.pode_gravar_tela():
            protect_window_from_capture_extended(self, True)
        layout = QVBoxLayout(self)
        self._tem_navegacao = self._lista_imagens is not None and len(self._lista_imagens) > 1
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing | QPainter.HighQualityAntialiasing)
        self.view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.view.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing, False)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        screen = QApplication.primaryScreen().size()
        self._max_width = int(screen.width() * 0.9)
        self._max_height = int(screen.height() * 0.9)
        if not self._carregar_imagem(imagem_blob):
            return
        _btn_style = '\n            QPushButton {\n                background-color: #2196F3;\n                color: white;\n                border: none;\n                padding: 8px 15px;\n                border-radius: 4px;\n                font-size: 13px;\n            }\n            QPushButton:hover { background-color: #1976D2; }\n        '
        _nav_btn_style = '\n            QPushButton {\n                background-color: #1565C0;\n                color: white;\n                border: none;\n                padding: 10px 20px;\n                border-radius: 4px;\n                font-weight: bold;\n                font-size: 15px;\n            }\n            QPushButton:hover { background-color: #0D47A1; }\n            QPushButton:disabled { background-color: #B0BEC5; color: #78909C; }\n        '
        controls_layout = QHBoxLayout()
        if self._tem_navegacao:
            self._btn_prev = QPushButton('ÔùÇ')
            self._btn_prev.setStyleSheet(_nav_btn_style)
            self._btn_prev.setFixedWidth(50)
            self._btn_prev.clicked.connect(self._ir_anterior)
            controls_layout.addWidget(self._btn_prev)
            self._label_posicao = QLabel()
            self._label_posicao.setStyleSheet('font-size: 13px; font-weight: bold; color: #2c3e50; padding: 0 5px;')
            self._label_posicao.setAlignment(Qt.AlignCenter)
            controls_layout.addWidget(self._label_posicao)
            self._btn_next = QPushButton('ÔûÂ')
            self._btn_next.setStyleSheet(_nav_btn_style)
            self._btn_next.setFixedWidth(50)
            self._btn_next.clicked.connect(self._ir_proximo)
            controls_layout.addWidget(self._btn_next)
            sep = QLabel('|')
            sep.setStyleSheet('color: #ccc; font-size: 18px; padding: 0 8px;')
            controls_layout.addWidget(sep)
            QShortcut(QKeySequence(Qt.Key_Left), self, self._ir_anterior)
            QShortcut(QKeySequence(Qt.Key_Right), self, self._ir_proximo)
        btn_zoom_in = QPushButton(self.translation_manager.get_text('zoom_in'))
        btn_zoom_in.setStyleSheet(_btn_style)
        btn_zoom_in.clicked.connect(self.zoom_in)
        btn_zoom_out = QPushButton(self.translation_manager.get_text('zoom_out'))
        btn_zoom_out.setStyleSheet(_btn_style)
        btn_zoom_out.clicked.connect(self.zoom_out)
        btn_reset = QPushButton(self.translation_manager.get_text('zoom_reset'))
        btn_reset.setStyleSheet(_btn_style)
        btn_reset.clicked.connect(self.reset_zoom)
        btn_fit = QPushButton(self.translation_manager.get_text('fit_to_window'))
        btn_fit.setStyleSheet(_btn_style)
        btn_fit.clicked.connect(self.fit_to_window)
        controls_layout.addWidget(btn_zoom_in)
        controls_layout.addWidget(btn_zoom_out)
        controls_layout.addWidget(btn_reset)
        controls_layout.addWidget(btn_fit)
        controls_layout.addStretch()
        layout.addWidget(self.view)
        layout.addLayout(controls_layout)
        self.resize(self._max_width, self._max_height)
        self.scale_factor = 1.0
        if self._tem_navegacao:
            self._atualizar_navegacao()
        QTimer.singleShot(100, self.fit_to_window)
    def _carregar_imagem(self, blob_data):
        try:
            pixmap = QPixmap()
            if not pixmap.loadFromData(blob_data):
                raise Exception('Falha ao carregar imagem')
            if pixmap.width() > self._max_width or pixmap.height() > self._max_height:
                scaled_pixmap = pixmap.scaled(self._max_width, self._max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                scaled_pixmap = pixmap
            self.scene.clear()
            self.pixmap_item = QGraphicsPixmapItem(scaled_pixmap)
            self.pixmap_item.setTransformationMode(Qt.SmoothTransformation)
            self.scene.addItem(self.pixmap_item)
            self.view.setScene(self.scene)
            self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
            self.scale_factor = 1.0
            return True
        except Exception:
            QMessageBox.critical(self, 'Erro', 'N├úo foi poss├¡vel carregar a imagem.')
            self.close()
            return False
    def _atualizar_navegacao(self):
        if not self._tem_navegacao:
            return
        total = len(self._lista_imagens)
        self._label_posicao.setText(f'{self._indice_atual + 1} de {total}')
        self._btn_prev.setEnabled(self._indice_atual > 0)
        self._btn_next.setEnabled(self._indice_atual < total - 1)
        nome_atual = self._lista_imagens[self._indice_atual][0]
        self.setWindowTitle(f'{nome_atual} ÔÇö {self._indice_atual + 1}/{total}')
    def _ir_anterior(self):
        if self._indice_atual > 0:
            self._indice_atual -= 1
            _, blob_data = self._lista_imagens[self._indice_atual]
            self._carregar_imagem(blob_data)
            self._atualizar_navegacao()
            QTimer.singleShot(50, self.fit_to_window)
    def _ir_proximo(self):
        if self._indice_atual < len(self._lista_imagens) - 1:
            self._indice_atual += 1
            _, blob_data = self._lista_imagens[self._indice_atual]
            self._carregar_imagem(blob_data)
            self._atualizar_navegacao()
            QTimer.singleShot(50, self.fit_to_window)
    def pode_gravar_tela(self):
        if self.is_admin:
            return True
        if hasattr(self.parent, 'user_domain') and self.parent.user_domain:
            return pode_gravar_tela(self.is_admin, self.parent.user_domain)
        return False
    def zoom_in(self):
        self.scale_image(1.25)
    def zoom_out(self):
        self.scale_image(0.8)
    def reset_zoom(self):
        self.scale_factor = 1.0
        self.view.resetTransform()
        self.view.setSceneRect(QRectF(self.pixmap_item.pixmap().rect()))
    def scale_image(self, factor):
        self.scale_factor *= factor
        self.view.scale(factor, factor)
    def fit_to_window(self):
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        self.scale_factor = 1.0
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'view'):
            if hasattr(self, 'scene'):
                self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
class DiagramaDialog(QDialog):
    def __init__(self, diagrama_blob, parent=None):
        super().__init__(parent)
        self.translation_manager = TranslationManager.get_instance()
        self.setWindowTitle(self.translation_manager.get_text('diagram_preview'))
        self.setModal(True)
        self.is_admin = parent.is_admin if hasattr(parent, 'is_admin') else False
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        if not self.pode_gravar_tela():
            protect_window_from_capture_extended(self, True)
        layout = QVBoxLayout(self)
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        try:
            try:
                self.doc = fitz.open(stream=diagrama_blob, filetype='pdf')
                self.current_page = 0
                self.total_pages = len(self.doc)
                self.is_pdf = True
                self.load_current_page()
            except:
                self.is_pdf = False
                pixmap = QPixmap()
                if not pixmap.loadFromData(diagrama_blob):
                    raise Exception('Falha ao carregar diagrama')
                self.load_image(pixmap)
        except Exception as e:
            QMessageBox.critical(self, 'Erro', 'N├úo foi poss├¡vel carregar o diagrama.')
            self.close()
        controls_layout = QHBoxLayout()
        btn_zoom_in = QPushButton(self.translation_manager.get_text('zoom_in'))
        btn_zoom_in.setStyleSheet('\n            QPushButton {\n                background-color: #2196F3;\n                color: white;\n                border: none;\n                padding: 8px 15px;\n                border-radius: 4px;\n            }\n            QPushButton:hover {\n                background-color: #1976D2;\n            }\n        ')
        btn_zoom_in.clicked.connect(self.zoom_in)
        btn_zoom_out = QPushButton(self.translation_manager.get_text('zoom_out'))
        btn_zoom_out.setStyleSheet('\n            QPushButton {\n                background-color: #2196F3;\n                color: white;\n                border: none;\n                padding: 8px 15px;\n                border-radius: 4px;\n            }\n            QPushButton:hover {\n                background-color: #1976D2;\n            }\n        ')
        btn_zoom_out.clicked.connect(self.zoom_out)
        btn_reset = QPushButton(self.translation_manager.get_text('zoom_reset'))
        btn_reset.setStyleSheet('\n            QPushButton {\n                background-color: #2196F3;\n                color: white;\n                border: none;\n                padding: 8px 15px;\n                border-radius: 4px;\n            }\n            QPushButton:hover {\n                background-color: #1976D2;\n            }\n        ')
        btn_reset.clicked.connect(self.reset_zoom)
        controls_layout.addWidget(btn_zoom_in)
        controls_layout.addWidget(btn_zoom_out)
        controls_layout.addWidget(btn_reset)
        if self.is_pdf:
            nav_layout = QHBoxLayout()
            self.btn_prev = QPushButton('ÔåÉ')
            self.btn_prev.setStyleSheet('\n                QPushButton {\n                    background-color: #2196F3;\n                    color: white;\n                    border: none;\n                    padding: 8px 15px;\n                    border-radius: 4px;\n                    font-size: 16px;\n                    font-weight: bold;\n                }\n                QPushButton:hover {\n                    background-color: #1976D2;\n                }\n                QPushButton:disabled {\n                    background-color: #BDBDBD;\n                }\n            ')
            self.btn_prev.clicked.connect(self.prev_page)
            self.page_label = QLabel(f'P├ígina {self.current_page + 1} de {self.total_pages}')
            self.page_label.setStyleSheet('font-size: 14px; margin: 0 10px;')
            self.btn_next = QPushButton('ÔåÆ')
            self.btn_next.setStyleSheet('\n                QPushButton {\n                    background-color: #2196F3;\n                    color: white;\n                    border: none;\n                    padding: 8px 15px;\n                    border-radius: 4px;\n                    font-size: 16px;\n                    font-weight: bold;\n                }\n                QPushButton:hover {\n                    background-color: #1976D2;\n                }\n                QPushButton:disabled {\n                    background-color: #BDBDBD;\n                }\n            ')
            self.btn_next.clicked.connect(self.next_page)
            nav_layout.addStretch()
            nav_layout.addWidget(self.btn_prev)
            nav_layout.addWidget(self.page_label)
            nav_layout.addWidget(self.btn_next)
            nav_layout.addStretch()
            controls_layout.addStretch()
            controls_layout.addLayout(nav_layout)
        controls_layout.addStretch()
        layout.addWidget(self.view)
        layout.addLayout(controls_layout)
        screen = QApplication.primaryScreen().size()
        self.resize(int(screen.width() * 0.8), int(screen.height() * 0.8))
        self.scale_factor = 1.0
        if self.is_pdf:
            self.update_nav_buttons()
    def load_current_page(self):
        if not self.is_pdf:
            return
        page = self.doc[self.current_page]
        zoom = 2.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_data = pix.tobytes()
        pixmap = QPixmap()
        pixmap.loadFromData(img_data)
        self.load_image(pixmap)
        if hasattr(self, 'page_label'):
            self.page_label.setText(f'P├ígina {self.current_page + 1} de {self.total_pages}')
            self.update_nav_buttons()
    def load_image(self, pixmap):
        screen = QApplication.primaryScreen().size()
        max_width = int(screen.width() * 0.8)
        max_height = int(screen.height() * 0.8)
        scale_factor = min(max_width / pixmap.width() if pixmap.width() > 0 else 1, max_height / pixmap.height() if pixmap.height() > 0 else 1)
        if scale_factor < 1:
            new_width = int(pixmap.width() * scale_factor)
            new_height = int(pixmap.height() * scale_factor)
            scaled_pixmap = pixmap.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            scaled_pixmap = pixmap
        self.scene.clear()
        self.pixmap_item = QGraphicsPixmapItem(scaled_pixmap)
        self.scene.addItem(self.pixmap_item)
        self.view.setScene(self.scene)
        self.reset_zoom()
    def next_page(self):
        if self.is_pdf:
            if self.current_page < self.total_pages - 1:
                self.current_page += 1
                self.load_current_page()
    def prev_page(self):
        if self.is_pdf:
            if self.current_page > 0:
                self.current_page -= 1
                self.load_current_page()
    def update_nav_buttons(self):
        if self.is_pdf:
            self.btn_prev.setEnabled(self.current_page > 0)
            self.btn_next.setEnabled(self.current_page < self.total_pages - 1)
    def zoom_in(self):
        self.scale_image(1.25)
    def zoom_out(self):
        self.scale_image(0.8)
    def reset_zoom(self):
        self.scale_factor = 1.0
        self.view.resetTransform()
        self.view.setSceneRect(QRectF(self.pixmap_item.pixmap().rect()))
    def scale_image(self, factor):
        self.scale_factor *= factor
        self.view.scale(factor, factor)
    def pode_gravar_tela(self):
        if self.is_admin:
            return True
        if hasattr(self.parent, 'user_domain') and self.parent.user_domain:
            return pode_gravar_tela(self.is_admin, self.parent.user_domain)
        return False
    def closeEvent(self, event):
        if self.is_pdf:
            self.doc.close()
        super().closeEvent(event)
class SolucoesWindow(QMainWindow):
    _SOL_CARDS_MIN_W = 240
    _SOL_CARDS_SPACING = 15
    _SOL_CARDS_MAX_COLS = 4
    _SOL_CARDS_MIN_COLS = 1
    def __init__(self, marca, parent=None):
        super().__init__(parent)
        icon = QIcon('app/resources/icon.png')
        self.setWindowIcon(icon)
        self.marca = marca
        self.parent = parent
        from ..utils.path_manager import PathManager
        self.db_path = PathManager.get_database_path('base.db')
        self.translation_manager = TranslationManager.get_instance()
        self.is_admin = parent.is_admin if hasattr(parent, 'is_admin') else False
        self.mysql_config = db_config(cursorclass=pymysql.cursors.DictCursor, ssl={'ca': None}, ssl_verify_cert=False)
        self.search_timer = None
        self.last_search_time = 0
        self.search_delay = 500
        self.cached_solutions = []
        self._sol_cards_widgets_ordem = []
        self._sol_cards_cols_atual = 0
        self._cards_scroll_area = None
        self._sol_resize_timer = None
        self.translation_manager.language_changed.connect(self.refresh_interface)
        if not self.pode_gravar_tela():
            protect_window_from_capture_extended(self, True)
        self.setup_ui()
        self._loading_label = QLabel('Carregando solucoes...')
        self._loading_label.setStyleSheet('font-size: 16px; color: #666; padding: 40px;')
        self._loading_label.setAlignment(Qt.AlignCenter)
        self.grid_layout.addWidget(self._loading_label, 0, 0, 1, 3)
        self.carregar_solucoes()
    def pode_gravar_tela(self):
        if self.is_admin:
            return True
        if hasattr(self.parent, 'user_domain') and self.parent.user_domain:
            return pode_gravar_tela(self.is_admin, self.parent.user_domain)
        return False
    def voltar(self):
        self.close()
        if self.parent:
            self.parent.show()
    def _calcular_colunas_solucoes(self) -> int:
        try:
            scroll = getattr(self, '_cards_scroll_area', None)
            if scroll is None:
                return 3
            avail = scroll.viewport().width()
            if avail <= 0:
                avail = max(0, self.width() - 320 - 40)
            min_w = self._SOL_CARDS_MIN_W
            sp = self._SOL_CARDS_SPACING
            cols = (avail - sp) // (min_w + sp)
            cols = max(self._SOL_CARDS_MIN_COLS, min(self._SOL_CARDS_MAX_COLS, int(cols)))
            return cols
        except Exception:
            return 3
    def _reorganizar_solucoes_grid_responsivo(self, force: bool=False) -> None:
        if not getattr(self, '_sol_cards_widgets_ordem', None):
            return
        if not hasattr(self, 'grid_layout') or self.grid_layout is None:
            return
        cols = self._calcular_colunas_solucoes()
        if not force:
            if cols == getattr(self, '_sol_cards_cols_atual', 0):
                return
        parent = self.grid_layout.parentWidget()
        try:
            col = 0
            row += 1
            # WARNING: continue outside loop (unrecovered structure)
        except Exception:
            try:
                if parent is not None:
                    parent.setUpdatesEnabled(False)
                while self.grid_layout.count():
                    item = self.grid_layout.takeAt(0)
                    if item is not None and item.widget() is not None:
                        item.widget().setParent(parent)
                for i in range(self.grid_layout.columnCount()):
                    self.grid_layout.setColumnStretch(i, 0)
                    self.grid_layout.setColumnMinimumWidth(i, 0)
                for i in range(cols):
                    self.grid_layout.setColumnStretch(i, 1)
                row = col = 0
                for card in self._sol_cards_widgets_ordem:
                    try:
                        if card is not None:
                            try:
                                self.grid_layout.addWidget(card, row, col)
                            except RuntimeError:
                                continue
                            else:
                                col += 1
                            finally:
                                if parent is not None:
                                    parent.setUpdatesEnabled(True)
                                    parent.update()
                            if col >= cols:
                                pass
                    except RuntimeError:
                        continue
            finally:
                if parent is not None:
                    parent.setUpdatesEnabled(True)
                    parent.update()
        finally:
            if parent is not None:
                parent.setUpdatesEnabled(True)
                parent.update()
        try:
            self.grid_layout.setRowStretch(row + 1, 1)
        except Exception:
            pass
        self._sol_cards_cols_atual = cols
        if parent is not None:
            parent.setUpdatesEnabled(True)
            parent.update()
    def _agendar_reorganizacao_solucoes(self) -> None:
        try:
            from PyQt5.QtCore import QTimer
            timer = getattr(self, '_sol_resize_timer', None)
            if timer is None:
                timer = QTimer(self)
                timer.setSingleShot(True)
                timer.timeout.connect(self._reorganizar_solucoes_grid_responsivo)
                self._sol_resize_timer = timer
            timer.start(80)
            return
        except Exception:
            try:
                self._reorganizar_solucoes_grid_responsivo()
                return
            except Exception:
                pass
    def resizeEvent(self, event):
        try:
            super().resizeEvent(event)
        except Exception:
            pass
        try:
            self._agendar_reorganizacao_solucoes()
        except Exception:
            return
    def filtrar_modelos(self, texto):
        try:
            if not texto:
                self.carregar_solucoes()
                return
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("\n                SELECT id, modelo, descricao, observacoes, \n                       diagrama_blob, imagem_blob,\n                       diagrama_blob_2, imagem_blob_2,\n                       diagrama_blob_3, imagem_blob_3\n                FROM solucoes \n                WHERE marca=? \n                AND status='ativo' \n                AND (\n                    lower(modelo) LIKE ? OR \n                    lower(descricao) LIKE ? OR \n                    lower(observacoes) LIKE ?\n                )\n                ORDER BY modelo\n            ", (self.marca, f'%{texto.lower()}%', f'%{texto.lower()}%', f'%{texto.lower()}%'))
            solucoes = cursor.fetchall()
            self.limpar_grid()
            self.adicionar_cards(solucoes)
            conn.close()
            return
        except Exception as e:
            QMessageBox.critical(self, 'Erro', 'N├úo foi poss├¡vel filtrar os modelos.')
    def limpar_grid(self):
        try:
            self._sol_cards_widgets_ordem = []
            self._sol_cards_cols_atual = 0
        except Exception:
            pass
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for i in range(self.grid_layout.rowCount()):
            self.grid_layout.setRowStretch(i, 0)
        QApplication.processEvents()
    def adicionar_cards(self, solucoes):
        row = col = 0
        for solucao in solucoes:
            card = self.criar_card_solucao(*solucao)
            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1
    def setup_ui(self):
        self.setWindowTitle(self.translation_manager.get_text('solutions_title').format(self.marca))
        self.setMinimumSize(1200, 700)
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        left_container = QWidget()
        left_container.setMaximumWidth(300)
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(10, 10, 10, 10)
        self.filters_widget = SolutionFiltersWidget()
        self.filters_widget.filterChanged.connect(self.aplicar_filtro)
        left_layout.addWidget(self.filters_widget)
        self.criar_secao_avisos(left_layout)
        left_layout.addStretch()
        main_layout.addWidget(left_container)
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        header = QHBoxLayout()
        btn_voltar = QPushButton(self.translation_manager.get_text('back'))
        btn_voltar.setStyleSheet('\n            QPushButton {\n                background-color: #2196F3;\n                color: white;\n                border: none;\n                padding: 8px 15px;\n                border-radius: 4px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #1976D2;\n            }\n        ')
        btn_voltar.clicked.connect(self.voltar)
        header.addWidget(btn_voltar)
        nav_label = QLabel(self.translation_manager.get_text('solutions_breadcrumb').format(self.marca))
        nav_label.setStyleSheet('color: #2196F3; font-size: 14px;')
        header.addWidget(nav_label)
        header.addStretch()
        right_layout.addLayout(header)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.translation_manager.get_text('search_solutions_placeholder'))
        self.search_input.setStyleSheet('\n            QLineEdit {\n                padding: 10px 14px;\n                border: 1.5px solid #e0e0e0;\n                border-radius: 12px;\n                margin: 10px 0;\n                font-size: 14px;\n                background: #fafbfc;\n            }\n            QLineEdit:focus {\n                border-color: #2196F3;\n                background: #ffffff;\n                border-width: 2px;\n            }\n        ')
        self.search_input.textChanged.connect(self.schedule_search)
        right_layout.addWidget(self.search_input)
        self.results_count_label = QLabel('')
        self.results_count_label.setStyleSheet('font-size: 12px; color: #888; padding: 0 0 5px 5px;')
        right_layout.addWidget(self.results_count_label)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet('\n            QScrollArea { \n                border: none;\n                background: transparent;\n            }\n            QScrollBar:vertical {\n                border: none;\n                background: #f0f0f0;\n                width: 10px;\n                border-radius: 5px;\n            }\n            QScrollBar::handle:vertical {\n                background: #c0c0c0;\n                border-radius: 5px;\n            }\n            QScrollBar::handle:vertical:hover {\n                background: #a0a0a0;\n            }\n            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n                height: 0px;\n            }\n            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {\n                background: #f0f0f0;\n            }\n            /* Estilo para barra horizontal */\n            QScrollBar:horizontal {\n                border: none;\n                background: #f0f0f0;\n                height: 10px;\n                border-radius: 5px;\n            }\n            QScrollBar::handle:horizontal {\n                background: #c0c0c0;\n                border-radius: 5px;\n            }\n            QScrollBar::handle:horizontal:hover {\n                background: #a0a0a0;\n            }\n            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {\n                width: 0px;\n            }\n            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {\n                background: #f0f0f0;\n            }\n            /* Estilo para o canto entre as barras */\n            QScrollBar::corner {\n                background: #f0f0f0;\n            }\n        ')
        content = QWidget()
        self.grid_layout = QGridLayout(content)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setAlignment(Qt.AlignTop)
        self.grid_layout.setContentsMargins(20, 20, 20, 20)
        content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        scroll.setWidget(content)
        right_layout.addWidget(scroll)
        self._cards_scroll_area = scroll
        main_layout.addWidget(right_container)
        main_layout.setStretch(0, 1)
        main_layout.setStretch(1, 4)
    def criar_secao_avisos(self, layout):
        avisos_frame = QFrame()
        avisos_frame.setStyleSheet('\n            QFrame {\n                background-color: white;\n                border: 2px solid #e0e0e0;\n                border-radius: 10px;\n                padding: 10px;\n                margin: 10px 0;\n            }\n        ')
        avisos_layout = QVBoxLayout(avisos_frame)
        avisos_layout.setContentsMargins(10, 10, 10, 10)
        avisos_layout.setSpacing(10)
        titulo_avisos = QLabel(self.translation_manager.get_text('important_information'))
        titulo_avisos.setStyleSheet('\n            QLabel {\n                color: #2c3e50;\n                font-size: 14px;\n                font-weight: bold;\n                padding: 5px 0;\n                border-bottom: 2px solid #3498db;\n                margin-bottom: 10px;\n            }\n        ')
        avisos_layout.addWidget(titulo_avisos)
        self.avisos_content = QWidget()
        self.avisos_content_layout = QVBoxLayout(self.avisos_content)
        self.avisos_content_layout.setContentsMargins(0, 0, 0, 0)
        self.avisos_content_layout.setSpacing(8)
        avisos_layout.addWidget(self.avisos_content)
        layout.addWidget(avisos_frame)
        self.carregar_avisos()
    def carregar_avisos(self):
        try:
            mysql_conn = pymysql.connect(**self.mysql_config)
            mysql_cursor = mysql_conn.cursor()
            mysql_cursor.execute("\n                SELECT id, titulo, descricao, link, arquivo_blob, ativo\n                FROM conteudos_dinamicos \n                WHERE LOWER(titulo) LIKE '%aviso%' \n                AND ativo = 1\n                ORDER BY id DESC\n                LIMIT 3\n            ")
            avisos = mysql_cursor.fetchall()
            mysql_cursor.close()
            mysql_conn.close()
            if not avisos:
                self.avisos_content.parent().setVisible(False)
                return
            self.avisos_content.parent().setVisible(True)
            self.limpar_avisos()
            for aviso in avisos:
                self.criar_card_aviso(aviso)
            return
        except Exception as e:
            print(f'Erro ao carregar avisos: {e}')
            self.avisos_content.parent().setVisible(False)
    def limpar_avisos(self):
        while self.avisos_content_layout.count():
            item = self.avisos_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        QApplication.processEvents()
    def criar_card_aviso(self, aviso):
        card = QFrame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(8, 8, 8, 8)
        card_layout.setSpacing(8)
        card.setStyleSheet('\n            QFrame {\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, \n                    stop:0 #e8f5e8, stop:1 #f0f8f0);\n                border: 2px solid #27ae60;\n                border-radius: 8px;\n                padding: 5px;\n            }\n        ')
        if aviso['arquivo_blob'] and len(aviso['arquivo_blob']) > 100:
            try:
                imagem_label = QLabel()
                pixmap = QPixmap()
                if pixmap.loadFromData(aviso['arquivo_blob']):
                    screen = QApplication.primaryScreen().size()
                    is_small_screen = screen.width() <= 1366 or screen.height() <= 768
                    original_width = pixmap.width()
                    original_height = pixmap.height()
                    is_landscape = original_width > original_height
                    is_portrait = original_height > original_width
                    aspect_ratio = original_width / original_height
                    if is_small_screen:
                        if is_landscape:
                            max_width = 220
                            max_height = int(220 / aspect_ratio)
                            if max_height > 90:
                                max_height = 90
                                max_width = int(90 * aspect_ratio)
                        elif is_portrait:
                            max_width = 140
                            max_height = int(140 / aspect_ratio)
                            if max_height > 120:
                                max_height = 120
                                max_width = int(120 * aspect_ratio)
                        else:
                            max_width = max_height = 100
                    elif is_landscape:
                        max_width = 250
                        max_height = int(250 / aspect_ratio)
                        if max_height > 120:
                            max_height = 120
                            max_width = int(120 * aspect_ratio)
                    elif is_portrait:
                        max_width = 160
                        max_height = int(160 / aspect_ratio)
                        if max_height > 140:
                            max_height = 140
                            max_width = int(140 * aspect_ratio)
                    else:
                        max_width = max_height = 120
                    scaled_pixmap = pixmap.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    imagem_label.setPixmap(scaled_pixmap)
                    imagem_label.setAlignment(Qt.AlignCenter)
                    min_height = 70 if is_small_screen else 90
                    imagem_label.setMinimumHeight(min_height)
                    imagem_label.setStyleSheet('\n                        QLabel {\n                            border: 1px solid #bdc3c7;\n                            border-radius: 5px;\n                            padding: 3px;\n                            background-color: white;\n                            cursor: pointer;\n                        }\n                        QLabel:hover {\n                            border: 2px solid #3498db;\n                            background-color: #f8f9fa;\n                        }\n                    ')
                    tooltip_text = 'Clique para ampliar\n'
                    tooltip_text += f'Tamanho original: {original_width}x{original_height}\n'
                    tooltip_text += f'Orienta├º├úo: {'Horizontal' if is_landscape else 'Vertical' if is_portrait else 'Quadrada'}'
                    imagem_label.setToolTip(tooltip_text)
                    imagem_label.mousePressEvent = lambda event: self.ampliar_imagem_aviso(aviso['arquivo_blob'])
                    card_layout.addWidget(imagem_label)
            except Exception as e:
                print(f'Erro ao carregar imagem do aviso: {e}')
        if aviso['descricao']:
            screen = QApplication.primaryScreen().size()
            is_small_screen = screen.width() <= 1366 or screen.height() <= 768
            max_chars = 80 if is_small_screen else 100
            desc_text = aviso['descricao'][:max_chars] + '...' if len(aviso['descricao']) > max_chars else aviso['descricao']
            desc_label = QLabel(desc_text)
            font_size = '10px' if is_small_screen else '11px'
            desc_label.setStyleSheet(f'\n                QLabel {{\n                    color: #34495e;\n                    font-size: {font_size};\n                    padding: 5px;\n                    background-color: rgba(255, 255, 255, 0.7);\n                    border-radius: 4px;\n                    font-weight: bold;\n                    line-height: 1.3;\n                }}\n            ')
            desc_label.setWordWrap(True)
            card_layout.addWidget(desc_label)
        if aviso['link']:
            screen = QApplication.primaryScreen().size()
            is_small_screen = screen.width() <= 1366 or screen.height() <= 768
            btn_text = self.translation_manager.get_text('link_short') if is_small_screen else self.translation_manager.get_text('access_link')
            btn_link = QPushButton(btn_text)
            font_size = '11px' if is_small_screen else '12px'
            min_height = '30px' if is_small_screen else '35px'
            padding = '6px 10px' if is_small_screen else '8px 12px'
            btn_link.setStyleSheet(f'\n                QPushButton {{\n                    background-color: #3498db;\n                    color: white;\n                    border: none;\n                    border-radius: 6px;\n                    padding: {padding};\n                    font-size: {font_size};\n                    font-weight: bold;\n                    min-height: {min_height};\n                }}\n                QPushButton:hover {{\n                    background-color: #2980b9;\n                }}\n                QPushButton:pressed {{\n                    background-color: #21618c;\n                }}\n            ')
            btn_link.setCursor(Qt.PointingHandCursor)
            btn_link.clicked.connect((lambda: self.abrir_link_aviso(aviso['link'])))
            card_layout.addWidget(btn_link)
        self.avisos_content_layout.addWidget(card)
    def abrir_link_aviso(self, link):
        try:
            import webbrowser
            webbrowser.open(link)
            QMessageBox.information(self, 'Link Aberto', f'O link foi aberto no seu navegador:\n\n{link}')
            return
        except Exception as e:
            QMessageBox.warning(self, 'Erro', f'N├úo foi poss├¡vel abrir o link:\n{link}\n\nErro: {str(e)}')
    def ampliar_imagem_aviso(self, imagem_blob):
        try:
            dialog = ImagemDialog(imagem_blob, self)
            dialog.setWindowTitle('Visualizar Imagem')
            dialog.setMinimumSize(800, 600)
            dialog.exec_()
            return
        except Exception as e:
            self._mostrar_erro_seguro('Erro de Visualiza├º├úo', 'N├úo foi poss├¡vel ampliar a imagem.', str(e))
    def schedule_search(self, texto):
        from PyQt5.QtCore import QTimer
        if self.search_timer is not None:
            self.search_timer.stop()
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect((lambda: self.filtrar_modelos(texto)))
        self.search_timer.start(self.search_delay)
    def carregar_solucoes(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            marca_busca = self.marca.replace('\n', ' ').strip()
            while '  ' in marca_busca:
                marca_busca = marca_busca.replace('  ', ' ')
            cursor.execute("\n                SELECT id, modelo, descricao, observacoes, \n                       diagrama_blob, imagem_blob,\n                       diagrama_blob_2, imagem_blob_2,\n                       diagrama_blob_3, imagem_blob_3\n                FROM solucoes \n                WHERE status='ativo'\n                AND marca = ?\n                ORDER BY modelo\n            ", (marca_busca,))
            self.cached_solutions = cursor.fetchall()
            conn.close()
            self.atualizar_grid(self.cached_solutions)
            return
        except Exception as e:
            self._mostrar_erro_seguro('Erro de Carregamento', 'N├úo foi poss├¡vel carregar as solu├º├Áes.', str(e))
    def atualizar_grid(self, solucoes):
        try:
            self.limpar_grid()
            total = len(solucoes) if solucoes else 0
            if hasattr(self, 'results_count_label'):
                if total == 0:
                    self.results_count_label.setText('')
                elif total == 1:
                    self.results_count_label.setText('1 solu├º├úo encontrada')
                else:
                    self.results_count_label.setText(f'{total} solu├º├Áes encontradas')
            if not solucoes:
                label = QLabel(self.translation_manager.get_text('no_solutions_found').format(self.marca))
                label.setStyleSheet('font-size: 14px; color: #666; padding: 20px;')
                label.setAlignment(Qt.AlignCenter)
                self.grid_layout.addWidget(label, 0, 0, 1, 3)
                return
            num_columns = self._calcular_colunas_solucoes()
            self.grid_layout.setSpacing(self._SOL_CARDS_SPACING)
            for i in range(self.grid_layout.columnCount()):
                self.grid_layout.setColumnStretch(i, 0)
                self.grid_layout.setColumnMinimumWidth(i, 0)
            for i in range(num_columns):
                self.grid_layout.setColumnStretch(i, 1)
            row = col = 0
            for idx, solucao in enumerate(solucoes):
                card = self.criar_card_solucao(*solucao)
                self.grid_layout.addWidget(card, row, col)
                self._sol_cards_widgets_ordem.append(card)
                col += 1
                if col >= num_columns:
                    col = 0
                    row += 1
                if (idx + 1) % 50 == 0:
                    QApplication.processEvents()
            self.grid_layout.setRowStretch(row + 1, 1)
            self._sol_cards_cols_atual = num_columns
            return
        except Exception as e:
            self._mostrar_erro_seguro('Erro de Visualiza├º├úo', 'N├úo foi poss├¡vel atualizar a lista de solu├º├Áes.', str(e))
    def criar_card_solucao(self, id, modelo, descricao, observacoes=None, diagrama_blob=None, imagem_blob=None, diagrama_blob_2=None, imagem_blob_2=None, diagrama_blob_3=None, imagem_blob_3=None):
        card = QWidget()
        card.setStyleSheet('\n            QWidget {\n                background-color: white;\n                border: 1px solid #e0e0e0;\n                border-radius: 10px;\n                padding: 0px;\n                margin: 8px;\n            }\n            QWidget:hover {\n                background-color: rgba(33, 150, 243, 0.03);\n                border: 1px solid #2196F3;\n                border-bottom: 2.5px solid rgba(13, 71, 161, 0.22);\n            }\n        ')
        card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        card.setFixedHeight(280)
        card.setMinimumWidth(240)
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)
        titulo = QLabel(modelo)
        titulo.setStyleSheet('\n            font-weight: bold; \n            font-size: 16px; \n            color: #2c3e50;\n            padding: 5px 0;\n        ')
        titulo.setWordWrap(True)
        titulo.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        titulo.setFixedHeight(50)
        layout.addWidget(titulo)
        desc_text = descricao[:120] + '...' if len(descricao) > 120 else descricao
        desc = QLabel(desc_text)
        desc.setWordWrap(True)
        desc.setStyleSheet('\n            color: #34495e; \n            font-size: 14px; \n            line-height: 1.4;\n            padding: 5px 0;\n        ')
        desc.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        desc.setFixedHeight(120)
        layout.addWidget(desc)
        layout.addStretch()
        btn = QPushButton(self.translation_manager.get_text('view_details'))
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet('\n            QPushButton {\n                background-color: #2196F3;\n                color: white;\n                border: none;\n                padding: 12px;\n                border-radius: 8px;\n                font-size: 14px;\n                font-weight: bold;\n                min-height: 40px;\n                max-height: 40px;\n            }\n            QPushButton:hover {\n                background-color: #1976D2;\n                border-bottom: 2px solid #0D47A1;\n            }\n            QPushButton:pressed {\n                background-color: #1565C0;\n                border-bottom: none;\n            }\n            QPushButton:focus {\n                outline: none;\n                border: 2px solid #4FC3F7;\n            }\n        ')
        btn.clicked.connect((lambda: self.ver_detalhes(id)))
        layout.addWidget(btn)
        return card
    def ver_detalhes(self, id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('\n                SELECT modelo, descricao, observacoes, \n                       CASE WHEN diagrama_blob IS NULL OR length(diagrama_blob) < 100 THEN 0 ELSE 1 END as tem_diagrama,\n                       CASE WHEN imagem_blob IS NULL OR length(imagem_blob) < 100 THEN 0 ELSE 1 END as tem_imagem,\n                       CASE WHEN diagrama_blob_2 IS NULL OR length(diagrama_blob_2) < 100 THEN 0 ELSE 1 END as tem_diagrama_2,\n                       CASE WHEN imagem_blob_2 IS NULL OR length(imagem_blob_2) < 100 THEN 0 ELSE 1 END as tem_imagem_2,\n                       CASE WHEN diagrama_blob_3 IS NULL OR length(diagrama_blob_3) < 100 THEN 0 ELSE 1 END as tem_diagrama_3,\n                       CASE WHEN imagem_blob_3 IS NULL OR length(imagem_blob_3) < 100 THEN 0 ELSE 1 END as tem_imagem_3,\n                       diagrama_blob, imagem_blob,\n                       diagrama_blob_2, imagem_blob_2,\n                       diagrama_blob_3, imagem_blob_3\n                FROM solucoes \n                WHERE id=?\n            ', (id,))
            resultado = cursor.fetchone()
            if not resultado:
                QMessageBox.critical(self, 'Erro', 'Solu├º├úo n├úo encontrada')
                conn.close()
                return
            (modelo, descricao, observacoes, tem_diagrama, tem_imagem, tem_diagrama_2,
            tem_imagem_2, tem_diagrama_3, tem_imagem_3, diagrama_blob, imagem_blob,
            diagrama_blob_2, imagem_blob_2, diagrama_blob_3, imagem_blob_3) = resultado
            precisa_baixar = not tem_diagrama or not tem_imagem or not tem_diagrama_2 or not tem_imagem_2 or not tem_diagrama_3 or not tem_imagem_3
            if precisa_baixar:
                novos_blobs = self.baixar_blobs_sob_demanda(id)
                if novos_blobs:
                    (diagrama_blob, imagem_blob, diagrama_blob_2, imagem_blob_2,
                    diagrama_blob_3, imagem_blob_3) = novos_blobs
            todos_blobs = {'imagem_blob': decrypt_blob_safe(imagem_blob), 'diagrama_blob': decrypt_blob_safe(diagrama_blob), 'imagem_blob_2': decrypt_blob_safe(imagem_blob_2), 'diagrama_blob_2': decrypt_blob_safe(diagrama_blob_2), 'imagem_blob_3': decrypt_blob_safe(imagem_blob_3), 'diagrama_blob_3': decrypt_blob_safe(diagrama_blob_3)}
            self.mostrar_dialog_detalhes(modelo, descricao, observacoes, todos_blobs)
            conn.close()
            return
        except Exception as e:
            self._mostrar_erro_seguro('Erro de Detalhes', 'N├úo foi poss├¡vel carregar os detalhes da solu├º├úo.', str(e))
    def baixar_blobs_sob_demanda(self, solucao_id):
        try:
            progress = QProgressDialog('Baixando detalhes da solu├º├úo...', 'Cancelar', 0, 100, self)
            progress.setWindowTitle('Carregando')
            progress.setWindowModality(Qt.WindowModal)
            progress.setValue(10)
            QApplication.processEvents()
        except Exception as e:
            self._mostrar_erro_seguro('Erro de Download', 'N├úo foi poss├¡vel baixar detalhes adicionais da solu├º├úo.', str(e))
        try:
            mysql_conn = pymysql.connect(**self.mysql_config)
            mysql_cursor = mysql_conn.cursor()
            progress.setValue(30)
            QApplication.processEvents()
            mysql_cursor.execute('\n                    SELECT diagrama_blob, imagem_blob, diagrama_blob_2, imagem_blob_2,\n                           diagrama_blob_3, imagem_blob_3, hash_verificacao\n                    FROM solucoes\n                    WHERE id = %s\n                ', (solucao_id,))
            blob_data = mysql_cursor.fetchone()
            progress.setValue(60)
            QApplication.processEvents()
            if not blob_data:
                progress.close()
                return
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('\n                    UPDATE solucoes\n                    SET diagrama_blob = ?, imagem_blob = ?, \n                        diagrama_blob_2 = ?, imagem_blob_2 = ?,\n                        diagrama_blob_3 = ?, imagem_blob_3 = ?,\n                        hash_verificacao = ?, data_sincronizacao = CURRENT_TIMESTAMP\n                    WHERE id = ?\n                ', (encrypt_blob(blob_data['diagrama_blob']), encrypt_blob(blob_data['imagem_blob']), encrypt_blob(blob_data['diagrama_blob_2']), encrypt_blob(blob_data['imagem_blob_2']), encrypt_blob(blob_data['diagrama_blob_3']), encrypt_blob(blob_data['imagem_blob_3']), blob_data['hash_verificacao'], solucao_id))
            progress.setValue(90)
            QApplication.processEvents()
            conn.commit()
            conn.close()
            mysql_cursor.close()
            mysql_conn.close()
            progress.setValue(100)
            progress.close()
            return blob_data['diagrama_blob'], blob_data['imagem_blob'], blob_data['diagrama_blob_2'], blob_data['imagem_blob_2'], blob_data['diagrama_blob_3'], blob_data['imagem_blob_3']
        except pymysql.MySQLError as e:
            progress.close()
            QMessageBox.warning(self, 'Erro de Conex├úo', 'N├úo foi poss├¡vel baixar os detalhes completos da solu├º├úo. Verifique sua conex├úo com a internet e tente novamente.')
    def mostrar_dialog_detalhes(self, modelo, descricao, observacoes, todos_blobs):
        dialog = QDialog(self, Qt.Window)
        dialog.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        if not self.pode_gravar_tela():
            protect_window_from_capture_extended(dialog, True)
        dialog.setWindowTitle(modelo)
        dialog.setMinimumSize(800, 600)
        QShortcut(QKeySequence(Qt.Key_Escape), dialog, dialog.close)
        screen = QApplication.primaryScreen().size()
        dialog.resize(int(screen.width() * 0.8), int(screen.height() * 0.8))
        layout = QVBoxLayout(dialog)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        titulo = QLabel(modelo)
        titulo.setStyleSheet('font-size: 28px; font-weight: bold; color: #2c3e50; margin: 10px 0;')
        content_layout.addWidget(titulo)
        if descricao:
            desc_group = QGroupBox(self.translation_manager.get_text('description'))
            desc_group.setStyleSheet('\n                QGroupBox {\n                    font-size: 18px;\n                    font-weight: bold;\n                    padding: 15px;\n                }\n                QGroupBox::title {\n                    color: #2c3e50;\n                }\n            ')
            desc_layout = QVBoxLayout()
            desc_label = QLabel(str(descricao))
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet('font-size: 16px; color: #34495e; margin: 5px; font-weight: bold;')
            desc_layout.addWidget(desc_label)
            desc_group.setLayout(desc_layout)
            content_layout.addWidget(desc_group)
        if observacoes:
            obs_group = QGroupBox(self.translation_manager.get_text('observations'))
            obs_group.setStyleSheet('\n                QGroupBox {\n                    font-size: 18px;\n                    font-weight: bold;\n                    padding: 15px;\n                }\n                QGroupBox::title {\n                    color: #2c3e50;\n                }\n            ')
            obs_layout = QVBoxLayout()
            obs_label = QLabel(str(observacoes))
            obs_label.setWordWrap(True)
            obs_label.setStyleSheet('font-size: 16px; color: #34495e; margin: 5px; font-weight: bold;')
            obs_layout.addWidget(obs_label)
            obs_group.setLayout(obs_layout)
            content_layout.addWidget(obs_group)
        arquivos_disponiveis = []
        campos_blob = [('imagem_blob', 'Imagem Principal', 'imagem'), ('diagrama_blob', 'Diagrama Principal', 'diagrama'), ('imagem_blob_2', 'Imagem 2', 'imagem'), ('diagrama_blob_2', 'Diagrama 2', 'diagrama'), ('imagem_blob_3', 'Imagem 3', 'imagem'), ('diagrama_blob_3', 'Diagrama 3', 'diagrama')]
        for campo, nome, tipo in campos_blob:
            if not todos_blobs.get(campo):
                continue
            if len(todos_blobs[campo]) > 100:
                arquivos_disponiveis.append((campo, nome, tipo, todos_blobs[campo]))
        _lista_nav_imagens = [(nome, blob_data) for campo, nome, tipo, blob_data in arquivos_disponiveis if tipo == 'imagem']
        if arquivos_disponiveis:
            images_group = QGroupBox(f'{self.translation_manager.get_text('images')} ({len(arquivos_disponiveis)} arquivo(s))')
            images_group.setStyleSheet('\n                QGroupBox {\n                    font-size: 18px;\n                    font-weight: bold;\n                    padding: 15px;\n                }\n                QGroupBox::title {\n                    color: #2c3e50;\n                }\n            ')
            images_layout = QGridLayout()
            images_layout.setSpacing(15)
            row = col = 0
            max_cols = 3
            for campo, nome, tipo, blob_data in arquivos_disponiveis:
                container = QFrame()
                container.setStyleSheet('\n                    QFrame {\n                        border: 2px solid #e0e0e0;\n                        border-radius: 8px;\n                        background-color: #f9f9f9;\n                        padding: 10px;\n                    }\n                    QFrame:hover {\n                        border-color: #2196F3;\n                    }\n                ')
                container_layout = QVBoxLayout(container)
                titulo_arquivo = QLabel(nome)
                titulo_arquivo.setStyleSheet('\n                    font-weight: bold;\n                    font-size: 14px;\n                    color: #2c3e50;\n                    text-align: center;\n                    padding: 5px;\n                ')
                titulo_arquivo.setAlignment(Qt.AlignCenter)
                container_layout.addWidget(titulo_arquivo)
                preview_scene = QGraphicsScene()
                preview_view = QGraphicsView(preview_scene)
                preview_view.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing | QPainter.HighQualityAntialiasing)
                preview_view.setFixedSize(250, 180)
                preview_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                preview_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                try:
                    if tipo == 'diagrama':
                        pass
                    try:
                        doc = fitz.open(stream=blob_data, filetype='pdf')
                        page = doc[0]
                        zoom = 1.5
                        mat = fitz.Matrix(zoom, zoom)
                        pix = page.get_pixmap(matrix=mat, alpha=False)
                        img_data = pix.tobytes()
                        doc.close()
                        pixmap = QPixmap()
                        pixmap.loadFromData(img_data)
                    except:
                        pixmap = QPixmap()
                        pixmap.loadFromData(blob_data)
                    else:
                        pixmap = QPixmap()
                        pixmap.loadFromData(blob_data)
                        if not pixmap.isNull():
                            scaled = pixmap.scaled(240, 170, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            pixmap_item = QGraphicsPixmapItem(scaled)
                            pixmap_item.setTransformationMode(Qt.SmoothTransformation)
                            preview_scene.addItem(pixmap_item)
                            preview_view.setScene(preview_scene)
                            preview_view.fitInView(preview_scene.sceneRect(), Qt.KeepAspectRatio)
                except Exception as e:
                    placeholder = QLabel('Erro no preview')
                    placeholder.setAlignment(Qt.AlignCenter)
                    placeholder.setStyleSheet('color: #666; font-style: italic;')
                    container_layout.addWidget(placeholder)
                    preview_view = None
                if preview_view:
                    container_layout.addWidget(preview_view)
                if tipo == 'diagrama':
                    botoes_layout = QHBoxLayout()
                    btn_abrir = QPushButton('­ƒôä Abrir Diagrama')
                    btn_abrir.setStyleSheet('\n                        QPushButton {\n                            background-color: #2196F3;\n                            color: white;\n                            border: none;\n                            padding: 8px 12px;\n                            border-radius: 4px;\n                            font-size: 12px;\n                            font-weight: bold;\n                        }\n                        QPushButton:hover {\n                            background-color: #1976D2;\n                        }\n                    ')
                    btn_abrir.clicked.connect((lambda checked, data=blob_data: self.abrir_diagrama(data)))
                    botoes_layout.addWidget(btn_abrir)
                    container_layout.addLayout(botoes_layout)
                images_layout.addWidget(container, row, col)
                col += 1
                if not col >= max_cols:
                    continue
                col = 0
                row += 1
                continue
            if _lista_nav_imagens:
                n_imgs = len(_lista_nav_imagens)
                btn_ver_imagens = QPushButton(f'­ƒôÀ  Ver {'Imagem' if n_imgs == 1 else f'Imagens ({n_imgs})'}')
                btn_ver_imagens.setStyleSheet('\n                    QPushButton {\n                        background-color: #4CAF50;\n                        color: white;\n                        border: none;\n                        padding: 12px 24px;\n                        border-radius: 6px;\n                        font-size: 15px;\n                        font-weight: bold;\n                    }\n                    QPushButton:hover {\n                        background-color: #43A047;\n                    }\n                ')
                btn_ver_imagens.clicked.connect((lambda checked, lst=_lista_nav_imagens: self.ampliar_imagem(lst[0][1], lista_imagens=lst, indice_atual=0)))
                images_layout.addWidget(btn_ver_imagens, row + 1, 0, 1, max_cols)
            images_group.setLayout(images_layout)
            content_layout.addWidget(images_group)
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        btn_fechar = QPushButton(self.translation_manager.get_text('close'))
        btn_fechar.setStyleSheet('\n            QPushButton {\n                background-color: #2196F3;\n                color: white;\n                border: none;\n                padding: 8px 15px;\n                border-radius: 4px;\n                font-size: 14px;\n                font-weight: bold;\n            }\n            QPushButton:hover {\n                background-color: #1976D2;\n            }\n        ')
        btn_fechar.clicked.connect(dialog.close)
        layout.addWidget(btn_fechar)
        screen = QApplication.primaryScreen().availableGeometry()
        dialog_size = dialog.frameGeometry()
        x = (screen.width() - dialog_size.width()) // 2
        y = (screen.height() - dialog_size.height()) // 2
        dialog.move(x, y)
        dialog.exec_()
    _EDGE_PATHS = [os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Microsoft', 'Edge', 'Application', 'msedge.exe'), os.path.join(os.environ.get('PROGRAMFILES', ''), 'Microsoft', 'Edge', 'Application', 'msedge.exe'), os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'Application', 'msedge.exe')]
    def abrir_diagrama(self, diagrama_blob):
        try:
            pixmap = QPixmap()
            if pixmap.loadFromData(diagrama_blob):
                dialog = DiagramaDialog(diagrama_blob, self)
                dialog.setMinimumSize(800, 600)
                dialog.exec_()
                return
            if not diagrama_blob[:5].startswith(b'%PDF'):
                raise Exception('Formato de arquivo n├úo suportado')
            temp_path = self._salvar_pdf_temp(diagrama_blob)
            self._abrir_pdf_edge(temp_path)
            return
        except Exception as e:
            self._mostrar_erro_seguro('Erro de Visualiza├º├úo', 'N├úo foi poss├¡vel abrir o arquivo.', str(e))
    def _salvar_pdf_temp(self, blob):
        union_temp = os.path.join(tempfile.gettempdir(), 'union_diagramas')
        os.makedirs(union_temp, exist_ok=True)
        fd, path = tempfile.mkstemp(suffix='.pdf', prefix='diagrama_', dir=union_temp)
        with os.fdopen(fd, 'wb') as f:
            f.write(blob)
        return path
    def _abrir_pdf_edge(self, pdf_path):
        for edge in self._EDGE_PATHS:
            if os.path.isfile(edge):
                file_url = 'file:///' + pdf_path.replace('\\', '/')
                subprocess.Popen([edge, '--app=' + file_url])
                return
        os.startfile(pdf_path)
    def ampliar_imagem(self, imagem_blob, lista_imagens=None, indice_atual=0):
        try:
            dialog = ImagemDialog(imagem_blob, self, lista_imagens=lista_imagens, indice_atual=indice_atual)
            dialog.setWindowTitle(self.translation_manager.get_text('enlarged_preview'))
            dialog.setMinimumSize(800, 600)
            dialog.exec_()
            return
        except Exception as e:
            self._mostrar_erro_seguro('Erro de Visualiza├º├úo', 'N├úo foi poss├¡vel ampliar a imagem.', str(e))
    def refresh_interface(self):
        self.setWindowTitle(self.translation_manager.get_text('solutions_title').format(self.marca))
        for label in self.findChildren(QLabel):
            if '>' in label.text():
                label.setText(self.translation_manager.get_text('solutions_breadcrumb').format(self.marca))
        self.search_input.setPlaceholderText(self.translation_manager.get_text('search_solutions_placeholder'))
        for btn in self.findChildren(QPushButton):
            if 'voltar' not in btn.text().lower():
                if 'back' in btn.text().lower() or 'volver' in btn.text().lower():
                    btn.setText(self.translation_manager.get_text('back'))
                    continue
            if 'abrir diagrama' in btn.text().lower() or 'open diagram' in btn.text().lower():
                btn.setText(self.translation_manager.get_text('open_diagram'))
                continue
            if 'ver diagrama' in btn.text().lower():
                btn.setText(self.translation_manager.get_text('view_diagram'))
                continue
            if 'ver imagem' in btn.text().lower():
                btn.setText(self.translation_manager.get_text('view_image'))
                continue
            if 'ampliar' not in btn.text().lower():
                if 'enlarge' in btn.text().lower() or 'aumentar' in btn.text().lower():
                    btn.setText(self.translation_manager.get_text('enlarge'))
                    continue
            if 'ver detalhes' not in btn.text().lower():
                continue
            btn.setText(self.translation_manager.get_text('view_details'))
            continue
        for group_box in self.findChildren(QGroupBox):
            title_lower = group_box.title().lower()
            if 'descri├º├úo' not in title_lower:
                if 'description' in title_lower or 'descripci├│n' in title_lower:
                    group_box.setTitle(self.translation_manager.get_text('description'))
                elif 'observa├º├Áes' not in title_lower:
                    if 'observations' in title_lower or 'observaciones' in title_lower:
                        group_box.setTitle(self.translation_manager.get_text('observations'))
                    elif 'imagens' in title_lower or 'images' in title_lower or 'im├ígenes' in title_lower:
                        group_box.setTitle(self.translation_manager.get_text('images'))
    def _sanitizar_entrada_busca(self, texto):
        if not texto:
            return ''
        import re
        texto_limpo = re.sub('[<>"\\\';\\\\%_]', '', str(texto).strip())
        if len(texto_limpo) > 100:
            texto_limpo = texto_limpo[:100]
        return texto_limpo
    def _mostrar_erro_seguro(self, titulo, mensagem_usuario, erro_tecnico=''):
        try:
            if erro_tecnico:
                print(f'[LOG T├ëCNICO] {titulo}: {erro_tecnico}')
            QMessageBox.warning(self, titulo, mensagem_usuario)
            return
        except Exception:
            QMessageBox.warning(self, 'Aviso', 'Ocorreu um problema inesperado.')
    def aplicar_filtro(self, filter_condition):
        try:
            if not filter_condition:
                self.atualizar_grid(self.cached_solutions)
                return
        except Exception as e:
            self._mostrar_erro_seguro('Erro de Filtro', 'N├úo foi poss├¡vel aplicar o filtro selecionado.', str(e))
        try:
            keywords = [self._sanitizar_entrada_busca(k.strip()) for k in filter_condition.split(',')]
        except Exception as e:
            self._mostrar_erro_seguro('Erro de Filtro', 'N├úo foi poss├¡vel aplicar o filtro selecionado.', str(e))
        try:
            keywords = [k for k in keywords if k]
            if not keywords:
                self.atualizar_grid(self.cached_solutions)
                return
            solucoes_filtradas = []
            texto_busca = self._sanitizar_entrada_busca(self.search_input.text())
            for solucao in self.cached_solutions:
                descricao = str(solucao[2]).lower() if solucao[2] else ''
                observacoes = str(solucao[3]).lower() if solucao[3] else ''
                matches_filter = False
                for keyword in keywords:
                    if not keyword:
                        continue
                    if keyword.lower() not in descricao:
                        if not keyword.lower() in observacoes:
                            continue
                    matches_filter = True
                    break
                if not matches_filter:
                    continue
                if texto_busca:
                    modelo = str(solucao[1]).lower() if solucao[1] else ''
                    if texto_busca.lower() in modelo or texto_busca.lower() in descricao or texto_busca.lower() in observacoes:
                        solucoes_filtradas.append(solucao)
                        continue
                solucoes_filtradas.append(solucao)
                continue
            self.atualizar_grid(solucoes_filtradas)
            return
        except Exception as e:
            self._mostrar_erro_seguro('Erro de Filtro', 'N├úo foi poss├¡vel aplicar o filtro selecionado.', str(e))
    def filtrar_modelos(self, texto):
        try:
            texto_sanitizado = self._sanitizar_entrada_busca(texto)
            if not texto_sanitizado:
                if hasattr(self, 'filters_widget') and self.filters_widget.current_filter:
                    self.aplicar_filtro(self.filters_widget.current_filter)
                    return
                self.atualizar_grid(self.cached_solutions)
                return
            if hasattr(self, 'filters_widget') and self.filters_widget.current_filter:
                self.aplicar_filtro(self.filters_widget.current_filter)
                return
        except Exception as e:
            self._mostrar_erro_seguro('Erro de Busca', 'N├úo foi poss├¡vel realizar a busca.', str(e))
        try:
            solucoes_filtradas = [s for s in self.cached_solutions if texto_sanitizado.lower() in str(s[1]).lower() if s[2] if texto_sanitizado.lower() in str(s[2]).lower() if s[3] if texto_sanitizado.lower() in str(s[3]).lower()]
            self.atualizar_grid(solucoes_filtradas)
            return
        except Exception as e:
            self._mostrar_erro_seguro('Erro de Busca', 'N├úo foi poss├¡vel realizar a busca.', str(e))
