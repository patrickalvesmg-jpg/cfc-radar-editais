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
# Páginas de cargo do PCI. Cada slug é uma listagem própria dele.
#
# Ampliado de 6 para 29 slugs em 19/08/2026, depois de sondar quais
# existem: só "contador" e "contabilidade" deixavam de fora quase 200
# vagas de cargos que TAMBÉM exigem formação contábil — fiscal de
# tributos, controlador interno, tesoureiro, auditor fiscal.
#
# Amostragem feita antes de incluir (5 vagas por slug, verificando se a
# matéria cita cargo contábil): fiscal-de-tributos 5/5, controlador
# interno 5/5, escriturário 5/5, tesoureiro 5/5, economista 4/4.
#
# Slug amplo (economista, escriturário) traz também vaga de outra área —
# quem separa é o `_confirmar_cargo`, que só aceita se a página de
# detalhe citar cargo contábil de fato.
CARGOS = (
    # núcleo contábil
    "contador",
    "tecnico-em-contabilidade",
    "tecnico-contabil",
    "contabilidade",
    "ciencias-contabeis",
    "analista-contabil",
    "auxiliar-contabil",
    # auditoria
    "auditor",
    "auditor-fiscal",
    "auditor-interno",
    "auditor-de-controle-interno",
    # controle interno e externo
    "controlador-interno",
    "analista-de-controle-interno",
    "analista-de-controle-externo",
    "tecnico-de-controle-externo",
    # tributos e arrecadação
    "fiscal",
    "fiscal-de-tributos",
    "fiscal-de-rendas",
    "agente-fiscal",
    "agente-de-tributos",
    "agente-de-arrecadacao",
    # finanças, orçamento e tesouraria
    "analista-financeiro",
    "analista-de-financas",
    "analista-orcamentario",
    "analista-de-orcamento",
    "analista-administrativo-e-financeiro",
    "tesoureiro",
    # NÃO incluir "economista" nem "escriturario": testados em
    # 19/08/2026 e REPROVADOS. Nenhuma das vagas capturadas confirmava
    # exigência contábil — escriturário de prefeitura costuma ser nível
    # médio sem relação com a área. Inflar o acervo com vaga irrelevante
    # atrapalha quem procura concurso de contador.
)

BLOCO = re.compile(
    r'<div class="na".*?(?=<div class="na"|<div id="paginacao|</div>\s*</div>\s*<footer)',
    re.S,
)
URL_BLOCO = re.compile(r'data-url="([^"]+)"')
TAG = re.compile(r"<[^>]+>")

