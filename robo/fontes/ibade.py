# -*- coding: utf-8 -*-
"""
Fonte: IBADE — banca organizadora, via portal de seleção.

https://portal.ibade.selecao.site/edital

## Por que esta fonte importa

O IBADE atende prefeituras de **Rondônia, Espírito Santo, Acre e Mato
Grosso** — exatamente os estados onde o radar é mais fraco. Medição de
20/08/2026: ES e AC tinham ZERO editais no acervo; RO tinha 2.

E não há sobreposição: "IBADE" não aparecia em nenhum dos 124 editais
capturados. É descoberta nova, não enriquecimento do que o PCI já traz.

## Por que ela não foi achada antes

As sondagens anteriores bateram em `ibade.org.br`, o site institucional
— cuja rota `/concursos` é um arquivo de certames PASSADOS. O catálogo
vivo mora no subdomínio da plataforma (`portal.ibade.selecao.site`).
Site institucional e portal de inscrição são coisas diferentes; vale
testar os dois ao sondar qualquer banca.

## Duas armadilhas medidas

**1. Não existe período de inscrição na página de detalhe.** As outras
fontes em plataforma comum casam duas datas com o regex `INSCRICAO`;
aqui isso não acha nada, e todo edital seria descartado em silêncio
pela trava de `if not fim`. O status vem da ABA em que o card está.

**2. A UF não está na página.** Os PDFs têm nome em hash
(`71a29ee7….pdf`) e o título não cita o estado. A UF sai do nome do
município, contra a base do IBGE — o mesmo caminho já usado para
resolver a Câmara de Seabra (ver `atualizar._uf_por_cidade`).
"""

import html
import re

from config import PADRAO_CONTABIL
from http_util import buscar

BASE = "https://portal.ibade.selecao.site"
LISTAGEM = f"{BASE}/edital"
DETALHE = BASE + "/edital/ver/{id}"

# As abas do portal. Só interessam os certames VIVOS: 'encerrados' tinha
# 96 dos 103 editais na medição, e publicá-los enganaria o candidato.
ABAS_VIVAS = ("abertos", "andamento", "futuros")

TAG = re.compile(r"<[^>]+>")
_ABA = re.compile(r'<div class="tab-pane[^"]*" id="([a-z]+)"')
_VER = re.compile(r"/edital/ver/(\d+)")

# O card da LISTAGEM traz o órgão limpo, num parágrafo próprio:
#   <p class="text-500 text-18 mb-0">PREFEITURA MUNICIPAL DE ITARANA</p>
# É de onde vale tirar o nome. Extrair do texto corrido da página de
# detalhe trazia lixo grudado ("PREFEITURA ... Acompanhar ins"), porque
# ali o nome fica encostado no menu.
_CARD = re.compile(
    r'<p class="text-500 text-18 mb-0"[^>]*>([^<]{6,90})</p>.{0,400}?'
    r"/edital/ver/(\d+)",
    re.S,
)

# "PREFEITURA MUNICIPAL DE ARIQUEMES/RO" ou "... DE ARIQUEMES"
_ORGAO = re.compile(
    r"((?:PREFEITURA|C[ÂA]MARA|MUNIC[ÍI]PIO|INSTITUTO|FUNDA[ÇC][ÃA]O|"
    r"SERVI[ÇC]O|CONS[ÓO]RCIO|AUTARQUIA)[^<\n]{4,80})",
    re.I,
)
_UF_BARRA = re.compile(r"/\s*([A-Z]{2})\b")
_PDF = re.compile(r'href="([^"]+\.pdf)"', re.I)


def _texto(bruto: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG.sub(" ", bruto))).strip()


def _por_aba(pagina: str) -> dict[str, str]:
    """Mapeia cada aba para o pedaço de HTML que lhe pertence.

    A relação aba→card não está no card: é a POSIÇÃO dele dentro do
    `<div class="tab-pane" id="...">`. Fatiamos por isso, em vez de
    olhar a ordem dos títulos, que muda com o layout do celular
    (o portal repete os títulos em blocos `d-block d-md-none`).
    """
    marcas = [(m.start(), m.group(1)) for m in _ABA.finditer(pagina)]
    blocos: dict[str, str] = {}
    for i, (pos, nome) in enumerate(marcas):
        fim = marcas[i + 1][0] if i + 1 < len(marcas) else len(pagina)
        blocos[nome] = pagina[pos:fim]
    return blocos


