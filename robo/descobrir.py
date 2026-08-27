# -*- coding: utf-8 -*-
"""
Descoberta: a página DO CONCURSO e o PDF do edital, no site da banca.

O PCI — nossa maior fonte — ancora só a home da banca
("ibgpconcursos.com.br/"). O candidato clica e cai numa lista de
dezenas de concursos para caçar o dele. Em 81 dos 127 editais era só
isso que tínhamos.

O caminho que funciona (medido em 27/08/2026, 81 alvos):

  1. abre a home da banca num navegador de verdade;
  2. se não achar, segue os links que parecem lista de concursos;
  3. casa pelo nome da cidade/órgão lendo o CARD inteiro.

Três coisas descobertas na marra, cada uma custou uma rodada:

  · Ler `innerText` do <a> não serve. No IBGP o texto do link é
    "SAIBA MAIS" e a cidade está no card ao redor — 418 links, zero
    casamentos. É preciso ler o container.

  · Sem navegador não dá. Várias bancas (GL Consultoria, Nosso Rumo)
    montam a lista por JavaScript; o HTML cru vem com o menu e nada
    mais.

  · Uma aba por banca. Reaproveitar a mesma página fazia a navegação
    seguinte cancelar a anterior ("interrupted by another
    navigation") e TODAS as bancas falharem por engano.

O IBGP também trocou de estrutura no meio do caminho: `/informacoes/N/`
virou `/concurso.jsp?cod=N`, com o mesmo número. Os links antigos que
guardamos devolvem 404 — ver `CORRIGIR_URL`.

Isto é ACRÉSCIMO: sem achar, o edital mantém o domínio da banca, que
já funcionava. Nunca piora o que existe.
"""

import re
import unicodedata

# Lista de concursos: onde procurar quando a home não mostra nada.
PADRAO_LISTA = re.compile(
    r"concurso|seletivo|edital|inscri|andamento|aberto", re.I)

# Links que nunca são a página de um concurso.
PADRAO_RUIM = re.compile(
    r"\.pdf$|termos|politica|privacidade|facebook|instagram|whats"
    r"|t\.me|linkedin|youtube|^javascript:|^mailto:|esqueci|cadastro"
    r"|lembrarsenha|trabalhe",
    re.I,
)

# Bancas que renomearam o caminho sem mudar o número do concurso.
CORRIGIR_URL = (
    # IBGP, ago/2026: /informacoes/747/ -> /concurso.jsp?cod=747
    (re.compile(r"^(https?://[^/]*ibgpconcursos\.com\.br)/informacoes/(\d+)/?$", re.I),
     r"\1/concurso.jsp?cod=\2"),
)

# Lê o link E o texto do bloco em volta: o nome da cidade quase nunca
# está no <a>, está no card.
_JS_LINKS = """els => els.map(e => {
  const caixa = e.closest('div,li,tr,article,section') || e;
  return [e.href,
          (e.innerText + ' ' + caixa.innerText)
            .replace(/\s+/g, ' ').trim().slice(0, 300)];
})"""


def corrigir_url(url: str) -> str:
    """Aplica as renomeações conhecidas. Devolve a url intacta se
    nenhuma se aplica."""
    for padrao, troca in CORRIGIR_URL:
        if padrao.match(url or ""):
            return padrao.sub(troca, url)
    return url or ""


def _plano(texto: str) -> str:
    """Sem acento, minúsculo, só letras e números."""
    t = unicodedata.normalize("NFD", texto or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]+", " ", t.lower()).strip()


def chaves_do_edital(edital: dict) -> list[str]:
    """Nomes pelos quais este concurso pode aparecer no site da banca.

    A cidade é a melhor pista, mas órgão sem cidade ("EMDAEP", "DMAE")
    aparece pela sigla — por isso vão as duas.
    """
    saida = []
    if edital.get("cidade"):
        saida.append(_plano(edital["cidade"]))

    org = _plano(edital.get("orgao", ""))
    org = re.sub(r"^(prefeitura|municipio|camara)( municipal)?"
                 r"( de| da| do| dos| das)?\s+", "", org)
    sigla = re.match(r"^([a-z]{3,10})\b", org)
    if sigla:
        saida.append(sigla.group(1))
    if org:
        saida.append(org[:26])

    # dict.fromkeys preserva a ordem e tira repetido
    return [k for k in dict.fromkeys(saida) if len(k) > 3]


def _casar(dados: list, chaves: list[str]) -> str:
    """O primeiro link cujo card cita uma das chaves."""
    for href, texto in dados:
        if not href or PADRAO_RUIM.search(href):
            continue
        ph, pt = _plano(href), _plano(texto)
        for k in chaves:
            if k in pt or k.replace(" ", "-") in ph:
                return href
    return ""


def descobrir(pagina, home: str, edital: dict) -> str:
    """A página do concurso no site da banca. '' se não achar.

    `pagina` é uma page do Playwright — o chamador controla o
    navegador, para não abrir um por edital.
    """
    chaves = chaves_do_edital(edital)
    if not chaves or not home:
        return ""

    def links(url: str) -> list:
        pagina.goto(url, timeout=30000, wait_until="networkidle")
        pagina.wait_for_timeout(2000)
        return pagina.eval_on_selector_all("a[href]", _JS_LINKS)

    try:
        dados = links(home)
    except Exception:
        return ""

    achado = _casar(dados, chaves)
    if achado:
        return achado

    # 2º nível: a lista de concursos costuma ser uma página à parte.
    candidatas, vistas = [], set()
    for href, _ in dados:
        if (href and href.startswith("http") and href not in vistas
                and PADRAO_LISTA.search(href) and not PADRAO_RUIM.search(href)):
            vistas.add(href)
            candidatas.append(href)

    for url in candidatas[:3]:
        try:
            achado = _casar(links(url), chaves)
        except Exception:
            continue
        if achado:
            return achado

    return ""
