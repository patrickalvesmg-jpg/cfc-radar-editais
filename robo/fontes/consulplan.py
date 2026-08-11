# -*- coding: utf-8 -*-
"""
Fonte: Instituto Consulplan.

Relevante por dois motivos:

1. É a banca dos **Conselhos de Contabilidade** — CRC-CE, CRC-RJ e o
   próprio CFC (Exame de Qualificação Técnica). Nenhuma outra fonte
   cobre isso, e é exatamente o público da CFC Academy.
2. Aplica muitos concursos de **prefeitura**, que é o que os diários
   municipais não entregam de forma pesquisável.

A listagem é HTML servido pelo servidor (não React), então lemos direto
sem navegador. O site não expõe robots.txt (404) — na ausência de regra,
seguimos as boas práticas do http_util: identificação e pausa.

LIMITE CONHECIDO: a listagem traz o ÓRGÃO, não o cargo. O cargo está
dentro do PDF do edital. Portanto os registros daqui nascem com
`confianca: baixa` e cargo genérico — cabe ao revisor abrir o edital e
completar. Preferimos isso a inventar um cargo que não podemos afirmar.
"""

import re

from http_util import buscar

LISTAGEM = "https://www.institutoconsulplan.org.br/concursos"

# Cartão de concurso na listagem.
CARTAO = re.compile(
    r'<div class="card custom-card.*?</div>\s*</div>\s*</div>', re.S | re.I
)
TAG = re.compile(r"<[^>]+>")
LINK = re.compile(r'href="(https://www\.institutoconsulplan\.org\.br/[^"]+)"', re.I)

# "Inscreva-se" só aparece enquanto a inscrição está aberta; encerrada,
# vira "Acompanhamento de Inscrição". É o sinal de que o concurso é
# oportunidade e não histórico.
ABERTO = re.compile(r"inscreva-?se", re.I)

# Órgão de interesse direto do público contábil.
ORGAO_CONTABIL = re.compile(
    r"conselho\s+(?:regional|federal)\s+de\s+contabilidade"
    r"|\bCRC\s*[/-]?\s*[A-Z]{2}\b"
    r"|\bCRC[A-Z]{2}\b"
    r"|\bCFC\b"
    r"|exame\s+de\s+qualifica[çc][ãa]o\s+t[ée]cnica",
    re.I,
)

UF_NO_NOME = re.compile(r"[/-]\s*([A-Z]{2})\b")


def _texto(html: str) -> str:
    return re.sub(r"\s+", " ", TAG.sub(" ", html)).strip()


def coletar(_limite: int = 0) -> list[dict]:
    html = buscar(LISTAGEM)
    if not html:
        print("    listagem indisponível")
        return []

    cartoes = CARTAO.findall(html)
    print(f"    {len(cartoes)} concursos na listagem")

    achados: list[dict] = []
    vistos: set[str] = set()

    for bruto in cartoes:
        texto = _texto(bruto)
        if not texto or not ABERTO.search(texto):
            continue                      # inscrição encerrada

        # Só entram órgãos contábeis. Prefeitura genérica não serve:
        # sem o cargo, publicaríamos "Prefeitura X — verificar edital",
        # que não ajuda ninguém a decidir se vale se inscrever.
        if not ORGAO_CONTABIL.search(texto):
            continue

        m = LINK.search(bruto)
        url = m.group(1) if m else LISTAGEM

        orgao = re.split(r"\s*(?:Concurso P[úu]blico|Processo Seletivo|Edital)",
                         texto, maxsplit=1)[0].strip()
        if not orgao or orgao in vistos:
            continue
        vistos.add(orgao)

        uf_m = UF_NO_NOME.search(orgao)
        uf = uf_m.group(1) if uf_m else ""

        achados.append({
            "fonte": "Instituto Consulplan",
            "fonte_tipo": "consulplan",
            "titulo": orgao,
            "orgao_bruto": orgao,
            "texto": texto[:2000],
            "url": url,
            "publicado_em": "",
            "_banca": "Consulplan",
            "_uf": uf,
            "_esfera": "federal",
            # Cargo e prazo estão no PDF: não afirmamos o que não lemos.
            "_confianca": "baixa",
        })
        print(f"      {orgao[:64]}")

    return achados
