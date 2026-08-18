# -*- coding: utf-8 -*-
"""
Fonte: PCI Concursos — página de vagas por cargo.

https://www.pciconcursos.com.br/vagas/contador

É a fonte de MAIOR VOLUME para concursos de prefeitura, que é justamente
o que os diários municipais não entregam (ver fontes/querido_diario.py).
O PCI já faz a curadoria: agrega, normaliza e mantém só o que está no
prazo — na medição inicial, 49 de 49 vagas tinham prazo futuro, contra
diários que devolviam 18 de 34 com mais de 180 dias.

Permissão: `robots.txt` traz `Allow: /` para `*`, e `/vagas/` não está
entre os caminhos bloqueados (`/acesso/`, `/adm/`, `/pdf/`, `*.php`…).

ATENÇÃO ao cargo: a listagem mostra "Vários Cargos" em 42 de 49 casos —
o filtro por contador é do PCI, mas o nome do cargo não vem no HTML da
lista. Por isso abrimos a página de detalhe para confirmar que há mesmo
vaga contábil e extrair quantas. Sem essa confirmação publicaríamos
"Prefeitura X — Vários Cargos", que não ajuda ninguém a decidir.
"""

import json
import re

from config import PADRAO_CONTABIL
from http_util import buscar

LISTAGEM = "https://www.pciconcursos.com.br/vagas/{cargo}"

# Páginas por cargo. O PCI mantém uma por termo, então varremos as que
# interessam ao público contábil em vez de filtrar texto solto.
# Cobertura medida (2026-08-18): 195 vagas somadas nestas páginas.
#   contador 52 · fiscal 85 · contabilidade 26 · auditor 20
#   tecnico-em-contabilidade 10 · ciencias-contabeis 2
# "auditor" e "fiscal" entram porque grande parte exige formação contábil,
# mas trazem também vaga de outras áreas — quem separa é o
# `_confirmar_cargo`, que só aceita o registro se a página de detalhe
# citar cargo contábil de fato.
CARGOS = (
    "contador",
    "tecnico-em-contabilidade",
    "contabilidade",
    "ciencias-contabeis",
    "auditor",
    "fiscal",
)

BLOCO = re.compile(
    r'<div class="na".*?(?=<div class="na"|<div id="paginacao|</div>\s*</div>\s*<footer)',
    re.S,
)
URL_BLOCO = re.compile(r'data-url="([^"]+)"')
TAG = re.compile(r"<[^>]+>")

# "Contador (1 vaga + CR)" / "Contador (CR)" na página de detalhe.
CARGO_DETALHE = re.compile(
    r"((?:t[ée]cnico\s+(?:em|de)\s+contabilidade|analista\s+cont[áa]bil"
    r"|auditor[\w\s]{0,24}cont[áa]b\w*|contador(?:a)?))"
    r"\s*\(([^)]{0,40})\)",
    re.I,
)

DATA = re.compile(r"(\d{2}/\d{2}/\d{4})")
SALARIO = re.compile(r"R\$\s*([\d.]+,\d{2})")
VAGAS_TOPO = re.compile(r"(\d+)\s*vagas?", re.I)


def _campos(bloco: str) -> list[str]:
    texto = re.sub(r"\s+", " ", TAG.sub("|", bloco))
    return [c.strip() for c in texto.split("|") if c.strip() and c.strip() != "&nbsp;"]


def _iso(br: str) -> str:
    d, m, a = br.split("/")
    return f"{a}-{m}-{d}"


# Site onde a inscrição realmente acontece. Em concurso municipal é
# sempre a BANCA organizadora (Inepam, AvançaSP, GL Consultoria…), nunca
# um .gov.br — verificado em 10 de 10 concursos. Guardamos esse endereço
# para a página interna do radar poder mandar o candidato ao lugar certo
# sem passar por nenhum agregador concorrente.
SITE_OFICIAL = re.compile(
    r"(?:pelo|no|atrav[ée]s do|por meio do|junto ao)\s+"
    r"(?:site|endere[çc]o(?:\s+eletr[ôo]nico)?|portal|link)\s+"
    r"((?:https?://)?(?:www\.)?[\w-]+\.(?:org|com|net|gov|edu)(?:\.br)?)",
    re.I,
)
DOMINIO_QUALQUER = re.compile(
    r"\b((?:www\.)?[\w-]+\.(?:org|com|net|gov|edu)\.br)\b", re.I
)
# Nunca apontar para agregador ou rede social — o radar é a plataforma.
DOMINIO_PROIBIDO = re.compile(
    r"pciconcursos|schema\.org|pci\.api\.br|googletag|google|facebook"
    r"|whatsapp|instagram|twitter|youtube|linkedin|jcconcursos"
    r"|concursosnobrasil|folhadirigida|qconcursos|grancursos|estrategia",
    re.I,
)


def _site_inscricao(texto: str) -> str:
    """Endereço onde a inscrição é feita, ou '' se não der para afirmar."""
    m = SITE_OFICIAL.search(texto)
    if m:
        alvo = m.group(1)
    else:
        candidatos = [
            d for d in dict.fromkeys(DOMINIO_QUALQUER.findall(texto))
            if not DOMINIO_PROIBIDO.search(d)
        ]
        if not candidatos:
            return ""
        # .gov.br primeiro; senão o primeiro domínio citado.
        alvo = next((c for c in candidatos if ".gov.br" in c.lower()), candidatos[0])

    if DOMINIO_PROIBIDO.search(alvo):
        return ""
    return alvo if alvo.startswith("http") else f"https://{alvo}"


