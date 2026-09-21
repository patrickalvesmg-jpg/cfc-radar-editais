# -*- coding: utf-8 -*-
"""Edital sem link nenhum some do site — a regra do "beco sem saída"
esconde quem não tem para onde mandar o candidato. Por isso vale
mandar para a home da banca quando não achamos a página do certame.

Bug real de 14/09/2026: 15 dos 31 editais novos ficaram invisíveis
porque `_site_inscricao` devolvia vazio. Duas causas:

  · lista fechada de terminações (org/com/net/gov/edu) deixava de fora
    a Câmara de Ibirama, cuja inscrição é em
    `portal.sctreinamentos.selecao.site`;
  · só aceitava href com "concurso/edital/informacoes/processo" no
    caminho, então a home da banca era descartada.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fontes.pci_api import _site_inscricao


def test_aceita_dominio_de_terminacao_incomum():
    """Caso Ibirama: o .site não entrava na lista antiga."""
    texto = ("As inscrições podem ser realizadas exclusivamente via internet, "
             "no site portal.sctreinamentos.selecao.site , de 10 de setembro")
    r = _site_inscricao(texto, "")
    assert "sctreinamentos" in r
    assert r.startswith("https://")


def test_usa_a_home_da_banca_quando_nao_ha_pagina_do_certame():
    html = '<a href="https://www.bancaexemplo.com.br/">Banca</a>'
    r = _site_inscricao("", html)
    assert r == "https://www.bancaexemplo.com.br/"


def test_pagina_do_certame_tem_prioridade_sobre_a_home():
    html = ('<a href="https://www.bancaexemplo.com.br/">Home</a>'
            '<a href="https://www.bancaexemplo.com.br/concurso/12">Certame</a>')
    assert _site_inscricao("", html).endswith("/concurso/12")


def test_prefere_a_banca_ao_site_da_prefeitura():
    """O .gov.br costuma ser o órgão, que não hospeda a inscrição."""
    html = ('<a href="https://www.camaraibirama.sc.gov.br/">Câmara</a>'
            '<a href="https://portal.sctreinamentos.selecao.site/">Banca</a>')
    assert "sctreinamentos" in _site_inscricao("", html)


def test_nunca_devolve_agregador():
    html = '<a href="https://www.pciconcursos.com.br/noticias/x">PCI</a>'
    assert _site_inscricao("", html) == ""


def test_nunca_devolve_infraestrutura_da_pagina():
    """O fallback de "qualquer link externo" chegou a mandar o
    candidato para o servidor de fontes do Google (14/09/2026)."""
    html = ('<a href="https://fonts.gstatic.com">fonte</a>'
            '<a href="https://cdnjs.cloudflare.com/x.js">cdn</a>')
    assert _site_inscricao("", html) == ""


def test_infraestrutura_nao_rouba_a_vez_da_banca():
    html = ('<a href="https://fonts.gstatic.com">fonte</a>'
            '<a href="https://portal.bancaboa.selecao.site/">Banca</a>')
    assert "bancaboa" in _site_inscricao("", html)


def test_tela_de_login_nao_vira_destino():
    """Quem cai numa tela de login não vê o concurso, vê um campo de
    senha. Caso real: CPCON/UEPB entrava como
    sistemas.cpcon.uepb.edu.br/sigeps-app/login (Patrick, 14/09/2026)."""
    html = ('<a href="https://sistemas.cpcon.uepb.edu.br/sigeps-app/login">Entrar</a>'
            '<a href="https://cpcon.uepb.edu.br/">CPCON</a>')
    r = _site_inscricao("", html)
    assert "/login" not in r
    assert r == "https://cpcon.uepb.edu.br/"


def test_portal_da_banca_preferido_mesmo_sozinho_o_login_sendo_unico():
    """Só havendo login, melhor devolver vazio do que mandar para a
    tela de senha — o card some, mas ninguém é enganado."""
    html = '<a href="https://sistemas.exemplo.br/sigeps-app/login">Entrar</a>'
    assert _site_inscricao("", html) == ""
