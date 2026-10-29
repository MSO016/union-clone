"""Configurações: dados da empresa e perfil do usuário — SPEC RF-CFG-*."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ....core.db.repos.config_repo import ConfigRepository
from ....core.models.models import ConfigEmpresa, PerfilUsuario
from ....core.services.backup_service import (
    BackupError,
    backup_nome_sugerido,
    backup_para,
    restaurar_de,
)
from ...i18n import t


class ConfigView(QWidget):
    """Módulo de configurações (aba Empresa + aba Perfil + aba Backup)."""

    def __init__(
        self,
        repo: ConfigRepository,
        user_id: int = 0,
        conexao=None,
        caminho_banco=None,
        pai=None,
    ) -> None:
        super().__init__(pai)
        self._repo = repo
        self._user_id = user_id
        self._conexao = conexao
        self._caminho_banco = caminho_banco

        layout = QVBoxLayout(self)
        titulo = QLabel(t("menu_config"))
        titulo.setObjectName("tituloModulo")
        layout.addWidget(titulo)

        abas = QTabWidget()
        layout.addWidget(abas)
        abas.addTab(self._aba_empresa(), "Empresa")
        abas.addTab(self._aba_perfil(), "Perfil")
        if self._conexao is not None and self._caminho_banco is not None:
            abas.addTab(self._aba_backup(), "Backup")

    # --- aba empresa -------------------------------------------------------
    def _aba_empresa(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)

        self._razao = QLineEdit()
        self._cnpj = QLineEdit()
        self._fantasia = QLineEdit()
        self._endereco = QLineEdit()
        self._cidade = QLineEdit()
        self._estado = QLineEdit()
        self._telefone = QLineEdit()
        self._email = QLineEdit()
        self._website = QLineEdit()
        self._rodape = QLineEdit()
        self._garantia = QTextEdit()
        self._garantia.setMaximumHeight(90)

        form.addRow("Razão social", self._razao)
        form.addRow("CNPJ", self._cnpj)
        form.addRow("Nome fantasia", self._fantasia)
        form.addRow("Endereço", self._endereco)
        form.addRow("Cidade", self._cidade)
        form.addRow("Estado", self._estado)
        form.addRow(t("cliente_telefone"), self._telefone)
        form.addRow(t("cliente_email"), self._email)
        form.addRow("Website", self._website)
        form.addRow("Mensagem do rodapé", self._rodape)
        form.addRow("Termos de garantia", self._garantia)

        btn = QPushButton(t("acao_salvar"))
        btn.clicked.connect(self._salvar_empresa)
        form.addRow(btn)

        cfg = self._repo.obter_empresa(self._user_id)
        if cfg is not None:
            self._razao.setText(cfg.razao_social)
            self._cnpj.setText(cfg.cnpj)
            self._fantasia.setText(cfg.nome_fantasia)
            self._endereco.setText(cfg.endereco)
            self._cidade.setText(cfg.cidade)
            self._estado.setText(cfg.estado)
            self._telefone.setText(cfg.telefone)
            self._email.setText(cfg.email)
            self._website.setText(cfg.website)
            self._rodape.setText(cfg.mensagem_rodape)
            self._garantia.setPlainText(cfg.termos_garantia)
        return w

    def _salvar_empresa(self) -> None:
        cfg = ConfigEmpresa(
            user_id=self._user_id,
            razao_social=self._razao.text().strip(),
            cnpj=self._cnpj.text().strip(),
            nome_fantasia=self._fantasia.text().strip(),
            endereco=self._endereco.text().strip(),
            cidade=self._cidade.text().strip(),
            estado=self._estado.text().strip(),
            telefone=self._telefone.text().strip(),
            email=self._email.text().strip(),
            website=self._website.text().strip(),
            mensagem_rodape=self._rodape.text().strip(),
            termos_garantia=self._garantia.toPlainText().strip(),
        )
        self._repo.salvar_empresa(cfg)
        QMessageBox.information(self, t("ok"), "Dados da empresa salvos.")

    # --- aba perfil --------------------------------------------------------
    def _aba_perfil(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)

        self._pnome = QLineEdit()
        self._ptelefone = QLineEdit()
        self._pemail = QLineEdit()
        self._pbio = QPlainTextEdit()
        self._pbio.setMaximumHeight(90)
        self._pnotif_email = QCheckBox(t("nao"))
        self._pnotif_push = QCheckBox(t("nao"))

        form.addRow("Nome", self._pnome)
        form.addRow(t("cliente_telefone"), self._ptelefone)
        form.addRow(t("cliente_email"), self._pemail)
        form.addRow("Bio", self._pbio)
        form.addRow("Notificações por e-mail", self._pnotif_email)
        form.addRow("Notificações push", self._pnotif_push)

        btn = QPushButton(t("acao_salvar"))
        btn.clicked.connect(self._salvar_perfil)
        form.addRow(btn)

        p = self._repo.obter_perfil(self._user_id)
        if p is not None:
            self._pnome.setText(p.nome)
            self._ptelefone.setText(p.telefone)
            self._pemail.setText(p.email)
            self._pbio.setPlainText(p.bio)
            self._pnotif_email.setChecked(p.notif_email)
            self._pnotif_push.setChecked(p.notif_push)
        return w

    def _salvar_perfil(self) -> None:
        p = PerfilUsuario(
            user_id=self._user_id,
            nome=self._pnome.text().strip(),
            telefone=self._ptelefone.text().strip(),
            email=self._pemail.text().strip(),
            bio=self._pbio.toPlainText().strip(),
            notif_email=self._pnotif_email.isChecked(),
            notif_push=self._pnotif_push.isChecked(),
        )
        self._repo.salvar_perfil(p)
        QMessageBox.information(self, t("ok"), "Perfil salvo.")

    # --- aba backup --------------------------------------------------------
    def _aba_backup(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        info = QLabel(
            "O backup salva uma cópia consistente do banco de dados "
            "(clientes, ordens, conhecimento e configurações) em um arquivo .db."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        btn_backup = QPushButton("Fazer backup agora…")
        btn_backup.clicked.connect(self._fazer_backup)
        layout.addWidget(btn_backup)

        btn_restaurar = QPushButton("Restaurar backup…")
        btn_restaurar.clicked.connect(self._restaurar_backup)
        layout.addWidget(btn_restaurar)

        layout.addStretch(1)
        return w

    def _fazer_backup(self) -> None:
        sugerido = backup_nome_sugerido(self._caminho_banco.parent)
        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar backup",
            str(sugerido),
            "Backup SQLite (*.db)",
        )
        if not caminho:
            return
        try:
            backup_para(self._conexao, Path(caminho))
        except BackupError as e:
            QMessageBox.warning(self, t("erro"), str(e))
            return
        QMessageBox.information(self, t("ok"), f"Backup salvo em:\n{caminho}")

    def _restaurar_backup(self) -> None:
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Selecionar backup", "", "Backup SQLite (*.db)"
        )
        if not caminho:
            return
        resp = QMessageBox.question(
            self,
            t("aviso"),
            "Restaurar substituirá TODOS os dados atuais pelos do backup.\n"
            "O aplicativo será fechado em seguida. Continuar?",
        )
        if resp != QMessageBox.StandardButton.Yes:
            return
        try:
            restaurar_de(Path(caminho), self._conexao, self._caminho_banco)
        except BackupError as e:
            QMessageBox.warning(self, t("erro"), str(e))
            return
        QMessageBox.information(
            self, t("ok"), "Backup restaurado. O aplicativo será encerrado — abra novamente."
        )
        # A conexão foi fechada pelo serviço; encerra o app para reabertura limpa.
        from PyQt6.QtWidgets import QApplication

        QApplication.quit()
