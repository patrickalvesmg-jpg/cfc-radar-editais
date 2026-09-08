# -*- coding: utf-8 -*-
"""Link de isenção/resultado/gabarito não pode virar "a página do
concurso". Bug real de 08/09/2026: UFPE mandava para
"baixar_noticia.php?id=..." — resultado de isenção de taxa (lista com
CPF de candidatos), não o edital. Quem clicasse "Ver edital" no card
caía nesse documento errado."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fontes import pci, pci_api


def test_pci_e_util_rejeita_link_de_isencao():
    assert not pci._e_util(
        "https://fadeconcursos.org.br/concursoufpe2026/resultado_isencao.php?id=20"
    )


def test_pci_e_util_aceita_link_de_edital_normal():
    assert pci._e_util("https://fadeconcursos.org.br/concursoufpe2026/edital.php")


def test_pci_api_site_inscricao_pula_link_de_isencao():
    html = (
        '<a href="https://fadeconcursos.org.br/concursoufpe2026/'
        'baixar_isencao.php?id=MjA=">Isenção</a>'
        '<a href="https://fadeconcursos.org.br/concursoufpe2026/'
        'concurso/edital-2026.pdf">Edital</a>'
    )
    r = pci_api._site_inscricao("", html)
    assert "isencao" not in r.lower()
    assert "edital" in r.lower()
