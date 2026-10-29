"""Testes do módulo PDF (gera em temp e valida existência/tamanho/páginas).

Executar: python -m tests.test_pdf
"""
from __future__ import annotations

import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    import pymupdf

    from app.core.models.models import (
        Cliente,
        ConfigEmpresa,
        OrdemServico,
        StatusOrdem,
        TipoDispositivo,
    )
    from app.core.pdf import (
        gerar_diagnostico_pdf,
        gerar_ordem_a4,
        gerar_ordem_termica,
        gerar_relatorio_pdf,
    )

    cliente = Cliente(
        id=1, nome="João da Silva", telefone="(11) 99999-0000", email="joao@ex.com"
    )
    ordem = OrdemServico(
        id=42,
        cliente_id=1,
        tipo_dispositivo=TipoDispositivo.SMARTPHONE,
        marca="Samsung",
        modelo="Galaxy A54",
        serie="SN123",
        valor=250.0,
        problema="Tela trincada <b>não liga</b>",
        diagnostico="Display danificado",
        status=StatusOrdem.CONCLUIDO_SUCESSO,
        solucao="Troca do display",
        passos="1. Abertura\n2. Troca\n3. Teste",
        valor_final=280.0,
        data_entrada=datetime.now().isoformat(timespec="seconds"),
        data_conclusao=datetime.now().isoformat(timespec="seconds"),
    )
    cfg = ConfigEmpresa(
        nome_fantasia="Minha Oficina",
        razao_social="Minha Oficina LTDA",
        cnpj="00.000.000/0001-00",
        endereco="Rua A, 100",
        cidade="São Paulo",
        estado="SP",
        telefone="(11) 3000-0000",
        mensagem_rodape="Obrigado pela preferência!",
        termos_garantia="Garantia de 90 dias.",
    )

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)

        a4 = gerar_ordem_a4(ordem, cliente, cfg, tdp / "os_a4.pdf")
        assert a4.exists() and a4.stat().st_size > 500, "PDF A4 vazio"
        doc = pymupdf.open(str(a4))
        assert doc.page_count == 1, "A4 deveria ter 1 página"
        texto = doc[0].get_text()
        doc.close()
        assert "Galaxy A54" in texto, "conteúdo da OS ausente no A4"
        assert "João da Silva" in texto, "cliente ausente no A4"
        # O escape HTML transforma as tags em texto visível (não em formatação),
        # então o conteúdo do problema deve aparecer integralmente.
        assert "não liga" in texto, "conteúdo do problema ausente no A4"

        tic = gerar_ordem_termica(ordem, cliente, cfg, tdp / "os_80mm.pdf")
        assert tic.exists() and tic.stat().st_size > 300, "PDF térmico vazio"
        doc = pymupdf.open(str(tic))
        largura_mm = doc[0].rect.width / 2.8346
        doc.close()
        assert abs(largura_mm - 80.0) < 1.0, f"largura térmica {largura_mm:.1f}mm != 80mm"

        diag = gerar_diagnostico_pdf(
            {"Bateria": "87%", "CPU": "4 núcleos"}, tdp / "diag.pdf"
        )
        assert diag.exists() and diag.stat().st_size > 300, "PDF de diagnóstico vazio"
        doc = pymupdf.open(str(diag))
        texto = doc[0].get_text()
        doc.close()
        assert "Bateria" in texto and "87%" in texto

        rel = gerar_relatorio_pdf(
            "Relatório diário",
            [("Em reparo", "2"), ("Faturamento", "R$ 300,00")],
            tdp / "rel.pdf",
        )
        assert rel.exists() and rel.stat().st_size > 300, "PDF de relatório vazio"

    print("OK — 4 PDFs gerados e validados (A4, térmico 80mm, diagnóstico, relatório).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
