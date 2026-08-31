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
from datetime import date, timedelta

from config import eh_abertura, eh_relevante
from http_util import buscar

# ATENÇÃO — FORA DO AR desde pelo menos 31/08/2026.
#
# O host `api.queridodiario.ok.org.br` devolve **404 em tudo**, não só
# nas nossas consultas: a raiz `/` e o `/docs` também. Não é o filtro
# nem o formato da query — a API saiu do ar ou mudou de endereço, e o
# endereço novo não é nenhuma das variações óbvias (`/gazettes`,
# `/api/v1/gazettes`, `backend.`). O site `queridodiario.ok.org.br`
# continua no ar e responde HTML.
#
# Efeito hoje: as 8 consultas falham e a fonte devolve 0. A varredura
# NÃO quebra (falha de fonte é tolerada de propósito), mas o log enche
# de 404 e o rendimento é zero.
#
# Antes de consertar, vale lembrar o que já sabíamos: esta fonte já
# rendia pouco (ver o bloco abaixo e o README). Reativar só compensa se
# a API nova indexar a tabela de cargos — que era o problema real.
API = "https://api.queridodiario.ok.org.br/api/gazettes"

# Janela de validade. Inscrição de concurso municipal costuma durar
# semanas; publicação com mais que isto quase certamente já encerrou.
DIAS_VALIDADE = 120


def _antigo(iso: str) -> bool:
    if not iso:
        return False
    try:
        return (date.today() - date.fromisoformat(iso[:10])).days > DIAS_VALIDADE
    except ValueError:
        return False

# ------------------------------------------------------------------
# O QUE ESTA FONTE RENDE, NA PRÁTICA (medido em 2026-08-10)
# ------------------------------------------------------------------
# Esta fonte tem rendimento BAIXO para concurso contábil, e o motivo não
# é o filtro. Foi investigado a fundo:
#
# 1. A API **não suporta booleano**. `"a" AND b` vira busca livre pelos
#    termos soltos: de 40 resultados, 27 falavam de concurso e só 1
#    citava contador.
#
# 2. Os `excerpts` trazem um trecho ARBITRÁRIO do diário — cláusula de
#    fotocópia, referência a lei — quase nunca a tabela de cargos. Como
#    o filtro lê o trecho, ele descarta editais válidos.
#
# 3. Baixando o TEXTO COMPLETO de 20 editais de abertura recentes
#    (média de 112 mil caracteres), **nenhum** tinha vaga contábil. Os 4
#    que citavam "contabilidade" eram listas de classificação de certame
#    já encerrado — corretamente barrados.
#
# Conclusão: concurso municipal para contador é raro, e quando sai vem
# num PDF de edital cuja tabela de cargos a API não indexa de forma
# pesquisável. Mantemos a fonte porque o custo é baixo e um dia ela
# acerta; mas o volume do site NÃO virá daqui — virá das bancas, que
# publicam cargo, vaga e salário estruturados (ver fontes/cebraspe.py).
#
# Consultas por FRASE EXATA (a única forma que funciona nesta API):
CONSULTAS = (
    '"provimento do cargo de contador"',
    '"para o cargo de contador"',
    '"cargo de contador"',
    '"analista contábil"',
    '"técnico em contabilidade"',
    '"cargo de técnico em contabilidade"',
    '"ciências contábeis"',
    '"contador" "concurso público"',
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

            # Precisa ser abertura de inscrição, não menção a concurso.
            if not eh_abertura(texto):
                continue

            # Diário antigo não é oportunidade. Um edital publicado há
            # mais de 4 meses já encerrou a inscrição — exibi-lo como
            # aberto faria o candidato perder tempo.
            if _antigo(it.get("date", "")):
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
