"""Repositório de configuração (empresa) e perfil do usuário (local)."""
from __future__ import annotations

import sqlite3
from typing import Optional

from ...models.models import ConfigEmpresa, PerfilUsuario


def _row_para_config(row: sqlite3.Row) -> ConfigEmpresa:
    return ConfigEmpresa(
        user_id=row["user_id"],
        logo=row["logo"],
        razao_social=row["razao_social"] or "",
        cnpj=row["cnpj"] or "",
        nome_fantasia=row["nome_fantasia"] or "",
        endereco=row["endereco"] or "",
        cidade=row["cidade"] or "",
        estado=row["estado"] or "",
        telefone=row["telefone"] or "",
        email=row["email"] or "",
        website=row["website"] or "",
        mensagem_rodape=row["mensagem_rodape"] or "",
        termos_garantia=row["termos_garantia"] or "",
    )


def _row_para_perfil(row: sqlite3.Row) -> PerfilUsuario:
    return PerfilUsuario(
        user_id=row["user_id"],
        nome=row["nome"] or "",
        telefone=row["telefone"] or "",
        email=row["email"] or "",
        foto=row["foto"],
        bio=row["bio"] or "",
        nascimento=row["nascimento"] or "",
        notif_email=bool(row["notif_email"]),
        notif_push=bool(row["notif_push"]),
    )


class ConfigRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    # --- empresa -----------------------------------------------------------
    def obter_empresa(self, user_id: int = 0) -> Optional[ConfigEmpresa]:
        row = self._conn.execute(
            "SELECT * FROM config_empresa WHERE user_id=?", (user_id,)
        ).fetchone()
        return _row_para_config(row) if row else None

    def salvar_empresa(self, cfg: ConfigEmpresa) -> None:
        # UPDATE com fallback para INSERT (SPEC RF-CFG-1).
        cur = self._conn.execute(
            """
            UPDATE config_empresa SET
                logo=?, razao_social=?, cnpj=?, nome_fantasia=?, endereco=?, cidade=?,
                estado=?, telefone=?, email=?, website=?, mensagem_rodape=?, termos_garantia=?
            WHERE user_id=?
            """,
            (
                cfg.logo,
                cfg.razao_social,
                cfg.cnpj,
                cfg.nome_fantasia,
                cfg.endereco,
                cfg.cidade,
                cfg.estado,
                cfg.telefone,
                cfg.email,
                cfg.website,
                cfg.mensagem_rodape,
                cfg.termos_garantia,
                cfg.user_id,
            ),
        )
        if cur.rowcount == 0:
            self._conn.execute(
                """
                INSERT INTO config_empresa (
                    user_id, logo, razao_social, cnpj, nome_fantasia, endereco, cidade,
                    estado, telefone, email, website, mensagem_rodape, termos_garantia
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cfg.user_id,
                    cfg.logo,
                    cfg.razao_social,
                    cfg.cnpj,
                    cfg.nome_fantasia,
                    cfg.endereco,
                    cfg.cidade,
                    cfg.estado,
                    cfg.telefone,
                    cfg.email,
                    cfg.website,
                    cfg.mensagem_rodape,
                    cfg.termos_garantia,
                ),
            )
        self._conn.commit()

    # --- perfil ------------------------------------------------------------
    def obter_perfil(self, user_id: int = 0) -> Optional[PerfilUsuario]:
        row = self._conn.execute(
            "SELECT * FROM perfil_usuario WHERE user_id=?", (user_id,)
        ).fetchone()
        return _row_para_perfil(row) if row else None

    def salvar_perfil(self, p: PerfilUsuario) -> None:
        cur = self._conn.execute(
            """
            UPDATE perfil_usuario SET
                nome=?, telefone=?, email=?, foto=?, bio=?, nascimento=?,
                notif_email=?, notif_push=?
            WHERE user_id=?
            """,
            (
                p.nome,
                p.telefone,
                p.email,
                p.foto,
                p.bio,
                p.nascimento,
                int(p.notif_email),
                int(p.notif_push),
                p.user_id,
            ),
        )
        if cur.rowcount == 0:
            self._conn.execute(
                """
                INSERT INTO perfil_usuario (
                    user_id, nome, telefone, email, foto, bio, nascimento,
                    notif_email, notif_push
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    p.user_id,
                    p.nome,
                    p.telefone,
                    p.email,
                    p.foto,
                    p.bio,
                    p.nascimento,
                    int(p.notif_email),
                    int(p.notif_push),
                ),
            )
        self._conn.commit()
