# -*- coding: utf-8 -*-
"""Testes do catálogo de organizadoras.

O que mais importa aqui: **banca sem edital aberto não pode sumir**.
Era o comportamento antigo — o catálogo nascia só dos editais
capturados — e apagava o mapa de onde procurar concurso.
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import organizadoras as org

MAPA = [
    {"dominio": "bancaviva.com.br", "nome": "Banca Viva",
     "site": "https://bancaviva.com.br/", "concursosHistorico": 120,
     "estados": ["SP"], "situacao": "reserva"},
    {"dominio": "bancaquieta.org.br", "nome": "Banca Quieta",
     "site": "https://bancaquieta.org.br/", "concursosHistorico": 40,
     "estados": ["MG", "BA"], "situacao": "reserva"},
]


def _isolar(tmp):
    org.ARQUIVO = Path(tmp) / "organizadoras.json"
    (Path(tmp) / "bancas-catalogo.json").write_text(
        json.dumps(MAPA, ensure_ascii=False), encoding="utf-8")


def _ler(tmp):
    return {c["dominio"]: c
            for c in json.loads((Path(tmp) / "organizadoras.json")
                                .read_text(encoding="utf-8"))}


def teste_banca_sem_edital_permanece():
    """O ponto central: quem não tem concurso agora continua no mapa."""
    with tempfile.TemporaryDirectory() as tmp:
        _isolar(tmp)
        editais = [{"id": "1", "siteInscricao": "https://bancaviva.com.br/x"}]
        org.vincular(editais)
        org.gravar_catalogo(editais)
        cat = _ler(tmp)
        assert "bancaquieta.org.br" in cat, "banca sem edital sumiu do catálogo"
        assert cat["bancaquieta.org.br"]["editais"] == 0
        assert cat["bancaviva.com.br"]["editais"] == 1


def teste_preserva_estados_e_situacao():
    with tempfile.TemporaryDirectory() as tmp:
        _isolar(tmp)
        org.gravar_catalogo([])
        cat = _ler(tmp)
        assert cat["bancaquieta.org.br"]["estados"] == ["MG", "BA"]
        assert cat["bancaquieta.org.br"]["situacao"] == "reserva"


def teste_banca_nova_entra_no_catalogo():
    """Banca vista num edital mas ausente do mapa não pode ser perdida."""
    with tempfile.TemporaryDirectory() as tmp:
        _isolar(tmp)
        editais = [{"id": "1", "siteInscricao": "https://bancanova.com.br/y"}]
        org.vincular(editais)
        org.gravar_catalogo(editais)
        cat = _ler(tmp)
        assert "bancanova.com.br" in cat
        assert cat["bancanova.com.br"]["editais"] == 1


def teste_ordena_com_edital_primeiro():
    with tempfile.TemporaryDirectory() as tmp:
        _isolar(tmp)
        editais = [{"id": "1", "siteInscricao": "https://bancaquieta.org.br/z"}]
        org.vincular(editais)
        org.gravar_catalogo(editais)
        lista = json.loads((Path(tmp) / "organizadoras.json")
                           .read_text(encoding="utf-8"))
        assert lista[0]["dominio"] == "bancaquieta.org.br"


def teste_dominio_em_tld_composto():
    """`selecao.net.br` É a banca, não subdomínio de serviço.

    O corte parava em 2 rótulos, então "selecao" era comido como se
    fosse prefixo e sobrava "net.br" — o site montava o link da
    organizadora para `https://net.br/`. 3 editais afetados em 31/08.
    """
    assert org.dominio("https://selecao.net.br") == "selecao.net.br"
    assert org.dominio("https://www.selecao.net.br") == "selecao.net.br"


def teste_subdominio_de_servico_ainda_e_cortado():
    """A correção acima não pode desfazer o motivo original da regra."""
    assert org.dominio(
        "https://editais.legalleconcursos.com.br/a") == "legalleconcursos.com.br"
    assert org.dominio(
        "https://novo.ibgpconcursos.com.br/y") == "ibgpconcursos.com.br"
    assert org.dominio("https://portal.institutoibepp.com.br/") == "institutoibepp.com.br"


def teste_orgao_publico_nao_e_banca():
    assert org.dominio("https://rs.gov.br/") == ""


def teste_cdn_nao_vira_banca():
    """Host de arquivo não é organizadora — já custou entradas 'CDN'."""
    with tempfile.TemporaryDirectory() as tmp:
        _isolar(tmp)
        editais = [{"id": "1", "siteInscricao": "https://cdn.cebraspe.org.br/a.pdf"}]
        org.vincular(editais)
        org.gravar_catalogo(editais)
        assert not any(d.startswith("cdn.") for d in _ler(tmp))


if __name__ == "__main__":
    testes = [v for k, v in sorted(globals().items()) if k.startswith("teste_")]
    for t in testes:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(testes)} testes passaram")
