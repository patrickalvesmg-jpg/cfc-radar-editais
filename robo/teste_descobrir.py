# -*- coding: utf-8 -*-
"""Testes da descoberta que não dependem de rede."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import descobrir


def test_corrige_url_do_ibgp():
    """O IBGP renomeou o caminho mantendo o número; os links antigos
    que guardamos devolvem 404."""
    velho = "https://novo.ibgpconcursos.com.br/informacoes/747/"
    assert descobrir.corrigir_url(velho) == \
        "https://novo.ibgpconcursos.com.br/concurso.jsp?cod=747"
    # sem barra final também
    assert descobrir.corrigir_url(
        "https://www.ibgpconcursos.com.br/informacoes/665") == \
        "https://www.ibgpconcursos.com.br/concurso.jsp?cod=665"


def test_nao_mexe_em_url_de_outra_banca():
    """A FAFIPA usa /informacoes/ e continua funcionando — trocar
    quebraria um link que está certo."""
    u = "https://www.fundacaofafipa.org.br/informacoes/4205/"
    assert descobrir.corrigir_url(u) == u


def test_descarta_javascript_e_pdf():
    """Link `javascript:void(0)` não leva a lugar nenhum; foram 3 dos
    38 'acertos' da primeira medição."""
    assert descobrir.PADRAO_RUIM.search("javascript:__doPostBack('ctl00')")
    assert descobrir.PADRAO_RUIM.search("https://x.org/termos.pdf")
    assert descobrir.PADRAO_RUIM.search("https://x.org/politica_lgpd.pdf")
    assert not descobrir.PADRAO_RUIM.search(
        "https://novo.ibgpconcursos.com.br/concurso.jsp?cod=747")


def test_chaves_usam_cidade_e_sigla():
    """Órgão sem cidade ('EMDAEP') só aparece pela sigla."""
    ks = descobrir.chaves_do_edital(
        {"cidade": "Lagoa da Prata", "orgao": "MUNICÍPIO DE LAGOA DA PRATA"})
    assert "lagoa da prata" in ks

    ks2 = descobrir.chaves_do_edital(
        {"cidade": "", "orgao": "EMDAEP - Empresa de Desenvolvimento"})
    assert any(k.startswith("emdaep") for k in ks2), ks2


def test_casar_le_o_card_nao_so_o_link():
    """No IBGP o texto do <a> é 'SAIBA MAIS'; a cidade está no card.
    Ler só o link dava 418 candidatos e zero casamentos."""
    dados = [("https://novo.ibgpconcursos.com.br/concurso.jsp?cod=665",
              "SAIBA MAIS EDITAL Nº 01/2026 MUNICÍPIO DE LAGOA DA PRATA/MG")]
    assert descobrir._casar(dados, ["lagoa da prata"]).endswith("cod=665")


if __name__ == "__main__":
    falhas = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            try:
                fn()
                print(f"  ok   {nome}")
            except AssertionError as e:
                print(f"  FALHA {nome}: {e}")
                falhas += 1
    print(f"\n{falhas} falha(s)")
    sys.exit(1 if falhas else 0)
