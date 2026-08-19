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


# Esfera pelo TIPO de órgão. Ordem importa: "Universidade Federal" tem
# que bater em federal antes de qualquer outra regra, e "Câmara
# Municipal" em municipal — sem isso saíam 18 classificações erradas
# (câmara municipal como estadual, universidade federal como estadual).
_ESFERA_FEDERAL = re.compile(
    r"TRF|TRT|TRE|STJ|STF|TCU|AGU|MPU"
    r"|universidade\s+federal|instituto\s+federal|UF[A-Z]{2,3}|IF[A-Z]{2,3}"
    r"|c[âa]mara\s+dos\s+deputados|senado|receita\s+federal|INSS"
    r"|conselho\s+federal|minist[ée]rio\s+p[úu]blico\s+federal",
    re.I,
)
_ESFERA_MUNICIPAL = re.compile(
    r"prefeitura|c[âa]mara(?!\s+dos\s+deputados)|munic[íi]pio|municipal"
    r"|IPREM|prev|cons[óo]rcio\s+intermunicipal"
    r"|servi[çc]o\s+aut[ôo]nomo|SAAE|DAAE",
    re.I,
)
_ESFERA_ESTADUAL = re.compile(
    r"TCE|TJ[- ]?[A-Z]{2}|governo\s+do\s+estado"
    r"|secretaria\s+de\s+estado|SEFAZ|DETRAN"
    r"|assembleia\s+legislativa|pol[íi]cia\s+(?:civil|militar)"
    r"|AGEPAR|universidade\s+estadual",
    re.I,
)


def extrair_esfera(orgao: str, texto: str) -> str:
    alvo = f"{orgao} {texto[:600]}"
    if _ESFERA_FEDERAL.search(alvo):
        return "federal"
    if _ESFERA_MUNICIPAL.search(alvo):
        return "municipal"
    if _ESFERA_ESTADUAL.search(alvo):
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
# Detalhes para a página do edital
# ------------------------------------------------------------------
# A matéria de origem traz informação que o card não comporta: etapas do
# certame, taxa por escolaridade, validade, requisitos. Extraímos o que
# dá para afirmar com âncora textual — o resto fica de fora, porque a
# página do edital é onde o candidato decide investir meses de estudo.

_ETAPAS = re.compile(
    r"(provas?\s+(?:objetivas?|pr[áa]ticas?|discursivas?|de\s+t[íi]tulos)"
    r"|avalia[çc][ãa]o\s+(?:de\s+t[íi]tulos|psicol[óo]gica|f[íi]sica)"
    r"|exame\s+(?:m[ée]dico|psicot[ée]cnico)"
    r"|teste\s+de\s+aptid[ãa]o(?:\s+f[íi]sica)?"
    r"|prova\s+de\s+t[íi]tulos"
    r"|investiga[çc][ãa]o\s+social"
    r"|curso\s+de\s+forma[çc][ãa]o)",
    re.I,
)

_TAXA = re.compile(
    r"taxa[s]?\s+de\s+inscri[çc][ãa]o[^.]{0,180}?"
    r"(R\$\s*[\d.]+(?:,\d{2})?(?:[^.]{0,120}?R\$\s*[\d.]+(?:,\d{2})?)*)",
    re.I | re.S,
)

_VALIDADE = re.compile(
    r"validade[^.]{0,60}?(\d{1,2})\s*\(?\w*\)?\s*(ano|anos|meses)"
    r"|v[áa]lido\s+por\s+(\d{1,2})\s*\(?\w*\)?\s*(ano|anos|meses)",
    re.I,
)

_DATA_PROVA = re.compile(
    r"(?:provas?|aplica[çc][ãa]o)[^.]{0,120}?"
    r"(?:no\s+dia\s+|em\s+|para\s+)"
    r"(\d{1,2}\s+de\s+[a-zç]+(?:\s+de\s+\d{4})?|\d{1,2}/\d{1,2}/\d{4})",
    re.I,
)

_ISENCAO = re.compile(
    r"isen[çc][ãa]o[^.]{0,200}", re.I,
)


def _frase(texto: str, padrao, limite: int = 300) -> str:
    """Devolve a frase inteira onde o padrão aparece — mais útil ao leitor
    que um fragmento cortado no meio."""
    m = padrao.search(texto)
    if not m:
        return ""
    ini = texto.rfind(".", 0, m.start()) + 1
    fim = texto.find(".", m.end())
    if fim == -1:
        fim = min(len(texto), m.end() + 160)
    return re.sub(r"\s+", " ", texto[ini:fim + 1]).strip()[:limite]


def extrair_detalhes(texto: str) -> dict:
    """Campos extras para a página do edital. Só o que tem âncora clara."""
    det = {}

    etapas = []
    for m in _ETAPAS.finditer(texto):
        e = re.sub(r"\s+", " ", m.group(1)).strip().lower()
        e = e[0].upper() + e[1:]
        if e not in etapas:
            etapas.append(e)
    if etapas:
        det["etapas"] = etapas[:6]

    taxa = _frase(texto, _TAXA)
    if taxa:
        det["taxaTexto"] = taxa

    val = _frase(texto, _VALIDADE, 200)
    if val:
        det["validade"] = val

    isen = _frase(texto, _ISENCAO, 260)
    if isen:
        det["isencao"] = isen

    m = _DATA_PROVA.search(texto)
    if m:
        det["provaTexto"] = re.sub(r"\s+", " ", m.group(0)).strip()[:160]

    return det


