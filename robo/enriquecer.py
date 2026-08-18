# -*- coding: utf-8 -*-
"""
Enriquecimento: link da PÁGINA DO CONCURSO.

Problema medido: o PCI — nossa maior fonte — ancora só a **home** da
banca ("ibgpconcursos.com.br/"). O candidato clica e ainda precisa
caçar o concurso dele no site. Já o Concursos no Brasil ancora o
endereço completo do certame ("integribrasil.com.br/Concurso/Detail/375",
"institutolegalle.org.br/edital/ver/82"): em amostra de 8 matérias, 8
tinham link específico.

Este módulo busca, na API dos portais WordPress, a matéria que fala do
MESMO órgão e extrai daí o link específico. É acréscimo: se não achar,
o edital mantém o domínio da banca, que já funcionava.
"""

import json
import re
import unicodedata
import urllib.parse

from http_util import buscar
from fontes.portais_wp import PORTAIS, _link_concurso


def _chave(texto: str) -> str:
    """Nome do órgão reduzido ao essencial, para casar entre fontes."""
    t = unicodedata.normalize("NFD", str(texto or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(
        r"\b(prefeitura|municipal|municipio|camara|de|do|da|dos|das|e"
        r"|estancia|turistica|hidromineral|instituto|previdencia"
        r"|autarquia|consorcio|intermunicipal|fundacao|servico)\b",
        " ", t,
    )
    return re.sub(r"[^a-z0-9]+", "", t)


def _busca_api(api: str, termo: str) -> list:
    url = f"{api}?search={urllib.parse.quote(termo)}&per_page=5"
    corpo = buscar(url, checar_robots=False)
    if not corpo:
        return []
    try:
        dados = json.loads(corpo)
        return dados if isinstance(dados, list) else []
    except json.JSONDecodeError:
        return []


def link_do_concurso(orgao: str, uf: str = "") -> str:
    """Procura a página do certame nos portais. '' se não achar."""
    alvo = _chave(orgao)
    if len(alvo) < 4:
        return ""

    # Busca pelo nome "limpo" do órgão: "Prefeitura de Ipaba" -> "Ipaba".
    termo = re.sub(
        r"^\s*(?:prefeitura|c[âa]mara|munic[íi]pio)\s+(?:municipal\s+)?"
        r"(?:d[aeo]s?\s+)?",
        "", orgao, flags=re.I,
    ).strip()
    termo = re.split(r"\s*[-–—/]\s*", termo)[0].strip()[:40]
    if len(termo) < 3:
        return ""

    for portal in PORTAIS:
        for post in _busca_api(portal["api"], termo):
            titulo = re.sub(r"<[^>]+>", " ", post.get("title", {}).get("rendered", ""))
            if _chave(titulo).find(alvo) < 0:
                continue
            link = _link_concurso(post.get("content", {}).get("rendered", ""))
            if link:
                return link
    return ""
