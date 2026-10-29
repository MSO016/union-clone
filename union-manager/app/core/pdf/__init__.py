"""Geração de PDF própria (PyMuPDF)."""
from .ordem_pdf import (
    gerar_diagnostico_pdf,
    gerar_ordem_a4,
    gerar_ordem_termica,
    gerar_relatorio_pdf,
)

__all__ = [
    "gerar_ordem_a4",
    "gerar_ordem_termica",
    "gerar_diagnostico_pdf",
    "gerar_relatorio_pdf",
]
