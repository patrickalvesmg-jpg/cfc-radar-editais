# -*- coding: utf-8 -*-
"""
Fonte: Radar do Estratégia — API do mapa de concursos.

https://www.estrategiaconcursos.com.br/blog/mapa-concursos

O mapa consome um GeoJSON com 1.662 concursos, e cada um traz
**latitude e longitude** — o único lugar onde encontramos coordenadas
prontas. É isso que alimenta o mapa interativo do nosso site.

Campos úteis: orgao, cidade, estado, esfera, situacao, vagasTotal,
salarioPrevisto, dataEncerraInscricoes, bancaOrganizadora, lat/long.

LIMITE IMPORTANTE: a API informa a ÁREA do concurso ("Fiscal",
"Legislativa", "Outras"), **nunca o cargo**. Não dá para afirmar que
existe vaga de contador só com esse dado — dos 166 abertos, apenas 4
são da área "Fiscal", e mesmo esses não confirmam cargo contábil.

Por isso esta fonte **não cria editais sozinha**. Ela cumpre dois papéis:
  1. dar coordenadas a editais que outras fontes confirmaram (o
     `atualizar.py` cruza por órgão + UF);
  2. servir de dicionário cidade/UF → lat/long para o mapa.

Permissão: robots.txt do domínio permite; o endpoint é o mesmo que a
página pública do mapa consome.
"""

import json
import re
import unicodedata

from http_util import buscar

API = ("https://www.estrategiaconcursos.com.br/blog/mapa-concursos"
       "/api/concursos/map")


# Prefixos institucionais que atrapalham o cruzamento: o mapa indexa
# "Piraju", nós temos "Prefeitura da Estância Turística de Piraju".
# Sem limpar isso, 42 de 55 editais caíam na capital do estado.
_RUIDO_ORGAO = re.compile(
    r"\b(prefeitura|municipio|municipal|camara|estancia|turistica|balneario"
    r"|autarquia|instituto|previdencia|consorcio|intermunicipal|fundacao"
    r"|servico|autonomo|agua|esgoto|saude|educacao|departamento|secretaria"
    r"|superintendencia|companhia|empresa|hospital|universidade|faculdade"
    r"|centro|regional|federal|estadual|de|do|da|dos|das|e|em|sa|ltda)\b",
    re.I,
)


