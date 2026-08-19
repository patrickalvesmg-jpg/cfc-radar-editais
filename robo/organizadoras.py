# -*- coding: utf-8 -*-
"""
Catálogo de organizadoras (bancas).

Guarda, em `data/organizadoras.json`, quem organiza cada concurso: nome
canônico, domínio e se é fonte primária nossa. Serve para três coisas:

  1. **exibir a banca no site**, com nome próprio em vez de um domínio
     solto ("Fundação FAFIPA", não "fundacaofafipa.org.br");
  2. **saber onde vale investir**: banca que aparece muito nos nossos
     editais é candidata a virar fonte primária, como já ocorreu com
     FAFIPA (8 editais) e IBGP (5);
  3. **distinguir banca de agregador** — só banca pode receber o
     visitante.

O catálogo do PCI (382 organizadoras) alimenta a lista de nomes; o
vínculo com cada edital sai do domínio do link de inscrição.
"""

import json
import re
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO = RAIZ / "data" / "organizadoras.json"

# Domínio → nome canônico. Preenchido a partir do catálogo do PCI e do
# que já observamos nos editais capturados.
CANONICO = {
    "fundacaofafipa.org.br": "Fundação FAFIPA",
    "ibgpconcursos.com.br": "IBGP Concursos",
    "cebraspe.org.br": "CESPE/CEBRASPE",
    "avancasp.org.br": "AvançaSP",
    "glconsultoria.com.br": "GL Consultoria",
    "institutoconsulplan.org.br": "Instituto Consulplan",
    "objetivas.com.br": "Objetiva Concursos",
    "legalleconcursos.com.br": "Legalle Concursos",
    "institutolegalle.org.br": "Instituto Legalle",
    "inepam.org.br": "INEPAM",
    "exameconsultores.com.br": "Exame Consultores",
    "institutoaplicativa.org.br": "Instituto Aplicativa",
    "aplicativa.net.br": "Instituto Aplicativa",
    "nossorumo.org.br": "Instituto Nosso Rumo",
    "access.org.br": "Instituto Access",
    "imam.org.br": "IMAM Concursos",
    "imeso.com.br": "IMESO",
    "jcmconcursos.com.br": "JCM Concursos",
    "gestaodeconcursos.com.br": "Fundep / Gestão de Concursos",
    "fundatec.org.br": "FUNDATEC",
    "selecao.net.br": "Seleção Concursos",
    "fadeconcursos.org.br": "FADE-UFPE",
    "institutoindec.org.br": "Instituto INDEC",
    "institutounicampo.com.br": "Instituto UniCampo",
    "gamaconsult.com.br": "Gama Consult",
    "ajuri.org.br": "Instituto Ajuri",
    "integribrasil.com.br": "Integri Brasil",
    "ibamsp-concursos.org.br": "IBAM-SP",
    "institutoibepp.com.br": "Instituto IBEPP",
    "ibgpconcursos.com": "IBGP Concursos",
    "quadrix.org.br": "Instituto Quadrix",
    "institutomais.org.br": "Instituto Mais",
    "comperve.ufrn.br": "COMPERVE/UFRN",
    "ibfc.org.br": "IBFC",
    "vunesp.com.br": "VUNESP",
    "idecan.org.br": "IDECAN",
}

# Bancas que já usamos como FONTE PRIMÁRIA (varremos o catálogo delas).
FONTES_PRIMARIAS = {
    "fundacaofafipa.org.br", "cebraspe.org.br",
    "avancasp.org.br", "access.org.br", "exameconsultores.com.br",
    "institutoconsulplan.org.br",
}


# Hosts que só servem arquivo — não são a banca. O PDF do CEBRASPE mora
# em cdn.cebraspe.org.br e o da FAFIPA em anexos-r2.selecao.net.br;
# tomar esses domínios como organizadora criava entradas "CDN" e
# "Anexos-r2" no catálogo.
HOSTS_DE_ARQUIVO = re.compile(
    r"^(?:cdn|anexos|arquivos|static|media|storage|s3|files)[\.-]", re.I
)


def dominio(url: str) -> str:
    """Domínio normalizado: tira www/novo/portal/app/concursos."""
    if not url:
        return ""
    try:
        host = urlparse(url).netloc.lower()
    except ValueError:
        return ""
    # Subdomínio não identifica a banca: "editais.legalleconcursos.com.br"
    # e "portal.institutoibepp.com.br" são a mesma organizadora do domínio
    # raiz. Sem isso o catálogo criava entradas "Editais" e "Portal".
    # Remove QUALQUER subdomínio de serviço, inclusive encadeado
    # ("editais.legalleconcursos.com.br" e "legalleconcursos.com.br" são a
    # mesma banca e viravam duas entradas no catálogo).
    _SERVICO = (
        "www", "novo", "portal", "app", "concurso", "concursos",
        "inscricao", "inscricoes", "edital", "editais", "site",
        "selecao", "sistema", "candidato",
    )
    partes = host.split(".")
    while len(partes) > 2 and partes[0] in _SERVICO:
        partes.pop(0)
    host = ".".join(partes)
    # Órgão público (rs.gov.br, pr.gov.br) não é banca: quem organiza é
    # outra entidade, e o nome viraria a sigla do estado.
    if re.fullmatch(r"[a-z]{2}\.gov\.br", host):
        return ""
    return host


def nome_da_banca(url: str) -> str:
    """Nome de exibição da organizadora, a partir de qualquer link dela."""
    d = dominio(url)
    if not d:
        return ""
    if d in CANONICO:
        return CANONICO[d]
    # Sem cadastro: o rótulo principal do domínio, que ao menos é
    # verificável. Siglas curtas ficam em caixa alta.
    base = d.split(".")[0].replace("-", " ")
    if len(base) <= 5:
        return base.upper()
    return base[:1].upper() + base[1:]


def vincular(editais: list[dict]) -> None:
    """Preenche `banca` e `bancaSite` em cada edital, quando faltarem."""
    for e in editais:
        # O site de INSCRIÇÃO identifica a banca; o PDF costuma estar num
        # CDN separado, que não diz quem organiza.
        ref = e.get("siteInscricao") or ""
        if not ref or HOSTS_DE_ARQUIVO.search(dominio(ref)):
            ref = e.get("pdfEdital") or ref
        d = dominio(ref)
        if not d:
            continue
        if not e.get("banca"):
            e["banca"] = nome_da_banca(ref)
        e["bancaDominio"] = d


def gravar_catalogo(editais: list[dict]) -> None:
    """Grava o catálogo com a contagem de editais por organizadora."""
    contagem: dict[str, int] = {}
    for e in editais:
        d = e.get("bancaDominio") or dominio(e.get("siteInscricao") or "")
        if d and not HOSTS_DE_ARQUIVO.search(d):
            contagem[d] = contagem.get(d, 0) + 1

    catalogo = [
        {
            "dominio": d,
            "nome": CANONICO.get(d, nome_da_banca(f"https://{d}")),
            "editais": n,
            "fontePrimaria": d in FONTES_PRIMARIAS,
            "site": f"https://{d}/",
        }
        for d, n in sorted(contagem.items(), key=lambda x: -x[1])
    ]

    ARQUIVO.parent.mkdir(parents=True, exist_ok=True)
    ARQUIVO.write_text(
        json.dumps(catalogo, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    primarias = sum(1 for c in catalogo if c["fontePrimaria"])
    print(f"  Organizadoras: {len(catalogo)} ({primarias} como fonte primária)")
