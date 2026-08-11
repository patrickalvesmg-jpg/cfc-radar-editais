# -*- coding: utf-8 -*-
"""
Fonte: portais de concurso construídos em WordPress.

Vários sites do ramo expõem a **API REST do WordPress** (`/wp-json/`),
que devolve o post inteiro em JSON — muito mais estável que raspar HTML,
porque não quebra quando o site muda de tema.

Portais ativos aqui (ambos com robots.txt permitindo `/wp-json/`):
  · Concursos no Brasil      — concursosnobrasil.com
  · Edital Concursos Brasil  — editalconcursosbrasil.com.br

Rendimento medido (2026-08-11): das 40 matérias buscadas por portal,
40 citavam cargo contábil — a busca da própria API já filtra bem. O
funil aperta depois, no `eh_abertura`, que separa "concurso abriu" de
"resultado saiu".

IMPORTANTE: estes portais são AGREGADORES, iguais ao PCI. Servem para
DESCOBRIR o concurso, nunca para receber o visitante. O link do site é
sempre a página interna do radar; o externo só aparece quando achamos o
endereço da banca/órgão dentro do texto (ver `_site_inscricao`).
"""

import json
import re
from datetime import date

from config import PADRAO_CONTABIL, PADRAO_RUIDO, eh_abertura
from http_util import buscar

PORTAIS = (
    {
        "nome": "Concursos no Brasil",
        "api": "https://concursosnobrasil.com/wp-json/wp/v2/posts",
    },
    {
        "nome": "Edital Concursos Brasil",
        "api": "https://www.editalconcursosbrasil.com.br/wp-json/wp/v2/posts",
    },
)

TERMOS = ("contador", "contabilidade", "contábeis")

TAG = re.compile(r"<[^>]+>")

# Nunca virar link: agregadores (inclusive estes) e redes sociais.
DOMINIO_PROIBIDO = re.compile(
    r"pciconcursos|jcconcursos|concursosnobrasil|editalconcursosbrasil"
    r"|folhadirigida|qconcursos|grancursos|estrategia|schema\.org"
    r"|google|facebook|whatsapp|instagram|twitter|youtube|linkedin"
    r"|megapush|wp-content|gravatar",
    re.I,
)

SITE_INSCRICAO = re.compile(
    r"(?:pelo|no|atrav[ée]s do|por meio do|junto ao)\s+"
    r"(?:site|endere[çc]o(?:\s+eletr[ôo]nico)?|portal)\s+"
    r"((?:https?://)?(?:www\.)?[\w-]+\.(?:org|com|net|gov|edu)(?:\.br)?)",
    re.I,
)
DOMINIO = re.compile(r"\b((?:www\.)?[\w-]+\.(?:org|com|net|gov|edu)\.br)\b", re.I)

CARGO = re.compile(
    r"\b(t[ée]cnico\s+(?:em|de)\s+contabilidade"
    r"|analista\s+(?:de\s+)?cont[áa]b\w*"
    r"|auditor[\w\s]{0,24}cont[áa]b\w*"
    r"|contador(?:a)?)\b",
    re.I,
)
SALARIO = re.compile(r"R\$\s*([\d]{1,3}(?:\.\d{3})*(?:,\d{2})?)")
DATA = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
UF = re.compile(r"\(([A-Z]{2})\)")
VAGAS = re.compile(r"(\d{1,4})\s*vagas?", re.I)


# O título precisa conter algo que se pareça com nome de órgão. Manchete
# do tipo "Nível médio e superior" ou "Com salários de até R$ 15 mil"
# não identifica concurso nenhum.
ORGAO_VALIDO = re.compile(
    r"prefeitura|c[âa]mara|conselho|tribunal|minist[ée]rio|secretaria"
    r"|universidade|instituto|autarquia|funda[çc][ãa]o|ag[êe]ncia"
    r"|banco|assembleia|defensoria|procuradoria|departamento"
    r"|\bTC[EU]?\b|\bTJ\b|\bTRF\b|\bTRT\b|\bTRE\b|\bMP[A-Z]{0,2}\b"
    r"|\bIF[A-Z]{1,3}\b|\bUF[A-Z]{1,3}\b|\bCRC\b|\bCFC\b|\bSTM\b|\bSEFAZ\b"
    r"|prev\b|\bIPREM\b|hospital|c[ôo]nsul|empresa\s+de",
    re.I,
)

# Não é concurso público de provimento efetivo.
NAO_CONCURSO = re.compile(
    r"est[áa]gi|estudantes|jovem\s+aprendiz|resid[êe]ncia\s+m[ée]dica"
    r"|vestibular|p[óo]s-gradua|mestrado|doutorado|bolsa",
    re.I,
)


