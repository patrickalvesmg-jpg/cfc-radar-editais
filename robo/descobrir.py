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
# Vale para a URL e para o TEXTO do link. Só a URL não bastava: a
# INEPAM chama a lista de "Concursos e Processos Seletivos" mas o
# endereço é /home.do, que não casa com nada.
PADRAO_LISTA = re.compile(
    r"concurso|seletivo|edital|inscri|andamento|aberto|certame", re.I)

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
_JS_LINKS = r"""els => els.map(e => {
  const caixa = e.closest('div,li,tr,article,section') || e;
  return [e.href,
          (e.innerText + ' ' + caixa.innerText)
            .replace(/\s+/g, ' ').trim().slice(0, 300)];
})"""

# Elementos que se comportam como link sem ser <a>. A INEPAM lista os
# concursos em <span class="fm-contest-link"> que responde a clique por
# JavaScript — para quem lê a[href], a página parece vazia.
_SELETOR_CLICAVEL = (
    "span[class*=link], span[class*=contest], span[class*=row-text], "
    "td[onclick], tr[onclick], div[onclick], span[onclick], "
    "[role=link], [role=button], button"
)


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


def _marca(url: str) -> str:
    """O nome da banca dentro do domínio, para reconhecê-la em outro
    subdomínio: "https://www.inepam.org.br" -> "inepam".

    Sem isto, seguir para outro host abriria a porta para sair do site
    da banca e cair em portal de terceiro — que a regra do Patrick
    proíbe apontar.
    """
    m = re.search(r"https?://([^/]+)", url or "")
    if not m:
        return ""
    partes = [x for x in m.group(1).lower().split(".")
              if x not in ("www", "com", "br", "org", "net", "gov", "edu")]
    return max(partes, key=len) if partes else ""


# Sobe do texto até o bloco que reage ao clique. Cada banca usa uma
# tag diferente para o item — <span> na INEPAM, <h4> no IBAM,
# <p class="card-text"> no Itame — mas em todas o item é um bloco
# clicável em volta do nome do município.
_JS_CAIXA_CLICAVEL = """el => {
  let n = el;
  for (let i = 0; i < 6 && n; i++) {
    if (n.tagName === 'A' || n.onclick || n.getAttribute('onclick') ||
        n.getAttribute('href') || n.getAttribute('role') === 'link' ||
        n.getAttribute('role') === 'button' ||
        (n.className || '').toString().match(/card|item|concurso|certame|box/i)) {
      return n;
    }
    n = n.parentElement;
  }
  return el;
}"""


def _clicar_ate_o_concurso(pagina, chaves: list) -> str:
    """Clica no item que cita a cidade e devolve a URL onde parou.

    Para bancas cujo "link" não é <a href>. Sem isto a página parece
    vazia mesmo listando o concurso na tela.
    """
    candidatos = []

    # 1) os suspeitos de sempre
    try:
        candidatos.extend(pagina.query_selector_all(_SELETOR_CLICAVEL))
    except Exception:
        pass

    # 2) qualquer elemento de texto que cite a cidade — a tag varia por
    #    banca, então não dá para listá-las todas.
    try:
        candidatos.extend(pagina.query_selector_all(
            "h1,h2,h3,h4,h5,p,li,strong,b,label"))
    except Exception:
        pass

    for el in candidatos[:220]:
        try:
            texto = _plano(el.inner_text())
        except Exception:
            continue
        if not texto or not any(k in texto for k in chaves):
            continue
        # Texto longo demais é a página inteira, não o item.
        if len(texto) > 180:
            continue

        try:
            alvo = el.evaluate_handle(_JS_CAIXA_CLICAVEL).as_element() or el
        except Exception:
            alvo = el

        antes = pagina.url
        try:
            alvo.click(timeout=8000)
            pagina.wait_for_timeout(3000)
        except Exception:
            continue
        if pagina.url != antes:
            return pagina.url
    return ""


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


# Ações e documentos dentro de um cartão de concurso.
_JS_DO_CARTAO = """el => {
  let caixa = el;
  for (let i = 0; i < 7 && caixa; i++) {
    if ((caixa.className || '').toString().match(/card|item|concurso|certame/i)
        && caixa.querySelectorAll('a[href]').length > 1) break;
    caixa = caixa.parentElement;
  }
  if (!caixa) return [];
  return Array.from(caixa.querySelectorAll('a[href]'))
    .map(a => [a.href, (a.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 90)]);
}"""


def links_do_cartao(pagina, chaves: list) -> list:
    """[(href, texto)] de dentro do cartão que cita a cidade.

    Para bancas que publicam tudo na home, sem página por concurso —
    o IBAM é assim: anexos, edital e inscrição ficam no próprio cartão
    do município.
    """
    try:
        elementos = pagina.query_selector_all("h1,h2,h3,h4,h5,strong,b,span,td,p")
    except Exception:
        return []

    for el in elementos[:220]:
        try:
            texto = _plano(el.inner_text())
        except Exception:
            continue
        if not texto or len(texto) > 180:
            continue
        if not any(k in texto for k in chaves):
            continue
        try:
            achados = el.evaluate(_JS_DO_CARTAO)
        except Exception:
            continue
        if achados and len(achados) > 1:
            return [(h, t) for h, t in achados if h]
    return []


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

    # A página pode listar o concurso sem usar <a href>.
    achado = _clicar_ate_o_concurso(pagina, chaves)
    if achado:
        return achado

    # 2º nível: a lista costuma ser uma página à parte — às vezes em
    # OUTRO SUBDOMÍNIO (app.inepam.org.br). Casamos pela URL ou pelo
    # texto do link, e só seguimos para host diferente se a marca da
    # banca continuar no endereço.
    marca = _marca(home)
    candidatas, vistas = [], set()
    for href, texto in dados:
        if not href or not href.startswith("http") or href in vistas:
            continue
        if PADRAO_RUIM.search(href):
            continue
        if not (PADRAO_LISTA.search(href) or PADRAO_LISTA.search(texto)):
            continue
        if marca and marca not in href.lower():
            continue
        vistas.add(href)
        candidatas.append(href)

    for url in candidatas[:4]:
        try:
            dados2 = links(url)
        except Exception:
            continue
        achado = _casar(dados2, chaves) or _clicar_ate_o_concurso(pagina, chaves)
        if achado:
            return achado

    return ""