def _confirmar_cargo(url: str) -> tuple | None:
    """Abre o detalhe e devolve (cargo, vagas, site, resumo, texto_longo).

    Devolve None se a página não confirmar cargo contábil — melhor perder
    o registro que afirmar uma vaga que talvez não exista.
    """
    html = buscar(url)
    if not html:
        return None

    texto = re.sub(r"\s+", " ", TAG.sub(" ", html))
    if not PADRAO_CONTABIL.search(texto):
        return None

    site = _site_inscricao(texto)

    # A matéria traz um resumo em `description` do JSON-LD: uma frase
    # pronta, escrita por humano, melhor que qualquer recorte nosso.
    resumo = ""
    m_desc = re.search(r'"description"\s*:\s*"([^"]{40,400})"', html)
    if m_desc:
        # O JSON-LD escapa acento em notacao \uXXXX. Decodificar com
        # unicode_escape sobre bytes utf-8 estraga o acento ("niveis"
        # virava "nAveis"); json.loads resolve o escape preservando a
        # codificacao.
        try:
            resumo = json.loads('"' + m_desc.group(1) + '"')
        except (json.JSONDecodeError, ValueError):
            resumo = m_desc.group(1)
        resumo = re.sub(r"\s+", " ", resumo).strip()

    # Corpo da matéria, sem o JSON-LD e sem menu — é dele que saem as
    # etapas, a taxa e a validade exibidas na página do edital.
    corpo = re.sub(r'\{"@context".*?\}\]\}', " ", texto, flags=re.S)
    corpo = re.sub(r"\s+", " ", corpo).strip()

    m = CARGO_DETALHE.search(texto)
    if m:
        cargo = re.sub(r"\s+", " ", m.group(1)).strip().title()
        vagas = m.group(2).strip()
        # "1 vaga + CR" -> "1 + CR" ; "CR" -> "CR"
        vagas = re.sub(r"\s*vagas?\s*", " ", vagas, flags=re.I).strip()
        return cargo, vagas, site, resumo, corpo

    # Termo contábil presente, mas sem o padrão "Cargo (n vagas)".
    return "Área contábil — verificar edital", "", site, resumo, corpo


def coletar(limite: int = 25) -> list[dict]:
    achados: list[dict] = []
    vistos: set[str] = set()

    for cargo_url in CARGOS:
        html = buscar(LISTAGEM.format(cargo=cargo_url))
        if not html:
            continue

        blocos = BLOCO.findall(html)
        print(f"    /vagas/{cargo_url}: {len(blocos)} vagas listadas")

        for bloco in blocos[:limite]:
            m = URL_BLOCO.search(bloco)
            if not m:
                continue
            url = m.group(1)
            if url in vistos:
                continue
            vistos.add(url)

            campos = _campos(bloco)
            if not campos:
                continue

            orgao = campos[0]
            uf = next((c for c in campos if len(c) == 2 and c.isupper()), "")

            texto_bloco = " ".join(campos)
            sal_m = SALARIO.search(texto_bloco)
            salario = 0.0
            if sal_m:
                try:
                    salario = float(sal_m.group(1).replace(".", "").replace(",", "."))
                except ValueError:
                    salario = 0.0

            datas = DATA.findall(texto_bloco)
            fim = _iso(datas[-1]) if datas else ""
            inicio = _iso(datas[0]) if len(datas) > 1 else ""

            escolaridade = "superior"
            if re.search(r"m[ée]dio|t[ée]cnico", texto_bloco, re.I) and \
               not re.search(r"superior", texto_bloco, re.I):
                escolaridade = "medio"

            confirmado = _confirmar_cargo(url)
            if not confirmado:
                continue
            nome_cargo, vagas_cargo, site_inscricao, resumo, texto_longo = confirmado

            achados.append({
                "fonte": "PCI Concursos",
                "fonte_tipo": "pci",
                "titulo": orgao,
                "orgao_bruto": orgao,
                "texto": texto_bloco[:2000],
                # O `url` do agregador NÃO vai para o site: ele serve só
                # como procedência interna, para o revisor conferir a
                # origem. O radar nunca manda visitante a concorrente.
                "url": "",
                "_procedencia": url,
                "_site_inscricao": site_inscricao,
                "_resumo": resumo,
                "_texto_longo": texto_longo,
                "publicado_em": "",
                "_cargo": nome_cargo,
                # Vagas do CARGO CONTÁBIL, não o total do concurso: dizer
                # "94 vagas" quando só 1 é de contador seria enganoso.
                # Sem o número do cargo, deixamos vazio em vez de usar o
                # total — melhor campo em branco que número errado.
                "_vagas": vagas_cargo,
                "_salario": salario,
                "_inscricao_inicio": inicio,
                "_inscricao_fim": fim,
                "_uf": uf,
                "_esfera": ("municipal"
                            if re.search(r"prefeitura|c[âa]mara municipal|munic[íi]pio",
                                         orgao, re.I) else "estadual"),
                "_escolaridade": escolaridade,
                # O salário da listagem é o TETO do concurso inteiro, que
                # pode não ser o do cargo contábil. Cabe revisão.
                "_confianca": "media",
            })
            print(f"      {orgao[:44]:44} {nome_cargo[:26]}")

    return achados
