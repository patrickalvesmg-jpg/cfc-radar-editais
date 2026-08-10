# -*- coding: utf-8 -*-
"""
Fonte: Querido Diário (Open Knowledge Brasil).

API pública e aberta que indexa diários oficiais MUNICIPAIS de todo o
Brasil — exatamente onde saem os concursos de contador de prefeitura,
que raramente aparecem em portal nacional.

Por que esta fonte e não o DOU:
o robots.txt de in.gov.br é `Disallow: /` para todos os agentes, ou
seja, proíbe raspagem automatizada do site inteiro. Respeitamos.
O Querido Diário publica `Allow: /` com `Content-Signal: use=reference`,
que é precisamente nosso uso: referenciamos o trecho e linkamos a fonte.

API: https://api.queridodiario.ok.org.br/docs
Dados sob licença aberta, mantidos pela Open Knowledge Brasil.
"""

import json
import urllib.parse

from config import eh_relevante
from http_util import buscar

API = "https://api.queridodiario.ok.org.br/api/gazettes"

# Cada busca combina o termo de concurso com um termo contábil.
# Fazer buscas separadas (e não uma só, ampla) reduz muito o ruído que
# chegaria ao filtro local.
CONSULTAS = (
    '"concurso público" AND contador',
    '"concurso público" AND "ciências contábeis"',
    '"concurso público" AND "técnico em contabilidade"',
    '"processo seletivo" AND contador',
    '"edital de abertura" AND contabilidade',
)


def _buscar(consulta: str, tamanho: int) -> list[dict]:
    params = urllib.parse.urlencode({
        "querystring": consulta,
        "size": tamanho,
        "sort_by": "descending_date",
    })
    # A API é feita para consumo automatizado; o robots.txt do host de API
    # não se aplica ao endpoint documentado.
    corpo = buscar(f"{API}?{params}", checar_robots=False)
    if not corpo:
        return []

    try:
        return json.loads(corpo).get("gazettes", []) or []
    except json.JSONDecodeError:
        print("    resposta não-JSON do Querido Diário")
        return []


def coletar(por_consulta: int = 25) -> list[dict]:
    """Roda as consultas e devolve os trechos que passam no filtro."""
    achados: list[dict] = []
    vistos: set[str] = set()

    for consulta in CONSULTAS:
        itens = _buscar(consulta, por_consulta)
        print(f"    {consulta[:46]:46} → {len(itens)}")

        for it in itens:
            url = it.get("url") or it.get("txt_url") or ""
            trechos = it.get("excerpts") or []
            texto = " ".join(trechos)

            if not texto or not eh_relevante(texto):
                continue

            municipio = it.get("territory_name") or ""
            uf = it.get("state_code") or ""
            chave = f"{municipio}|{it.get('date')}|{url}"
            if chave in vistos:
                continue
            vistos.add(chave)

            achados.append({
                "fonte": f"Diário Oficial de {municipio}/{uf}",
                "fonte_tipo": "querido_diario",
                "titulo": f"Concurso público — {municipio}/{uf}",
                "orgao_bruto": f"Prefeitura Municipal de {municipio}/{uf}",
                "texto": texto[:4000],
                "url": url,
                "publicado_em": it.get("date", ""),
                "_uf": uf,
                "_cidade": municipio,
            })

    return achados
