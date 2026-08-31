# -*- coding: utf-8 -*-
"""Testes do arquivamento de PDF. Sem rede: os bytes são montados aqui."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import arquivo_pdf

# Um PDF mínimo de verdade: precisa começar com %PDF para passar pela
# checagem que existe porque link "de PDF" muitas vezes devolve HTML.
PDF_OK = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"
HTML = b"<!doctype html><html><body>Pagina de erro</body></html>"


def _isolar(tmp):
    """Aponta o modulo para uma pasta temporaria."""
    arquivo_pdf.PASTA = Path(tmp) / "editais-pdf"
    arquivo_pdf.INDICE = arquivo_pdf.PASTA / "indice.json"


def teste_guarda_pdf_valido():
    with tempfile.TemporaryDirectory() as tmp:
        _isolar(tmp)
        r = arquivo_pdf.guardar_bytes("abc", "https://banca/e.pdf", PDF_OK)
        assert r is not None, "PDF valido deveria ser guardado"
        assert (Path(tmp) / "editais-pdf" / Path(r["arquivo"]).name).exists()
        assert r["bytes"] == len(PDF_OK)


def teste_recusa_html_disfarcado():
    """O caso real: a URL termina em .pdf e devolve pagina de erro."""
    with tempfile.TemporaryDirectory() as tmp:
        _isolar(tmp)
        assert arquivo_pdf.guardar_bytes("abc", "https://b/e.pdf", HTML) is None
        assert not arquivo_pdf.PASTA.exists() or not list(
            arquivo_pdf.PASTA.glob("*.pdf"))


def teste_recusa_arquivo_gigante():
    with tempfile.TemporaryDirectory() as tmp:
        _isolar(tmp)
        gigante = PDF_OK + b"\0" * (arquivo_pdf.LIMITE_BYTES + 1)
        assert arquivo_pdf.guardar_bytes("abc", "https://b/e.pdf", gigante) is None


def teste_conteudo_diferente_vira_arquivo_novo():
    """Edital retificado nao pode sobrescrever o que ja lemos."""
    with tempfile.TemporaryDirectory() as tmp:
        _isolar(tmp)
        a = arquivo_pdf.guardar_bytes("x1", "https://b/e.pdf", PDF_OK)
        b = arquivo_pdf.guardar_bytes("x1", "https://b/e.pdf", PDF_OK + b"%v2\n")
        assert a["arquivo"] != b["arquivo"], "retificacao deveria gerar outro arquivo"
        assert len(list(arquivo_pdf.PASTA.glob("*.pdf"))) == 2


def teste_mesmo_conteudo_nao_duplica():
    with tempfile.TemporaryDirectory() as tmp:
        _isolar(tmp)
        a = arquivo_pdf.guardar_bytes("x1", "https://b/e.pdf", PDF_OK)
        b = arquivo_pdf.guardar_bytes("x1", "https://b/e.pdf", PDF_OK)
        assert a["arquivo"] == b["arquivo"]
        assert len(list(arquivo_pdf.PASTA.glob("*.pdf"))) == 1


def teste_aplica_campo_nos_editais():
    with tempfile.TemporaryDirectory() as tmp:
        _isolar(tmp)
        arquivo_pdf.guardar_bytes("e1", "https://b/e.pdf", PDF_OK)
        editais = [{"id": "e1"}, {"id": "e2"}]
        n = arquivo_pdf.aplicar_aos_editais(editais)
        assert n == 1
        assert editais[0]["pdfArquivo"].startswith("data/editais-pdf/")
        assert "pdfArquivo" not in editais[1], "edital sem copia nao pode ganhar campo"


if __name__ == "__main__":
    testes = [v for k, v in sorted(globals().items()) if k.startswith("teste_")]
    for t in testes:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(testes)} testes passaram")
