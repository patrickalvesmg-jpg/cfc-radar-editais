# -*- coding: utf-8 -*-
"""
Fonte: CEBRASPE (ex-CESPE).

Usa a API que o próprio site consome (`apis.cebraspe.org.br`). O
robots.txt do portal traz `Disallow:` vazio — ou seja, permite acesso.

Vantagem sobre raspar diário oficial: os dados já vêm estruturados
(vagas, salário, período de inscrição e **lista de cargos**), então
identificamos o cargo contábil com precisão em vez de inferir do texto.

Fluxo:
  1. lista os eventos por fase (Novos / Inscrições Abertas / …)
  2. para cada evento ativo, busca o detalhe
  3. procura cargo contábil em `eventoCargos[].area`

Por que outras bancas não estão aqui:
  FCC    — robots.txt proíbe /concursos/, justamente a área necessária
  VUNESP — responde 403 até no robots.txt (bloqueia automação)
  IBFC   — idem
Incluí-las exigiria contornar bloqueio explícito, o que não fazemos.
"""

import json
import re
import time

from config import UFS as UFS_VALIDAS
from http_util import buscar

LISTA = "https://apis.cebraspe.org.br/cebraspe/eventos/tipo/concursos/"
DETALHE = "https://apis.cebraspe.org.br/cebraspe/eventos/{url}/"
PAGINA = "https://www.cebraspe.org.br/concursos/{url}"

# Só interessa o que ainda dá para se inscrever ou está por abrir.
FASES_ATIVAS = ("Novos", "Inscrições Abertas")

# Aqui o filtro é estreito de propósito: o campo `area` é o nome oficial
# do cargo, então não há o ruído de texto corrido que exige as três
# camadas do config.py.
CARGO_CONTABIL = re.compile(
    r"cont[áa]bil|contabilidade|contador|ci[êe]ncias cont", re.I
)

# "De 17/07/2026 até 21/08/2026 às 18:00, horário oficial de Brasília/DF"
PERIODO = re.compile(
    r"de\s+(\d{2}/\d{2}/\d{4}).{0,12}?at[ée]\s+(\d{2}/\d{2}/\d{4})", re.I | re.S
)


def _json(url: str):
    # API pública destinada a consumo programático.
    corpo = buscar(url, checar_robots=False)
    if not corpo:
        return None
    try:
        return json.loads(corpo)
    except json.JSONDecodeError:
        return None


def _iso(br: str) -> str:
    d, m, a = br.split("/")
    return f"{a}-{m}-{d}"


def _periodo(texto: str | None) -> tuple[str, str]:
    if not texto:
        return "", ""
    m = PERIODO.search(texto)
    if not m:
        return "", ""
    try:
        return _iso(m.group(1)), _iso(m.group(2))
    except ValueError:
        return "", ""


def _orgao_e_uf(nome: str) -> tuple[str, str]:
    """'TCE MA 26' → ('TCE MA', 'MA'). O nome do CEBRASPE é uma sigla com
    UF e ano; tiramos o ano e isolamos a UF. Expandir a sigla para o nome
    completo do órgão é trabalho do revisor — inventar aqui seria pior
    que deixar a sigla, que ao menos é verificável no link."""
    limpo = re.sub(r"\s*\b(19|20)\d{2}\b\s*$", "", nome.strip())
    limpo = re.sub(r"\s+\d{2}\s*$", "", limpo).strip()

    m = re.search(r"\b([A-Z]{2})\b", limpo)
    uf = m.group(1) if m and m.group(1) in UFS_VALIDAS else ""
    return limpo, uf


def _esfera(nome: str, uf: str) -> str:
    """Esfera pelo tipo de órgão na sigla. Sem isto tudo cai em 'federal',
    que é o padrão do extrator genérico e estaria errado na maioria."""
    n = nome.upper()
    if re.search(r"\bPREF\b|PREFEITURA|C[ÂA]MARA MUNICIPAL|\bCM\b", n):
        return "municipal"
    if re.search(r"\bTCE\b|\bTJ\b|\bPC\b|\bPM\b|\bSEAP\b|\bSESAU\b|\bSEFAZ\b"
                 r"|\bALE?\b|AGEPAR|PROCON|\bARS\b|PERICIA|\bDETRAN\b|\bIPE\b", n):
        return "estadual"
    if re.search(r"\bTRF\b|\bTRT\b|\bTRE\b|\bSTJ\b|\bSTF\b|\bTCU\b|\bAGU\b"
                 r"|\bMPU\b|\bUF[A-Z]{1,3}\b|\bIF[A-Z]{1,3}\b|C[ÂA]MARA DOS DEPUTADOS"
                 r"|\bSENADO\b|\bANAC\b|\bANTAQ\b|\bANS\b|\bINSS\b", n):
        return "federal"
    # Sigla de UF no nome, sem marca federal: quase sempre órgão estadual.
    return "estadual" if uf else "federal"


def _limpar_cargo(area: str) -> str:
    """'CARGO 2: ANALISTA ... – ESPECIALIDADE: CONTABILIDADE'
       → 'Analista ... — Contabilidade'"""
    txt = re.sub(r"^\s*CARGO\s*\d+\s*:\s*", "", area, flags=re.I)
    txt = re.sub(r"\s*–\s*ESPECIALIDADE\s*:\s*", " — ", txt, flags=re.I)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt.title() if txt.isupper() else txt


def coletar(_limite: int = 0) -> list[dict]:
    """Devolve achados já com cargo, prazo e salário confirmados."""
    grupos = _json(LISTA)
    if not isinstance(grupos, list):
        print("    lista de eventos indisponível")
        return []

    ativos = [
        e for g in grupos
        if g.get("faseEvento") in FASES_ATIVAS
        for e in (g.get("eventos") or [])
    ]
    print(f"    {len(ativos)} concursos ativos para inspecionar")

    achados: list[dict] = []
    for ev in ativos:
        url_ev = ev.get("eventoURL")
        if not url_ev:
            continue

        det = _json(DETALHE.format(url=url_ev))
        if not det:
            continue

        contabeis = [
            c.get("area", "") for c in (det.get("eventoCargos") or [])
            if isinstance(c, dict) and CARGO_CONTABIL.search(c.get("area", ""))
        ]
        if not contabeis:
            continue

        inicio, fim = _periodo(det.get("periodoInscricao"))
        nome = ev.get("eventoNomeAbreviado", "").strip()
        orgao, uf = _orgao_e_uf(nome)

        for area in contabeis:
            achados.append({
                "fonte": "CEBRASPE",
                "fonte_tipo": "cebraspe",
                "titulo": nome,
                "orgao_bruto": orgao,
                "texto": f"{nome} {area} {det.get('periodoInscricao') or ''}",
                "url": PAGINA.format(url=url_ev),
                "publicado_em": "",
                # Campos que a fonte entrega prontos — melhores que
                # qualquer coisa que a extração por regex inferiria.
                "_cargo": _limpar_cargo(area),
                "_banca": "CESPE/CEBRASPE",
                "_vagas": str(ev.get("eventoTotalVagas") or ""),
                "_salario": ev.get("eventoSalarioMaximo") or 0,
                "_inscricao_inicio": inicio,
                "_inscricao_fim": fim,
                "_uf": uf,
                "_esfera": _esfera(nome, uf),
                "_confianca": "alta" if (fim and ev.get("eventoSalarioMaximo")) else "media",
            })

        print(f"      {nome}: {len(contabeis)} cargo(s) contábil(is)")
        time.sleep(0.3)

    return achados
