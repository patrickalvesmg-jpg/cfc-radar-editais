# -*- coding: utf-8 -*-
"""_limpar_orgao() usa "/" como separador de "Órgão/UF" — mas "S/A"
(Sociedade Anônima) também tem barra, e não é separador nenhum. Bug
real de 08/09/2026: "EPTC - Empresa Pública de Transporte e
Circulação S/A" virou orgao="A" no card publicado."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from extrair import _limpar_orgao


def test_sigla_sa_nao_e_confundida_com_separador_de_uf():
    r = _limpar_orgao(
        "EPTC - Empresa Pública de Transporte e Circulação S/A", "titulo"
    )
    assert r == "EPTC - Empresa Pública de Transporte e Circulação S/A"
    assert r != "A"


def test_prefeitura_com_uf_continua_cortando_a_uf():
    r = _limpar_orgao("Prefeitura de Exemplo/SP", "titulo")
    assert r == "Prefeitura de Exemplo"


def test_sa_seguido_de_uf_preserva_sigla_e_corta_uf():
    r = _limpar_orgao("Companhia XYZ S/A/MG", "titulo")
    assert r == "Companhia XYZ S/A"
