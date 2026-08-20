# -*- coding: utf-8 -*-
"""
Fonte: IBGP Concursos — banca organizadora, via API REST própria.

https://novo.ibgpconcursos.com.br/

O IBGP já chegava até nós de segunda mão, pelo PCI, o que trazia dois
problemas: só entrava o concurso que o PCI tivesse indexado, e o cargo
vinha inferido de texto corrido. A API da própria banca resolve os dois.

## As rotas

    /rest/concurso/proximasInscricoes   lista os concursos
    /rest/concurso/cargos/{id}          os cargos de um concurso

A listagem NÃO traz os cargos — só `totalCargos: 3`. Sem abrir o detalhe
não há como saber se o concurso tem vaga contábil, então uma requisição
por concurso é inevitável (são ~20, com a pausa do http_util).

`inscricoesAbertas` existe e é a rota que o nome sugere, mas responde
**500** no servidor deles (medido em 20/08/2026). Não é bloqueio nosso:
é defeito do lado deles. Se um dia voltar, é só acrescentá-la em ROTAS —
o resto do código não muda.

## Por que a lista de cargos importa tanto

O concurso de Contagem/MG tem CINCO cargos "Auditor de Controle Interno":
Ciências Contábeis, Direito, Engenharia Civil, Tecnologia da Informação e
Contador. Só dois são vaga contábil. Filtrar pelo nome do concurso, ou
pelo cargo sem olhar a especialidade, publicaria vaga de engenheiro num
site de contabilidade.

Daí o `_NAO_CONTABIL`: quando o cargo declara a formação exigida, ela
manda. Testado nos 11 cargos reais do IBGP: 11 de 11 corretos.

Rendimento medido (20/08/2026): 8 dos 20 concursos têm cargo contábil.
"""

import json
import re

from config import PADRAO_CONTABIL, UFS
from http_util import buscar

BASE = "https://novo.ibgpconcursos.com.br"
LISTAGEM = f"{BASE}/rest/concurso/proximasInscricoes"
CARGOS = BASE + "/rest/concurso/cargos/{id}"
PAGINA = BASE + "/informacoes/{id}/"

# Cargo que declara a área de formação exigida e ela NÃO é contábil.
# "Auditor de Controle Interno - Direito" casa em PADRAO_CONTABIL por
# causa de "controle interno", mas é vaga de advogado. O mesmo vale para
# "Agente Fiscal de Saneamento": fiscalização sanitária, não tributária.
_NAO_CONTABIL = re.compile(
    r"-\s*(?:direito|engenharia|tecnologia|arquitetura|medicina|enfermagem"
    r"|psicologia|pedagogia|letras|servi[çc]o\s+social|administra[çc][ãa]o"
    r"|inform[áa]tica|comunica[çc][ãa]o|ambiental|nutri[çc][ãa]o|odontolog"
    r"|veterin[áa]ri|farm[áa]c|fisioterap)"
    r"|saneamento|sanit[áa]ri|ambiental|obras|posturas|tr[âa]nsito"
    r"|vigil[âa]ncia",
    re.I,
)

