# -*- coding: utf-8 -*-
"""
Extração dos campos estruturados a partir do texto bruto da publicação.

Filosofia: **campo que não dá para afirmar fica vazio.** Um salário
inventado ou uma data mal lida é pior que um campo em branco — quem lê o
site decide se vai estudar meses para um concurso com base nisso.
Tudo o que sai daqui passa por revisão humana antes de ir ao ar.
"""

import hashlib
import re
import unicodedata
from datetime import datetime

from config import BANCAS, UFS


def _sem_acento(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def id_estavel(titulo: str, orgao: str, url: str) -> str:
    """ID determinístico: a mesma publicação gera sempre o mesmo id, então
    reprocessar o mesmo dia não duplica registros."""
    base = _sem_acento(f"{titulo}|{orgao}|{url}".lower())
    return "e-" + hashlib.sha1(base.encode()).hexdigest()[:12]


# ------------------------------------------------------------------
# Campos
# ------------------------------------------------------------------

_RE_SALARIO = re.compile(
    r"R\$\s*([\d]{1,3}(?:\.\d{3})*(?:,\d{2})?)", re.I
)

def extrair_salario(texto: str) -> float | None:
    """Maior valor em reais citado — costuma ser a remuneração do cargo
    de nível superior. Ignora valores baixos, que quase sempre são taxa
    de inscrição, e altos demais, que são valor global de contrato."""
    valores = []
    for bruto in _RE_SALARIO.findall(texto):
        try:
            v = float(bruto.replace(".", "").replace(",", "."))
        except ValueError:
            continue
        if 1_000 <= v <= 100_000:
            valores.append(v)
    return max(valores) if valores else None


_RE_DATA = re.compile(r"(\d{1,2})[/\.](\d{1,2})[/\.](\d{4})")

def extrair_datas(texto: str) -> list[str]:
    """Datas no formato ISO, em ordem de aparição, descartando o inválido
    (31/02) em vez de deixar explodir."""
    saida = []
    for d, m, a in _RE_DATA.findall(texto):
        try:
            saida.append(datetime(int(a), int(m), int(d)).date().isoformat())
        except ValueError:
            continue
    return saida


def extrair_periodo_inscricao(texto: str) -> tuple[str | None, str | None]:
    """Procura a janela de inscrição perto das palavras que a anunciam.
    Sem âncora textual, não chuta: devolve (None, None)."""
    m = re.search(
        r"inscri[çc][õo]es?.{0,120}?"
        r"(\d{1,2}[/\.]\d{1,2}[/\.]\d{4})"
        r".{0,40}?(?:a|at[ée]|\-)\s*"
        r"(\d{1,2}[/\.]\d{1,2}[/\.]\d{4})",
        texto, re.I | re.S,
    )
    if not m:
        return None, None

    datas = extrair_datas(m.group(1) + " " + m.group(2))
    if len(datas) == 2:
        return datas[0], datas[1]
    return None, None


def extrair_uf(texto: str, orgao: str = "") -> str:
    """UF por sigla isolada ou por nome de estado."""
    m = re.search(r"[/\-–]\s*([A-Z]{2})\b", orgao)
    if m and m.group(1) in UFS:
        return m.group(1)

    for m in re.finditer(r"\b([A-Z]{2})\b", texto[:1500]):
        if m.group(1) in UFS:
            return m.group(1)

    nomes = {
        "acre":"AC","alagoas":"AL","amazonas":"AM","amapa":"AP","bahia":"BA",
        "ceara":"CE","distrito federal":"DF","espirito santo":"ES","goias":"GO",
        "maranhao":"MA","minas gerais":"MG","mato grosso do sul":"MS",
        "mato grosso":"MT","para":"PA","paraiba":"PB","pernambuco":"PE",
        "piaui":"PI","parana":"PR","rio de janeiro":"RJ",
        "rio grande do norte":"RN","rondonia":"RO","roraima":"RR",
        "rio grande do sul":"RS","santa catarina":"SC","sergipe":"SE",
        "sao paulo":"SP","tocantins":"TO",
    }
    plano = _sem_acento((orgao + " " + texto[:1500]).lower())
    for nome, uf in nomes.items():
        if nome in plano:
            return uf
    return ""


def extrair_banca(texto: str) -> str:
    plano = _sem_acento(texto.lower())
    for chave, canonico in BANCAS.items():
        if _sem_acento(chave) in plano:
            return canonico
    return ""


def extrair_vagas(texto: str) -> str:
    m = re.search(
        r"(\d{1,4})\s*(?:\(\w+\)\s*)?vagas?", texto, re.I
    )
    if not m:
        return ""
    vagas = m.group(1)
    if re.search(r"cadastro\s+de\s+reserva|\bCR\b", texto, re.I):
        return f"{vagas} + CR"
    return vagas


def extrair_esfera(orgao: str, texto: str) -> str:
    plano = _sem_acento((orgao + " " + texto[:800]).lower())
    if re.search(r"prefeitura|municip|camara municipal", plano):
        return "municipal"
    if re.search(r"governo do estado|secretaria de estado|estadual|tribunal de justica", plano):
        return "estadual"
    return "federal"


def extrair_escolaridade(texto: str) -> str:
    plano = _sem_acento(texto.lower())
    if re.search(r"nivel superior|ensino superior|bacharel|ciencias contabeis", plano):
        return "superior"
    if re.search(r"nivel medio|ensino medio|tecnico em contabilidade", plano):
        return "medio"
    return "superior"


def extrair_cargo(titulo: str, texto: str) -> str:
    """Nome do cargo, quando aparece de forma reconhecível."""
    m = re.search(
        r"\b(t[ée]cnico\s+(?:em|de)\s+contabilidade"
        r"|auditor[\w\s\-]{0,40}?(?:fiscal|controle externo|interno)"
        r"|anal(?:ista)[\w\s\-]{0,40}?cont[áa]b\w*"
        r"|contador\w*)",
        titulo + " " + texto, re.I,
    )
    if m:
        cargo = re.sub(r"\s+", " ", m.group(1)).strip()
        return cargo[:70].title()
    return ""


# ------------------------------------------------------------------
# Montagem do registro
# ------------------------------------------------------------------

def _limpar_orgao(bruto: str, titulo: str) -> str:
    """Nome do órgão a partir do campo bruto da fonte.

    Cuidado com o último segmento: em 'Prefeitura de X/SP' ele é a UF,
    não o órgão. Descartamos segmentos que sejam só sigla de estado.
    """
    if bruto:
        partes = [p.strip() for p in bruto.split("/") if p.strip()]
        partes = [p for p in partes if p.upper() not in UFS]
        if partes:
            return partes[-1][:120]
    return titulo[:120]


def montar(achado: dict) -> dict:
    """Converte um achado bruto no formato que o front-end consome.

    O campo `confianca` diz ao revisor onde olhar primeiro:
      alta  — tem cargo, período de inscrição e salário
      media — falta um desses
      baixa — só sabemos que existe algo contábil publicado
    """
    texto = achado["texto"]
    orgao = _limpar_orgao(achado.get("orgao_bruto", ""), achado["titulo"])

    inicio, fim = extrair_periodo_inscricao(texto)
    salario = extrair_salario(texto)
    cargo = extrair_cargo(achado["titulo"], texto)

    # Quando a fonte já entrega município e UF de forma estruturada
    # (caso do Querido Diário), confiamos nela em vez de adivinhar no texto.
    uf = achado.get("_uf") or extrair_uf(texto, orgao)
    cidade = achado.get("_cidade", "")

    completos = sum(bool(x) for x in (cargo, fim, salario))
    confianca = "alta" if completos == 3 else "media" if completos == 2 else "baixa"

    return {
        "id": id_estavel(achado["titulo"], orgao, achado["url"]),
        "orgao": orgao,
        "cargo": cargo or "Área contábil — verificar edital",
        "banca": extrair_banca(texto),
        "uf": uf,
        "cidade": cidade,
        "vagas": extrair_vagas(texto),
        "salario": salario or 0,
        "salarioObs": "",
        "cargaHoraria": "",
        "escolaridade": extrair_escolaridade(texto),
        "nivel": extrair_esfera(orgao, texto),
        "status": "aberto" if fim else "previsto",
        "inscricaoInicio": inicio or "",
        "inscricaoFim": fim or "",
        "dataProva": "",
        "taxaInscricao": 0,
        "editalUrl": achado["url"],
        "fonte": achado["fonte"],
        "capturadoEm": datetime.now().isoformat(timespec="seconds"),
        "confianca": confianca,
        # Trecho que originou o registro — o revisor confere sem abrir o DOU.
        "_trecho": re.sub(r"\s+", " ", texto)[:300],
    }
