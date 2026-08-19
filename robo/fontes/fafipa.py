# -*- coding: utf-8 -*-
"""
Fonte: Fundação FAFIPA — banca organizadora.

https://www.fundacaofafipa.org.br/

Rendimento medido (2026-08-18): **8 de 22** concursos ativos têm cargo
contábil — muito acima do IBGP (1 em 17). E 6 desses 8 NÃO vinham do
PCI, ou seja, é descoberta nova, não só enriquecimento.

Por que rende tanto: a Fafipa atende prefeituras do interior (PR, SC,
MG), e concurso municipal quase sempre inclui vaga de contador.

A página de cada concurso traz o que precisamos sem adivinhação:
  · tabela "Vagas" com cargo e quantidade — confirma o cargo contábil
  · bloco "Editais" com o PDF de abertura
  · texto do edital com órgão, data da prova e período de inscrição

ATENÇÃO à codificação: o site serve **iso-8859-1**. Forçar utf-8
transformava "Fundação" em "Funda??o" — o `http_util` agora respeita o
charset declarado.
"""

import html
import re

from http_util import buscar

HOME = "https://www.fundacaofafipa.org.br/"
CONCURSO = "https://www.fundacaofafipa.org.br/informacoes/{id}/"

TAG = re.compile(r"<[^>]+>")

# Linha da tabela de vagas: "Contador Cadastro de Reserva" ou
# "Contador 2 + Cadastro de Reserva".
CARGO_VAGA = re.compile(
    r"\b((?:t[ée]cnico\s+(?:em|de)\s+contabilidade"
    r"|analista\s+cont[áa]b\w*"
    r"|auditor[\w\s]{0,20}cont[áa]b\w*"
    r"|contador(?:a)?))\s+"
    r"((?:\d{1,3}\s*\+\s*)?(?:cadastro\s+de\s+reserva|\d{1,3}))",
    re.I,
)

ORGAO = re.compile(
    r"(?:Munic[íi]pio|Prefeitura(?:\s+Municipal)?|C[âa]mara(?:\s+Municipal)?"
    r"|Cons[óo]rcio)\s+(?:Municipal\s+)?(?:d[aeo]s?\s+)?"
    r"([A-ZÀ-Ú][\wÀ-ú']*(?:\s+(?:d[aeo]s?\s+)?[A-ZÀ-Ú][\wÀ-ú']*){0,4})",
)

UF_TXT = re.compile(
    r"Estado\s+d[aeo]s?\s+([A-ZÀ-Ú][\wÀ-ú]+(?:\s+[A-ZÀ-Ú][\wÀ-ú]+){0,2})", re.I
)

INSCRICAO = re.compile(
    r"inscri[çc][õo]es?[^.]{0,120}?(\d{2}/\d{2}/\d{4})[^.]{0,60}?(\d{2}/\d{2}/\d{4})",
    re.I | re.S,
)
PROVA = re.compile(
    r"aplica[çc][ãa]o\s+da\s+prova[^:]{0,40}:\s*(\d{2}/\d{2}/\d{4})", re.I
)
SALARIO = re.compile(r"R\$\s*([\d]{1,3}(?:\.\d{3})*,\d{2})")

# O PDF de abertura, entre os vários anexos publicados.
PDF = re.compile(r'href="(https?://[^"]+\.pdf[^"]*)"', re.I)
ABERTURA = re.compile(r"edital\s+de\s+abertura|abertura\s+n", re.I)

UF_POR_NOME = {
    "paraná": "PR", "parana": "PR", "santa catarina": "SC",
    "minas gerais": "MG", "são paulo": "SP", "sao paulo": "SP",
    "mato grosso do sul": "MS", "mato grosso": "MT", "goiás": "GO",
    "goias": "GO", "rio grande do sul": "RS", "bahia": "BA",
    "espírito santo": "ES", "espirito santo": "ES", "rondônia": "RO",
    "rondonia": "RO", "pará": "PA", "para": "PA", "tocantins": "TO",
}