# Preposições ficam minúsculas no meio do nome; siglas de estado
# permanecem em caixa alta. "PREFEITURA MUNICIPAL DE BARRA DE SÃO
# FRANCISCO" vira "Prefeitura Municipal de Barra de São Francisco".
_MIUDAS = {"de", "da", "do", "das", "dos", "e"}


def _titulo(bruto: str) -> str:
    palavras = []
    for i, palavra in enumerate(bruto.split()):
        baixa = palavra.lower()
        if i and baixa in _MIUDAS:
            palavras.append(baixa)
        elif len(palavra) == 2 and palavra.isupper():
            palavras.append(palavra)          # UF
        else:
            palavras.append("-".join(p.capitalize() for p in baixa.split("-")))
    return " ".join(palavras)


def _cargo_contabil(texto: str) -> str:
    """Devolve o cargo contábil citado, ou '' se não houver."""
    achado = PADRAO_CONTABIL.search(texto)
    if not achado:
        return ""
    bruto = achado.group(0).strip(" -–,;.")
    return " ".join(p.capitalize() for p in bruto.split())


def coletar(limite: int = 25) -> list[dict]:
    pagina = buscar(LISTAGEM)
    if not pagina:
        return []

    blocos = _por_aba(pagina)
    # id -> (aba, nome do órgão vindo do card)
    vivos: dict[str, tuple[str, str]] = {}
    for aba in ABAS_VIVAS:
        bloco = blocos.get(aba, "")
        for nome, ident in _CARD.findall(bloco):
            vivos[ident] = (aba, html.unescape(nome).strip())
        # Card fora do formato esperado: ainda assim não perdemos o
        # edital, só ficamos sem o nome pronto.
        for ident in _VER.findall(bloco):
            vivos.setdefault(ident, (aba, ""))

    print(f"    {len(vivos)} concursos vivos "
          f"({', '.join(f'{a}: {sum(1 for v in vivos.values() if v == a)}' for a in ABAS_VIVAS)})")

    achados: list[dict] = []
    for ident, (aba, orgao_card) in vivos.items():
        url = DETALHE.format(id=ident)
        detalhe = buscar(url)
        if not detalhe:
            continue

        texto = _texto(detalhe)
        cargo = _cargo_contabil(texto)
        if not cargo:
            continue

        # O nome do card é o bom; o do detalhe é o último recurso.
        orgao = orgao_card
        if not orgao:
            m_orgao = _ORGAO.search(texto)
            orgao = m_orgao.group(1).strip() if m_orgao else ""
        if not orgao:
            continue
        orgao = _titulo(orgao)

        m_uf = _UF_BARRA.search(orgao)
        uf = m_uf.group(1) if m_uf else ""

        m_pdf = _PDF.search(detalhe)
        pdf = m_pdf.group(1) if m_pdf else ""
        if pdf and pdf.startswith("/"):
            pdf = BASE + pdf

        achados.append({
            "fonte": "IBADE",
            "fonte_tipo": "ibade",
            "titulo": orgao,
            "orgao_bruto": orgao,
            "texto": texto[:4000],
            "url": "",
            "_procedencia": url,
            "_site_inscricao": url,
            "_pdf_edital": pdf,
            "_cargo": cargo,
            "_uf": uf,
            "_banca": "IBADE",
            # Sem período de inscrição na página, o melhor que podemos
            # afirmar é a fase. 'futuros' não abriu ainda; 'abertos' e
            # 'andamento' estão correndo.
            "_esfera": "municipal" if re.search(r"munic|prefeitura|c[âa]mara", orgao, re.I) else "",
            "_confianca": "media",
        })
        print(f"      {orgao[:46]:46} {cargo[:24]}")

    return achados