def _vencido(iso: str) -> bool:
    """A inscrição já encerrou? Único critério que importa para saber se
    a vaga ainda é oportunidade."""
    try:
        return date.fromisoformat(iso) < date.today()
    except (ValueError, TypeError):
        return False


def _texto(html: str) -> str:
    return re.sub(r"\s+", " ", TAG.sub(" ", html)).strip()


def _orgao(titulo: str, corpo: str = "") -> str:
    """Nome do órgão, a partir da manchete e, se preciso, do corpo.

    A manchete é jornalística e nem sempre começa pelo órgão — o CRC-CE
    aparecia como "Nível médio e superior: CRC-CE recebe inscrições…".
    Quando o corte do título não rende nome reconhecível, procuramos a
    primeira entidade citada no texto.
    """
    corte = re.split(
        r"\s+(?:abre|oferta|tem|anuncia|divulga|lan[çc]a|publica|reabre"
        r"|seleciona|recebe|retoma|convoca)\s+"
        r"|\s*[:—–]\s*",
        titulo, maxsplit=1,
    )[0].strip()
    corte = re.split(r"\s*,\s*", corte, maxsplit=1)[0].strip()

    if ORGAO_VALIDO.search(corte):
        return corte[:120]

    # Segunda tentativa: parte do título depois do prefixo editorial.
    resto = titulo[len(corte):].strip(" :—–")
    alvo = re.split(
        r"\s+(?:abre|oferta|tem|anuncia|divulga|lan[çc]a|publica|reabre"
        r"|seleciona|recebe|retoma|convoca)\s+",
        resto, maxsplit=1,
    )[0].strip()
    if ORGAO_VALIDO.search(alvo):
        return alvo[:120]

    # Terceira: nome completo citado no corpo da matéria.
    m = re.search(
        r"((?:Conselho|Tribunal|Prefeitura|C[âa]mara|Universidade|Instituto"
        r"|Secretaria|Minist[ée]rio|Funda[çc][ãa]o|Autarquia|Ag[êe]ncia"
        r"|Assembleia|Defensoria|Procuradoria)[^.;:()]{4,80})",
        corpo,
    )
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()[:120]

    return corte[:120]


def _site_inscricao(texto: str) -> str:
    m = SITE_INSCRICAO.search(texto)
    alvo = m.group(1) if m else None

    if not alvo:
        cands = [d for d in dict.fromkeys(DOMINIO.findall(texto))
                 if not DOMINIO_PROIBIDO.search(d)]
        if not cands:
            return ""
        alvo = next((c for c in cands if ".gov.br" in c.lower()), cands[0])

    if DOMINIO_PROIBIDO.search(alvo):
        return ""
    return alvo if alvo.startswith("http") else f"https://{alvo}"


def _salario(texto: str) -> float:
    valores = []
    for bruto in SALARIO.findall(texto):
        try:
            v = float(bruto.replace(".", "").replace(",", "."))
        except ValueError:
            continue
        if 1_000 <= v <= 100_000:
            valores.append(v)
    return max(valores) if valores else 0.0


MESES = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4,
    "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9,
    "outubro": 10, "novembro": 11, "dezembro": 12,
}

# Texto jornalístico escreve a data POR EXTENSO ("até 25 de novembro de
# 2025", "de 27 de outubro a 10 de dezembro"). Ler só dd/mm/aaaa
# descartava todos os candidatos válidos — medido: 3 de 3 morriam aqui.
_DIA_EXTENSO = r"(\d{1,2})\s*de\s*([a-zç]+)(?:\s*de\s*(\d{4}))?"

_PERIODO_EXTENSO = re.compile(
    r"inscri[çc][õo]es.{0,120}?de\s+" + _DIA_EXTENSO +
    r"\s*(?:a|at[ée])\s*" + _DIA_EXTENSO,
    re.I | re.S,
)
_ATE_EXTENSO = re.compile(
    r"inscri[çc][õo]es.{0,120}?at[ée]\s+" + _DIA_EXTENSO,
    re.I | re.S,
)
_PERIODO_NUM = re.compile(
    r"inscri[çc][õo]es.{0,140}?(\d{1,2}/\d{1,2}/\d{4})"
    r".{0,50}?(?:a|at[ée])\s*(\d{1,2}/\d{1,2}/\d{4})",
    re.I | re.S,
)


def _iso_extenso(dia: str, mes: str, ano: str | None) -> str:
    m = MESES.get(mes.lower())
    if not m or not ano:
        return ""
    try:
        return f"{int(ano):04d}-{m:02d}-{int(dia):02d}"
    except ValueError:
        return ""