def _texto(bruto: str) -> str:
    return re.sub(r"\s+", " ", TAG.sub(" ", html.unescape(bruto))).strip()


def _iso(br: str) -> str:
    d, m, a = br.split("/")
    return f"{a}-{m}-{d}"


def _pdf_abertura(bruto: str) -> str:
    """PDF do edital de ABERTURA. Os anexos vêm em blocos rotulados; o de
    abertura é o que descreve o concurso inteiro. Retificação sozinha não
    serve, porque só lista o que mudou."""
    # Procura o link cujo texto âncora fale em abertura.
    for m in re.finditer(r'<a[^>]+href="([^"]+\.pdf[^"]*)"[^>]*>(.*?)</a>',
                         bruto, re.I | re.S):
        if ABERTURA.search(_texto(m.group(2))):
            return m.group(1)
    pdfs = PDF.findall(bruto)
    return pdfs[0] if pdfs else ""


def coletar(_limite: int = 0) -> list[dict]:
    home = buscar(HOME)
    if not home:
        print("    site indisponível")
        return []

    ids = list(dict.fromkeys(re.findall(r"/informacoes/(\d+)/", home)))
    print(f"    {len(ids)} concursos no catálogo")

    achados: list[dict] = []
    for cid in ids:
        url = CONCURSO.format(id=cid)
        bruto = buscar(url)
        if not bruto:
            continue

        texto = _texto(bruto)
        m_cargo = CARGO_VAGA.search(texto)
        if not m_cargo:
            continue

        cargo = re.sub(r"\s+", " ", m_cargo.group(1)).strip().title()
        vagas = re.sub(r"\s+", " ", m_cargo.group(2)).strip()
        # "Cadastro de Reserva" -> "CR" ; "2 + Cadastro de Reserva" -> "2 + CR"
        vagas = re.sub(r"cadastro\s+de\s+reserva", "CR", vagas, flags=re.I)

        m_org = ORGAO.search(texto)
        orgao = re.sub(r"\s+", " ", m_org.group(0)).strip() if m_org else ""
        if not orgao:
            continue

        uf = ""
        m_uf = UF_TXT.search(texto)
        if m_uf:
            uf = UF_POR_NOME.get(m_uf.group(1).strip().lower(), "")
        if not uf:
            m2 = re.search(r"[-–]\s*([A-Z]{2})\b", texto[:2000])
            uf = m2.group(1) if m2 else ""

        inicio = fim = ""
        m_ins = INSCRICAO.search(texto)
        if m_ins:
            try:
                inicio, fim = _iso(m_ins.group(1)), _iso(m_ins.group(2))
            except ValueError:
                pass

        prova = ""
        m_pr = PROVA.search(texto)
        if m_pr:
            try:
                prova = _iso(m_pr.group(1))
            except ValueError:
                pass

        salario = 0.0
        valores = []
        for v in SALARIO.findall(texto):
            try:
                n = float(v.replace(".", "").replace(",", "."))
                if 1_000 <= n <= 100_000:
                    valores.append(n)
            except ValueError:
                continue
        if valores:
            salario = max(valores)

        achados.append({
            "fonte": "Fundação FAFIPA",
            "fonte_tipo": "fafipa",
            "titulo": orgao,
            "orgao_bruto": orgao,
            "texto": texto[:4000],
            # Banca legítima: pode receber o visitante.
            "url": "",
            "_procedencia": url,
            "_site_inscricao": url,
            "_pdf_edital": _pdf_abertura(bruto),
            "_cargo": cargo,
            "_vagas": vagas,
            "_uf": uf,
            "_salario": salario,
            "_inscricao_inicio": inicio,
            "_inscricao_fim": fim,
            "_data_prova": prova,
            "_esfera": "municipal",
            "_banca": "FAFIPA",
            "_confianca": "alta" if (fim and salario) else "media",
        })
        print(f"      {orgao[:44]:44} {cargo[:22]}")

    return achados