# ------------------------------------------------------------------
# Montagem do registro
# ------------------------------------------------------------------

# Prefixo de manchete que não faz parte do nome do órgão. Vinha
# "Concurso Prefeitura de Relvado (RS)" e o editorial gerava
# "O Concurso Prefeitura de Relvado abriu concurso público".
_PREFIXO_MANCHETE = re.compile(
    r"^(?:concurso|processo\s+seletivo|edital)\s+", re.I
)
_UF_PARENTESES = re.compile(r"\s*\([A-Z]{2}\)\s*$")


def _limpar_orgao(bruto: str, titulo: str) -> str:
    """Nome do órgão a partir do campo bruto da fonte.

    Cuidado com o último segmento: em 'Prefeitura de X/SP' ele é a UF,
    não o órgão. Descartamos segmentos que sejam só sigla de estado.
    """
    if bruto:
        partes = [p.strip() for p in bruto.split("/") if p.strip()]
        partes = [p for p in partes if p.upper() not in UFS]
        if partes:
            return _sem_prefixo(partes[-1])[:120]
    return _sem_prefixo(titulo)[:120]


def _sem_prefixo(nome: str) -> str:
    n = _PREFIXO_MANCHETE.sub("", nome.strip())
    return _UF_PARENTESES.sub("", n).strip(" -–—,")


def montar(achado: dict) -> dict:
    """Converte um achado bruto no formato que o front-end consome.

    O campo `confianca` diz ao revisor onde olhar primeiro:
      alta  — tem cargo, período de inscrição e salário
      media — falta um desses
      baixa — só sabemos que existe algo contábil publicado
    """
    texto = achado["texto"]
    orgao = _limpar_orgao(achado.get("orgao_bruto", ""), achado["titulo"])

    # Campo entregue pela fonte de forma estruturada sempre ganha do que
    # a regex infere do texto corrido. O CEBRASPE, por exemplo, dá o nome
    # oficial do cargo e o período de inscrição — inferir seria pior.
    inicio = achado.get("_inscricao_inicio") or ""
    fim = achado.get("_inscricao_fim") or ""
    if not fim:
        inicio, fim = extrair_periodo_inscricao(texto)

    salario = achado.get("_salario") or extrair_salario(texto)
    cargo = achado.get("_cargo") or extrair_cargo(achado["titulo"], texto)
    banca = achado.get("_banca") or extrair_banca(texto)
    vagas = achado.get("_vagas") or extrair_vagas(texto)
    uf = achado.get("_uf") or extrair_uf(texto, orgao)
    cidade = achado.get("_cidade", "")

    # O id precisa ser estável mesmo agora que `url` é o link interno:
    # usamos a procedência (URL de origem), que não muda entre execuções.
    id_est = id_estavel(
        achado["titulo"], orgao,
        achado.get("_procedencia") or achado.get("url", ""),
    )

    confianca = achado.get("_confianca")
    if not confianca:
        completos = sum(bool(x) for x in (cargo, fim, salario))
        confianca = "alta" if completos == 3 else "media" if completos == 2 else "baixa"

    return {
        "id": id_est,
        "orgao": orgao,
        "cargo": cargo or "Área contábil — verificar edital",
        "banca": banca,
        "uf": uf,
        "cidade": cidade,
        "vagas": vagas,
        "salario": salario or 0,
        "salarioObs": "",
        "cargaHoraria": "",
        "escolaridade": achado.get("_escolaridade") or extrair_escolaridade(texto),
        "nivel": achado.get("_esfera") or extrair_esfera(orgao, texto),
        "status": "aberto" if fim else "previsto",
        "inscricaoInicio": inicio or "",
        "inscricaoFim": fim or "",
        "dataProva": achado.get("_data_prova", ""),
        "taxaInscricao": 0,
        # Link do card aponta para a PÁGINA INTERNA do radar. O site não
        # manda visitante para agregador concorrente — quem constrói
        # audiência é a plataforma, não quem indexa.
        "editalUrl": f"edital.html?id={id_est}",
        # Onde a inscrição realmente acontece (banca organizadora ou
        # órgão). Fica vazio quando não dá para afirmar — a página
        # interna então orienta a procurar o edital oficial.
        "siteInscricao": achado.get("_site_inscricao", "") or achado.get("url", ""),
        # Link DIRETO para o PDF do edital, quando a fonte o expõe.
        # Só o CEBRASPE publica o arquivo de forma acessível; as demais
        # bancas mantêm o edital atrás do sistema de inscrição.
        "pdfEdital": achado.get("_pdf_edital", ""),
        # Origem do dado, para auditoria do revisor. Não é exibida.
        "procedencia": achado.get("_procedencia", "") or achado.get("url", ""),
        "fonte": achado["fonte"],
        "capturadoEm": datetime.now().isoformat(timespec="seconds"),
        "confianca": confianca,
        # Trecho que originou o registro — o revisor confere sem abrir o DOU.
        "_trecho": re.sub(r"\s+", " ", texto)[:300],
        # Resumo e detalhes para a página do edital: é onde o candidato
        # decide investir meses de estudo, então cabe mais contexto que
        # no card.
        "resumo": achado.get("_resumo", ""),
        "detalhes": extrair_detalhes(achado.get("_texto_longo") or texto),
    }