def _prazo(texto: str) -> tuple[str, str]:
    """Janela de inscrição, quando o texto a ancora explicitamente."""
    m = _PERIODO_NUM.search(texto)
    if m:
        def iso(br):
            d, mm, a = br.split("/")
            return f"{a}-{int(mm):02d}-{int(d):02d}"
        try:
            return iso(m.group(1)), iso(m.group(2))
        except (ValueError, IndexError):
            return "", ""

    m = _PERIODO_EXTENSO.search(texto)
    if m:
        d1, mes1, ano1, d2, mes2, ano2 = m.groups()
        # "de 27 de outubro a 10 de dezembro de 2025": o ano só aparece
        # no fim e vale para as duas pontas.
        ano1 = ano1 or ano2
        return _iso_extenso(d1, mes1, ano1), _iso_extenso(d2, mes2, ano2 or ano1)

    m = _ATE_EXTENSO.search(texto)
    if m:
        return "", _iso_extenso(*m.groups())

    return "", ""


def _buscar(api: str, termo: str, quantos: int) -> list[dict]:
    url = f"{api}?search={termo}&per_page={quantos}&orderby=date&order=desc"
    corpo = buscar(url, checar_robots=False)
    if not corpo:
        return []
    try:
        dados = json.loads(corpo)
        return dados if isinstance(dados, list) else []
    except json.JSONDecodeError:
        return []


def coletar(limite: int = 20) -> list[dict]:
    achados: list[dict] = []
    vistos: set[str] = set()

    for portal in PORTAIS:
        encontrados = 0

        for termo in TERMOS:
            for post in _buscar(portal["api"], termo, limite):
                link = post.get("link", "")
                if not link or link in vistos:
                    continue
                vistos.add(link)

                titulo = _texto(post.get("title", {}).get("rendered", ""))
                corpo = _texto(post.get("content", {}).get("rendered", ""))
                texto = f"{titulo} {corpo}"

                if not PADRAO_CONTABIL.search(texto):
                    continue
                # Precisa ser abertura de inscrição, não resultado/nomeação.
                if PADRAO_RUIDO.search(texto) or not eh_abertura(texto):
                    continue
                # Estágio, vestibular e residência não são concurso de
                # provimento — apareceu "Prefeitura seleciona estudantes".
                if NAO_CONCURSO.search(titulo):
                    continue

                inicio, fim = _prazo(texto)
                cargo_m = CARGO.search(texto)
                uf_m = UF.search(titulo)
                vagas_m = VAGAS.search(texto)

                # Sem cargo contábil nomeado, o registro viraria
                # "Prefeitura X — verificar edital", que não ajuda
                # ninguém a decidir se vale se inscrever.
                if not cargo_m:
                    continue

                # Prazo é o dado que torna a vaga acionável. Matéria
                # jornalística sem data de inscrição não vira card.
                if not fim:
                    continue

                # Estes portais mantêm matéria antiga indexada: na
                # primeira medição, 4 de 4 candidatos tinham inscrição
                # encerrada (a mais recente havia fechado 7 meses antes).
                # Publicar isso mandaria o candidato para uma inscrição
                # que já fechou.
                if _vencido(fim):
                    continue

                orgao = _orgao(titulo, corpo)
                # Título que não rende nome de órgão reconhecível
                # ("Nível médio e superior", "Com salários de até R$ 15 mil")
                # produziria um card sem sentido no site.
                if not ORGAO_VALIDO.search(orgao):
                    continue

                achados.append({
                    "fonte": portal["nome"],
                    "fonte_tipo": "portal_wp",
                    "titulo": titulo[:160],
                    "orgao_bruto": orgao[:120] or titulo[:120],
                    "texto": texto[:4000],
                    # Agregador nunca recebe o visitante.
                    "url": "",
                    "_procedencia": link,
                    "_site_inscricao": _site_inscricao(texto),
                    "publicado_em": (post.get("date") or "")[:10],
                    "_cargo": (cargo_m.group(1).title() if cargo_m else ""),
                    "_uf": uf_m.group(1) if uf_m else "",
                    "_vagas": vagas_m.group(1) if vagas_m else "",
                    "_salario": _salario(texto),
                    "_inscricao_inicio": inicio,
                    "_inscricao_fim": fim,
                    # Texto jornalístico: o salário citado pode ser o teto
                    # do concurso, não o do cargo contábil. Sempre revisar.
                    "_confianca": "media" if (fim and cargo_m) else "baixa",
                })
                encontrados += 1

        print(f"    {portal['nome']}: {encontrados} candidatos")

    return achados