# "Tue Sep 22 16:00:00 BRT 2026" — formato Java, que é o que a API devolve.
_MES = {m: i for i, m in enumerate(
    "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}


def _data_iso(bruto: str) -> str:
    """Converte a data no formato Java para ISO. Devolve "" se não der —
    data errada é pior que data ausente, porque o site a exibe como prazo."""
    if not bruto:
        return ""
    partes = bruto.split()
    if len(partes) < 6:
        return ""
    try:
        mes = _MES.get(partes[1])
        if not mes:
            return ""
        return f"{int(partes[-1]):04d}-{mes:02d}-{int(partes[2]):02d}"
    except (ValueError, IndexError):
        return ""


def _uf(*textos: str) -> str:
    """UF de 'MUNICÍPIO DE IPABA/MG' -> 'MG'.

    Aceita vários textos porque a UF nem sempre está onde se espera:
    `empresa.nome` é 'MUNICÍPIO DE SÃO JOÃO DEL-REI', sem UF, enquanto
    `concurso.nome` traz 'SÃO JOÃO DEL-REI/MG'. Sem olhar os dois, cinco
    concursos ficavam sem estado e sumiam do mapa.
    """
    for texto in textos:
        m = re.search(r"/\s*([A-Z]{2})\b", texto or "")
        if m and m.group(1) in UFS:
            return m.group(1)
    return ""


def _titulo(bruto: str) -> str:
    """Capitaliza respeitando hífen e preposição: 'SÃO JOÃO DEL-REI' vira
    'São João Del-Rei', não 'São João Del-rei'."""
    miudas = {"de", "da", "do", "das", "dos", "e"}
    palavras = []
    for i, palavra in enumerate(bruto.strip().split()):
        baixa = palavra.lower()
        if i and baixa in miudas:
            palavras.append(baixa)
        else:
            palavras.append("-".join(p.capitalize() for p in baixa.split("-")))
    return " ".join(palavras)


def _cidade(nome: str) -> str:
    """'MUNICÍPIO DE IPABA/MG' -> 'Ipaba'. Só o que der para afirmar."""
    m = re.search(
        r"(?:MUNIC[ÍI]PIO|PREFEITURA(?:\s+MUNICIPAL)?|C[ÂA]MARA(?:\s+MUNICIPAL)?)"
        r"\s+(?:DE\s+|D[AO]\s+|D[AO]S\s+)?([^/,]+)",
        nome or "", re.I,
    )
    if not m:
        return ""
    return _titulo(m.group(1))


def _esfera(nome: str) -> str:
    n = (nome or "").upper()
    if "CÂMARA" in n or "CAMARA" in n:
        return "municipal"
    if "MUNIC" in n or "PREFEITURA" in n or "PREV" in n:
        return "municipal"
    return ""


def coletar(limite: int = 25) -> list[dict]:
    bruto = buscar(LISTAGEM)
    if not bruto:
        return []

    try:
        concursos = json.loads(bruto)
    except json.JSONDecodeError:
        print("    listagem não veio em JSON")
        return []

    if not isinstance(concursos, list):
        return []

    print(f"    {len(concursos)} concursos na listagem")

    achados: list[dict] = []
    for c in concursos:
        cid = c.get("id")
        if not cid:
            continue

        detalhe = buscar(CARGOS.format(id=cid))
        if not detalhe:
            continue
        try:
            cargos = (json.loads(detalhe).get("cargos") or [])
        except json.JSONDecodeError:
            continue

        empresa = (c.get("empresa") or {}).get("nome", "") or c.get("nome", "")
        uf = _uf(empresa, c.get("nome", ""))
        cidade = _cidade(empresa)
        esfera = _esfera(empresa)
        fim = _data_iso(c.get("fimInscricao", ""))
        inicio = _data_iso(c.get("inicioInscricao", ""))
        pagina = PAGINA.format(id=cid)

        for cargo in cargos:
            nome = (cargo.get("nome") or "").strip()
            if not nome:
                continue
            if not PADRAO_CONTABIL.search(nome):
                continue
            # A especialidade declarada manda sobre o nome genérico.
            if _NAO_CONTABIL.search(nome):
                continue

            prova = _data_iso(cargo.get("dataHoraRealizacao", ""))
            vagas = cargo.get("totalVagas")

            achados.append({
                "fonte": "IBGP Concursos",
                "fonte_tipo": "ibgp",
                "titulo": f"{empresa} — {nome}",
                "orgao_bruto": empresa,
                # Texto sintético: o filtro genérico do pipeline espera
                # marca de concurso E de abertura, e a API não entrega
                # prosa. Os dados aqui são todos da própria API.
                "texto": (
                    f"Concurso público {c.get('edital', '')} de {empresa}. "
                    f"Cargo: {nome}. Vagas: {vagas}. "
                    f"Período de inscrições de "
                    f"{c.get('inicioInscricaoFormatado', '')} a "
                    f"{c.get('fimInscricaoFormatado', '')}."
                ),
                "url": "",
                "_procedencia": pagina,
                "_site_inscricao": pagina,
                "_cargo": _titulo(nome),
                "_vagas": str(vagas) if vagas else "",
                "_uf": uf,
                "_cidade": cidade,
                "_taxa_inscricao": cargo.get("taxaInscricao") or "",
                "_inscricao_inicio": inicio,
                "_inscricao_fim": fim,
                "_data_prova": prova,
                "_esfera": esfera,
                "_banca": "IBGP Concursos",
                "_confianca": "alta" if (fim and vagas) else "media",
            })
            print(f"      {empresa[:40]:40} {nome[:30]}")

    return achados