# "Contador (1 vaga + CR)" / "Contador (CR)" na página de detalhe.
# Cargo + vagas na página de detalhe: "Contador (1 vaga + CR)".
# Cobre o núcleo contábil e os cargos adjacentes que exigem ou aceitam
# formação em Ciências Contábeis — sem eles, ampliar as páginas de
# busca não adiantaria: o registro seria capturado e descartado por
# falta de cargo reconhecido.
CARGO_DETALHE = re.compile(
    r"((?:"
    # núcleo contábil
    r"t[ée]cnico\s+(?:em|de)\s+contabilidade"
    r"|auxiliar\s+(?:de\s+)?cont[áa]b\w*"
    r"|assistente\s+(?:de\s+)?cont[áa]b\w*"
    r"|analista\s+(?:de\s+)?cont[áa]b\w*"
    r"|contador(?:a)?(?:\s+p[úu]blico)?"
    r"|contabilista"
    # auditoria
    r"|auditor[\w\s]{0,28}?(?:cont[áa]b\w*|fiscal|interno|p[úu]blico"
    r"|controle\s+(?:interno|externo))"
    # controle
    r"|controlador[\w\s]{0,16}?interno"
    r"|(?:analista|t[ée]cnico|assistente|oficial)[\w\s]{0,20}?"
    r"controle\s+(?:interno|externo)"
    # tributos e arrecadação
    r"|(?:fiscal|agente)[\w\s]{0,16}?(?:de\s+)?"
    r"(?:tributos?|rendas?|arrecada[çc][ãa]o|receita)"
    r"|analista\s+tribut[áa]rio"
    # finanças, orçamento, tesouraria
    r"|(?:analista|t[ée]cnico)[\w\s]{0,20}?"
    r"(?:financ\w+|or[çc]ament\w+|custos?)"
    r"|tesoureiro(?:a)?"
    r"))"
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


# Link com CAMINHO, não só domínio. É a diferença entre mandar o
# candidato para "inepam.org.br" — onde ele ainda precisa caçar o
# concurso — e para a página do certame dele.
_HREF = re.compile(r'href="(https?://[^"]+)"', re.I)


def _e_util(url: str) -> bool:
    """O link serve como destino? Precisa apontar para fora dos
    agregadores e ter caminho próprio (não ser só a home)."""
    if DOMINIO_PROIBIDO.search(url):
        return False
    try:
        from urllib.parse import urlparse
        caminho = urlparse(url).path.strip("/")
    except ValueError:
        return False
    if not caminho or len(caminho) < 3:
        return False
    # Descarta assets e páginas institucionais.
    return not re.search(
        r"\.(?:png|jpe?g|gif|svg|css|js|ico)$"
        r"|/(?:contato|sobre|privacidade|termos|politica|login|cookies)\b",
        caminho, re.I,
    )


def _link_concurso(html: str) -> str:
    """Página do concurso na banca, extraída dos links do CORPO.

    A matéria cita o site da banca em texto ("pelo site www.x.com.br"),
    mas ancora o link no endereço COMPLETO da página do certame. Ler o
    href é o que separa "home da banca" de "página deste concurso".
    """
    candidatos = [u for u in dict.fromkeys(_HREF.findall(html)) if _e_util(u)]
    if not candidatos:
        return ""

    # Ordem de preferência: quem se parece com página de concurso.
    for padrao in (
        r"/concurso[s]?/(?:detail|detalhe|ver)?/?\d+",
        r"/(?:informacoes|edital|concurso)[s]?/\d+",
        r"concurso\.jsp\?cod=\d+",
        r"/concurso|/edital|/processo|/selecao",
    ):
        for u in candidatos:
            if re.search(padrao, u, re.I):
                return u

    return ""


def _site_inscricao(texto: str, html: str = "") -> str:
    """Endereço da inscrição. Preferimos a página do concurso; o domínio
    da banca é o plano B."""
    especifico = _link_concurso(html) if html else ""
    if especifico:
        return especifico

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


def _extrair_cargo_e_vagas(html: str) -> tuple[str, str]:
    """Cargo contábil e número de vagas DELE, a partir do corpo visível.

    O JSON-LD (schema.org) vem ANTES do corpo no HTML, com headline,
    contador de interações e outros números que nada têm a ver com
    vaga. Rodar CARGO_DETALHE sobre o texto com o JSON-LD ainda dentro
    puxava esse lixo para o grupo de vagas quando o corpo visível não
    tinha o padrão explícito "Cargo (N vagas)" perto o bastante — foi
    assim que "658" (claramente de um contador do JSON-LD, não vaga)
    saiu idêntico em 8 concursos de estados diferentes na mesma
    varredura (31/08/2026). O corte precisa vir ANTES da busca, não
    depois: usar `corpo`, nunca `texto`, para o CARGO_DETALHE.
    """
    corpo_html = re.split(r'class="n\d{5,}"', html)[0]
    texto = re.sub(r"\s+", " ", TAG.sub(" ", corpo_html))
    corpo = re.sub(r'\{"@context".*?\}\]\}', " ", texto, flags=re.S)
    corpo = re.sub(r"\s+", " ", corpo).strip()

    m = CARGO_DETALHE.search(corpo)
    if m:
        cargo = re.sub(r"\s+", " ", m.group(1)).strip().title()
        vagas = m.group(2).strip()
        # "1 vaga + CR" -> "1 + CR" ; "CR" -> "CR"
        vagas = re.sub(r"\s*vagas?\s*", " ", vagas, flags=re.I).strip()
        return cargo, vagas

    return "Área contábil — verificar edital", ""


def _confirmar_cargo(url: str) -> tuple | None:
    """Abre o detalhe e devolve (cargo, vagas, site, resumo, texto_longo).

    Devolve None se a página não confirmar cargo contábil — melhor perder
    o registro que afirmar uma vaga que talvez não exista.
    """
    html = buscar(url)
    if not html:
        return None

    # A matéria traz uma barra lateral com ~114 links de notícias
    # relacionadas (class="nXXXXX"), e quase sempre alguma cita
    # "Contador". Rodar o filtro sobre o HTML inteiro fazia QUALQUER
    # concurso passar pelo gate contábil — testado: 4 de 4 vagas de
    # psicólogo eram aprovadas. Cortamos a barra antes de filtrar.
    corpo_html = re.split(r'class="n\d{5,}"', html)[0]
    texto = re.sub(r"\s+", " ", TAG.sub(" ", corpo_html))
    if not PADRAO_CONTABIL.search(texto):
        return None

    site = _site_inscricao(texto, html)

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

    cargo, vagas = _extrair_cargo_e_vagas(html)

    # Corpo da matéria, sem o JSON-LD e sem menu — é dele que saem as
    # etapas, a taxa e a validade exibidas na página do edital.
    corpo = re.sub(r'\{"@context".*?\}\]\}', " ", texto, flags=re.S)
    corpo = re.sub(r"\s+", " ", corpo).strip()

    return cargo, vagas, site, resumo, corpo


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
