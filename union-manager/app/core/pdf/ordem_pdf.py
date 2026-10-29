"""Geração de PDFs (A4, térmico 80 mm, diagnóstico, relatórios) — SPEC RF-PDF-*.

Usa PyMuPDF (`import pymupdf`) com `insert_htmlbox` para compor o conteúdo.
Nenhum layout vem do alvo original: é implementação própria.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional

import pymupdf

from ..models.models import (
    Cliente,
    ConfigEmpresa,
    OrdemServico,
    StatusOrdem,
)

# Largura útil de uma impressora térmica de 80 mm em pontos PDF (1 mm ≈ 2.835 pt).
_LARGURA_TERMICA_MM = 80.0
_MM_PT = 2.8346  # pontos por mm


def _esc(texto: str) -> str:
    """Escape mínimo de HTML para campos livres do usuário."""
    return (
        (texto or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _status_rotulo(s: StatusOrdem) -> str:
    return {
        StatusOrdem.EM_REPARO: "Em reparo",
        StatusOrdem.CONCLUIDO_SUCESSO: "Concluído com sucesso",
        StatusOrdem.CONCLUIDO_SEM_SOLUCAO: "Concluído sem solução",
    }[s]


def _cabecalho_empresa(cfg: Optional[ConfigEmpresa]) -> str:
    if cfg is None:
        return "<h1>Union Manager</h1>"
    linhas = [f"<h1>{_esc(cfg.nome_fantasia or cfg.razao_social or 'Oficina')}</h1>"]
    if cfg.razao_social and cfg.nome_fantasia:
        linhas.append(f"<p>{_esc(cfg.razao_social)}</p>")
    if cfg.cnpj:
        linhas.append(f"<p>CNPJ: {_esc(cfg.cnpj)}</p>")
    if cfg.endereco:
        linhas.append(f"<p>{_esc(cfg.endereco)}</p>")
    if cfg.cidade or cfg.estado:
        linhas.append(f"<p>{_esc(cfg.cidade)} {_esc(cfg.estado)}</p>")
    if cfg.telefone:
        linhas.append(f"<p>Tel.: {_esc(cfg.telefone)}</p>")
    return "".join(linhas)


def _dados_ordem_html(o: OrdemServico, c: Optional[Cliente]) -> str:
    nome = c.nome if c else str(o.cliente_id)
    tel = c.telefone if c else ""
    valor = f"R$ {o.valor_final if o.valor_final is not None else (o.valor or 0):,.2f}"
    linhas = [
        f"<p><b>OS nº</b> {o.id} &nbsp; <b>Status:</b> {_status_rotulo(o.status)}</p>",
        f"<p><b>Cliente:</b> {_esc(nome)} &nbsp; <b>Telefone:</b> {_esc(tel)}</p>",
        f"<p><b>Dispositivo:</b> {o.tipo_dispositivo.value} — {_esc(o.marca)} {_esc(o.modelo)}</p>",
    ]
    if o.serie:
        linhas.append(f"<p><b>Série:</b> {_esc(o.serie)}</p>")
    linhas.append(f"<p><b>Data de entrada:</b> {_esc(o.data_entrada)}</p>")
    if o.data_conclusao:
        linhas.append(f"<p><b>Data de conclusão:</b> {_esc(o.data_conclusao)}</p>")
    linhas.append(f"<p><b>Valor:</b> {valor}</p>")
    linhas.append(f"<p><b>Problema relatado:</b><br/>{_esc(o.problema)}</p>")
    if o.diagnostico:
        linhas.append(f"<p><b>Diagnóstico:</b><br/>{_esc(o.diagnostico)}</p>")
    if o.solucao:
        linhas.append(f"<p><b>Solução:</b><br/>{_esc(o.solucao)}</p>")
    if o.passos:
        linhas.append(f"<p><b>Passos realizados:</b><br/>{_esc(o.passos)}</p>")
    if o.motivo_falha:
        linhas.append(f"<p><b>Motivo da falha:</b><br/>{_esc(o.motivo_falha)}</p>")
    return "".join(linhas)


def _rodape_html(cfg: Optional[ConfigEmpresa]) -> str:
    termos = cfg.termos_garantia if cfg else ""
    rodape = cfg.mensagem_rodape if cfg else ""
    partes = []
    if termos:
        partes.append(f"<p class='menor'><b>Termos de garantia:</b> {_esc(termos)}</p>")
    if rodape:
        partes.append(f"<p class='menor'>{_esc(rodape)}</p>")
    partes.append("<p class='menor'>Documento gerado por Union Manager.</p>")
    return "".join(partes)


_CSS = """
h1 { font-size: 16px; margin-bottom: 2px; }
h2 { font-size: 13px; }
p { margin: 2px 0; font-size: 11px; }
.menor { font-size: 8px; color: #555; }
"""


_CSS_TERMICO = """
h1 { font-size: 12px; margin-bottom: 2px; }
p { margin: 1px 0; font-size: 8px; }
.menor { font-size: 7px; color: #555; }
"""


def gerar_ordem_a4(
    ordem: OrdemServico,
    cliente: Optional[Cliente],
    cfg: Optional[ConfigEmpresa],
    destino: Path,
) -> Path:
    """Ordem de serviço em A4 (RF-PDF-1)."""
    doc = pymupdf.open()
    a4 = pymupdf.paper_rect("a4")
    html = (
        _cabecalho_empresa(cfg)
        + "<hr/>"
        + _dados_ordem_html(ordem, cliente)
        + "<hr/>"
        + _rodape_html(cfg)
    )
    pagina = doc.new_page(width=a4.width, height=a4.height)
    pagina.insert_htmlbox(
        pymupdf.Rect(40, 40, a4.width - 40, a4.height - 40), html, css=_CSS
    )
    destino = Path(destino)
    doc.save(str(destino))
    doc.close()
    return destino


def gerar_ordem_termica(
    ordem: OrdemServico,
    cliente: Optional[Cliente],
    cfg: Optional[ConfigEmpresa],
    destino: Path,
    altura_mm: float = 200.0,
) -> Path:
    """Cupom em bobina térmica de 80 mm (RF-PDF-2)."""
    doc = pymupdf.open()
    largura = _LARGURA_TERMICA_MM * _MM_PT
    altura = altura_mm * _MM_PT
    html = (
        _cabecalho_empresa(cfg)
        + _dados_ordem_html(ordem, cliente)
        + _rodape_html(cfg)
    )
    pagina = doc.new_page(width=largura, height=altura)
    pagina.insert_htmlbox(
        pymupdf.Rect(8, 8, largura - 8, altura - 8), html, css=_CSS_TERMICO
    )
    destino = Path(destino)
    doc.save(str(destino))
    doc.close()
    return destino


def gerar_diagnostico_pdf(
    dados: dict[str, str],
    destino: Path,
    titulo: str = "Diagnóstico de dispositivo",
) -> Path:
    """Laudo simples de diagnóstico (RF-PDF-3): pares chave/valor."""
    doc = pymupdf.open()
    a4 = pymupdf.paper_rect("a4")
    linhas = [f"<h1>{_esc(titulo)}</h1>"]
    linhas.append(f"<p><b>Data:</b> {date.today().isoformat()}</p><hr/>")
    for chave, valor in dados.items():
        linhas.append(f"<p><b>{_esc(chave)}:</b> {_esc(valor)}</p>")
    pagina = doc.new_page(width=a4.width, height=a4.height)
    pagina.insert_htmlbox(
        pymupdf.Rect(40, 40, a4.width - 40, a4.height - 40),
        "".join(linhas),
        css=_CSS,
    )
    destino = Path(destino)
    doc.save(str(destino))
    doc.close()
    return destino


def gerar_relatorio_pdf(
    titulo: str,
    linhas: list[tuple[str, str]],
    destino: Path,
) -> Path:
    """Relatório (diário/mensal) em A4 (RF-REP-1/2 + RF-PDF-4)."""
    doc = pymupdf.open()
    a4 = pymupdf.paper_rect("a4")
    partes = [f"<h1>{_esc(titulo)}</h1>"]
    partes.append(f"<p><b>Emitido em:</b> {date.today().isoformat()}</p><hr/>")
    for rotulo, valor in linhas:
        partes.append(f"<p><b>{_esc(rotulo)}:</b> {_esc(valor)}</p>")
    pagina = doc.new_page(width=a4.width, height=a4.height)
    pagina.insert_htmlbox(
        pymupdf.Rect(40, 40, a4.width - 40, a4.height - 40),
        "".join(partes),
        css=_CSS,
    )
    destino = Path(destino)
    doc.save(str(destino))
    doc.close()
    return destino