def _sem_acento(texto: str) -> str:
    t = unicodedata.normalize("NFD", str(texto or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def _chave(texto: str) -> str:
    """Normaliza nome de órgão/cidade para cruzamento tolerante a acento,
    caixa e prefixo institucional."""
    t = _RUIDO_ORGAO.sub(" ", _sem_acento(texto))
    return re.sub(r"[^a-z0-9]+", "", t)


def nome_cidade(orgao: str) -> str:
    """Extrai o nome da cidade de dentro do nome do órgão.

    "Prefeitura de Limeira" -> "Limeira"
    "Câmara de Governador Valadares" -> "Governador Valadares"

    Devolve "" quando o nome não segue esse padrão — o campo fica vazio
    em vez de receber um palpite errado.
    """
    m = re.search(
        r"(?:prefeitura|c[âa]mara|munic[íi]pio)\s*"
        r"(?:municipal\s*)?(?:d[aeo]s?\s+)?"
        r"(?:est[âa]ncia\s+tur[íi]stica\s+d[aeo]\s+)?"
        r"([A-ZÀ-Ú][^\s,/-]*(?:\s+(?:d[aeo]s?\s+)?[A-ZÀ-Ú][^\s,/-]*){0,3})",
        str(orgao or ""),
        re.I,
    )
    if not m:
        return ""
    nome = re.sub(r"\s+", " ", m.group(1)).strip(" -–—/")
    return nome if len(nome) > 2 else ""


def coletar_geo() -> dict:
    """Devolve dois índices para o cruzamento:

        {"orgaos": {chave_orgao|UF: {...}}, "cidades": {chave_cidade|UF: (lat, lon)}}

    Não devolve achados: esta fonte não cria edital (ver docstring).
    """
    corpo = buscar(API, checar_robots=False)
    if not corpo:
        print("    API do mapa indisponível")
        return {"orgaos": {}, "cidades": {}}

    try:
        dados = json.loads(corpo)
    except json.JSONDecodeError:
        print("    resposta não-JSON")
        return {"orgaos": {}, "cidades": {}}

    feats = (dados.get("geojson") or {}).get("features") or []
    orgaos, cidades = {}, {}

    for f in feats:
        p = f.get("properties") or {}
        uf = (p.get("estado") or "").upper()
        lat, lon = p.get("latitude"), p.get("longitude")
        if not (uf and lat and lon):
            continue

        info = {
            "lat": lat, "lon": lon,
            "cidade": p.get("cidade") or "",
            "uf": uf,
            "banca": p.get("bancaOrganizadora") or "",
            "esfera": (p.get("esfera") or "").lower(),
        }

        ko = _chave(p.get("orgao"))
        if ko:
            orgaos[f"{ko}|{uf}"] = info

        kc = _chave(p.get("cidade"))
        if kc:
            cidades.setdefault(f"{kc}|{uf}", (lat, lon))

    print(f"    {len(feats)} concursos no mapa → "
          f"{len(orgaos)} órgãos, {len(cidades)} cidades georreferenciadas")
    return {"orgaos": orgaos, "cidades": cidades}


# ------------------------------------------------------------------
# Municípios brasileiros com coordenadas
# ------------------------------------------------------------------
# O mapa do Estratégia só georreferencia cidades onde ELE tem concurso —
# 440 no total. Nossos editais são de cidades pequenas (Auriflama,
# Rifaina, Santana de Pirapama), e 40 de 55 caíam na capital do estado.
#
# Esta base tem os 5.571 municípios do IBGE com lat/long, cobrindo 100%
# dos casos testados. É um JSON estático em repositório público, sob
# licença aberta, então não há robots.txt a consultar nem risco de
# sobrecarregar servidor de terceiro.
MUNICIPIOS_URL = (
    "https://raw.githubusercontent.com/kelvins/municipios-brasileiros"
    "/main/json/municipios.json"
)

# codigo_uf do IBGE -> sigla. O dataset traz o código, não a sigla.
_UF_POR_CODIGO = {
    11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO",
    21: "MA", 22: "PI", 23: "CE", 24: "RN", 25: "PB", 26: "PE", 27: "AL",
    28: "SE", 29: "BA", 31: "MG", 32: "ES", 33: "RJ", 35: "SP",
    41: "PR", 42: "SC", 43: "RS", 50: "MS", 51: "MT", 52: "GO", 53: "DF",
}


def coletar_municipios() -> dict:
    """Índice {chave_cidade|UF: (lat, lon)} dos 5.571 municípios."""
    corpo = buscar(MUNICIPIOS_URL, checar_robots=False)
    if not corpo:
        print("    base de municípios indisponível")
        return {}

    try:
        # O arquivo vem com BOM; sem o lstrip o json.loads quebra.
        dados = json.loads(corpo.lstrip("\ufeff"))
    except json.JSONDecodeError:
        print("    base de municípios em formato inesperado")
        return {}

    idx = {}
    for m in dados:
        uf = _UF_POR_CODIGO.get(m.get("codigo_uf"))
        lat, lon = m.get("latitude"), m.get("longitude")
        if not (uf and lat and lon):
            continue
        idx[f"{_chave(m.get('nome'))}|{uf}"] = (lat, lon)

    print(f"    {len(idx)} municípios com coordenada")
    return idx


# Capitais, para posicionar no mapa quando não achamos a cidade exata.
# Melhor um ponto no estado certo que nenhum ponto.
CAPITAIS = {
    "AC": (-9.9754, -67.8249), "AL": (-9.6498, -35.7089),
    "AM": (-3.1190, -60.0217), "AP": (0.0349, -51.0694),
    "BA": (-12.9777, -38.5016), "CE": (-3.7319, -38.5267),
    "DF": (-15.7939, -47.8828), "ES": (-20.3155, -40.3128),
    "GO": (-16.6869, -49.2648), "MA": (-2.5307, -44.3068),
    "MG": (-19.9167, -43.9345), "MS": (-20.4697, -54.6201),
    "MT": (-15.6014, -56.0979), "PA": (-1.4558, -48.5044),
    "PB": (-7.1195, -34.8450), "PE": (-8.0476, -34.8770),
    "PI": (-5.0892, -42.8019), "PR": (-25.4284, -49.2733),
    "RJ": (-22.9068, -43.1729), "RN": (-5.7945, -35.2110),
    "RO": (-8.7612, -63.9004), "RR": (2.8235, -60.6758),
    "RS": (-30.0346, -51.2177), "SC": (-27.5945, -48.5477),
    "SE": (-10.9472, -37.0731), "SP": (-23.5505, -46.6333),
    "TO": (-10.1849, -48.3336),
}
