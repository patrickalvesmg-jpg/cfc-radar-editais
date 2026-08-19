# -*- coding: utf-8 -*-
"""
Fonte: bancas organizadoras na plataforma "selecao.net" e similares.

Várias bancas usam a MESMA plataforma de site, com a rota
`/informacoes/{id}/` para cada concurso. Uma fonte genérica atende
todas — acrescentar banca aqui é acrescentar uma linha em `BANCAS`,
não um arquivo novo.

Rendimento medido (2026-08-18), em concursos com cargo contábil:
    AvançaSP   3 de 10
    Access     2 de 12
    Exame      0 de 8   (mantida: o catálogo muda toda semana)

Por que ir direto na banca, e não só pelo agregador:
  1. a página traz a TABELA DE CARGOS — confirma que há vaga contábil,
     em vez de inferir do texto da notícia;
  2. traz o PDF do edital;
  3. o link que guardamos já é a página do concurso, não a home.

Estas são bancas ORGANIZADORAS: aplicam a prova e recebem a inscrição.
Podem receber o visitante, ao contrário dos agregadores.
"""

import html
import re
from datetime import date

from http_util import buscar

# nome exibido → base do site
# Bancas na plataforma "selecao.net" e compatíveis: todas expõem
# `/informacoes/{id}/`. Lista montada sondando os 71 domínios de banca
# que aparecem nas matérias do PCI — 16 responderam com padrão
# reconhecível, 22 barram por robots.txt e 32 não têm rota previsível.
BANCAS = (
    ("Fundação FAFIPA", "https://www.fundacaofafipa.org.br"),
    ("Objetiva Concursos", "https://www.objetivas.com.br"),
    ("AvançaSP", "https://www.avancasp.org.br"),
    ("Instituto Access", "https://concursos.access.org.br"),
    ("Exame Consultores", "https://www.exameconsultores.com.br"),
    ("Fundep / Gestão de Concursos", "https://www.gestaodeconcursos.com.br"),
    ("Instituto Aplicativa", "https://www.institutoaplicativa.org.br"),
    ("AMAUC", "https://amauc.selecao.net.br"),
    ("Consulpam", "https://www.consulpam.com.br"),
    ("Instituto Vicente Nelson", "https://www.institutovicentenelson.com.br"),
    ("ISET", "https://iset.selecao.net.br"),
    ("AB Concursos Públicos", "https://abconcursospublicos.org"),
    ("JCM Concursos", "https://www.concursosjcm.com.br"),
    ("Auctor Consultoria", "https://www.auctorconsultoria.com.br"),
    ("MS Concursos", "https://www.msconc.com.br"),
    ("COTEC / FADENOR", "https://cotec-fadenor.selecao.net.br"),
    ("EducaPB", "https://www.educapb.com.br"),
    ("Selecon", "https://www.selecon.org.br"),
    ("IDCAP", "https://www.idcap.org.br"),
    # Rota própria: o terceiro item substitui /informacoes/{id}/.
    ("Instituto Mais", "https://www.institutomais.org.br", "/Concursos/Detalhe/{id}"),
)

TAG = re.compile(r"<[^>]+>")
ID_CONCURSO = re.compile(r"/informacoes/(\d+)")

# Nem toda banca usa /informacoes/{id}: o Instituto Mais usa
# /Concursos/Detalhe/{id}. A tupla de BANCAS aceita um terceiro item
# com o molde da rota, e daí sai tanto o regex quanto a URL final.
def _rota(banca):
    molde = banca[2] if len(banca) > 2 else "/informacoes/{id}/"
    padrao = re.compile(re.escape(molde).replace(r"\{id\}", r"(\d+)"))
    return molde, padrao

CARGO_VAGA = re.compile(
    r"\b((?:t[ée]cnico\s+(?:em|de)\s+contabilidade"
    r"|analista\s+cont[áa]b\w*"
    r"|auditor[\w\s]{0,20}cont[áa]b\w*"
    r"|contador(?:a)?))\b",
    re.I,
)

# Órgão CONTRATANTE, não a banca. "Instituto ACCESS" é quem organiza;
# o concurso é da prefeitura. Por isso não aceitamos "Instituto" solto
# como início do nome.
ORGAO = re.compile(
    r"(?:Munic[íi]pio|Prefeitura(?:\s+Municipal)?|C[âa]mara(?:\s+Municipal)?"
    r"|Cons[óo]rcio(?:\s+P[úu]blico)?(?:\s+Intermunicipal)?"
    r"|Servi[çc]o\s+Aut[ôo]nomo|Autarquia)"
    r"\s+(?:Municipal\s+)?(?:d[aeo]s?\s+)?"
    r"([A-ZÀ-Ú][\wÀ-ú']*(?:\s+(?:d[aeo]s?\s+)?[A-ZÀ-Ú][\wÀ-ú']*){0,4})",
)

# Nome da própria banca: nunca é o órgão do concurso.
NOME_BANCA = re.compile(
    r"instituto\s+access|avan[çc]asp|exame\s+consultores|fafipa|ibgp"
    r"|selecao\.net|nosso\s+rumo|objetivas",
    re.I,
)

INSCRICAO = re.compile(
    r"inscri[çc][õo]es?[^.]{0,120}?(\d{2}/\d{2}/\d{4})[^.]{0,60}?(\d{2}/\d{2}/\d{4})",
    re.I | re.S,
)
SALARIO = re.compile(r"R\$\s*([\d]{1,3}(?:\.\d{3})*,\d{2})")
UF_SIGLA = re.compile(r"[-–/]\s*([A-Z]{2})\b")
PDF_LINK = re.compile(r'<a[^>]+href="([^"]+\.pdf[^"]*)"[^>]*>(.*?)</a>', re.I | re.S)
ABERTURA = re.compile(r"edital\s+de\s+abertura|abertura\s+n|^edital\s+n", re.I)


def _vencido(iso: str) -> bool:
    """Inscrição encerrada não é oportunidade. O catálogo destas bancas
    mantém concurso antigo publicado — sem esta trava, entravam editais
    de 2025 como se estivessem abertos."""
    if not iso:
        return False
    try:
        return date.fromisoformat(iso) < date.today()
    except ValueError:
        return False


def _texto(bruto: str) -> str:
    return re.sub(r"\s+", " ", TAG.sub(" ", html.unescape(bruto))).strip()


def _iso(br: str) -> str:
    d, m, a = br.split("/")
    return f"{a}-{m}-{d}"


def _pdf_abertura(bruto: str) -> str:
    """Prefere o PDF cujo rótulo fale em abertura; senão, o primeiro."""
    primeiro = ""
    for m in PDF_LINK.finditer(bruto):
        if not primeiro:
            primeiro = m.group(1)
        if ABERTURA.search(_texto(m.group(2))):
            return m.group(1)
    return primeiro


def coletar(_limite: int = 0) -> list[dict]:
    achados: list[dict] = []

    for banca in BANCAS:
        nome, base = banca[0], banca[1]
        molde, id_regex = _rota(banca)
        home = buscar(f"{base}/")
        if not home:
            print(f"    {nome}: indisponível")
            continue

        # Alguns sites listam /informacoes/{id} mas servem o conteúdo em
        # outra rota (dão 404 no caminho direto). Usamos o href COMPLETO
        # que a home publica, e só montamos a URL quando não há href.
        por_id = {}
        for href in dict.fromkeys(re.findall(r'href="([^"]+)"', home)):
            m = id_regex.search(href)
            if m:
                por_id.setdefault(m.group(1),
                                  href if href.startswith("http") else base + href)

        ids = list(por_id) or list(dict.fromkeys(id_regex.findall(home)))
        encontrados = 0

        for cid in ids:
            url = por_id.get(cid) or base + molde.replace("{id}", cid)
            bruto = buscar(url)
            if not bruto:
                continue

            texto = _texto(bruto)
            m_cargo = CARGO_VAGA.search(texto)
            if not m_cargo:
                continue

            m_org = ORGAO.search(texto)
            if not m_org:
                continue
            orgao = re.sub(r"\s+", " ", m_org.group(0)).strip()[:120]
            # A captura gulosa arrastava a palavra seguinte da página
            # ("Prefeitura Municipal Inscrições"). Cortamos no primeiro
            # termo que claramente não faz parte do nome.
            orgao = re.split(
                r"\s+(?:Inscri[çc]|Edital|Concurso|Processo|Torna|Comunica"
                r"|Resultado|Cronograma|Anexo|Retifica)",
                orgao, maxsplit=1, flags=re.I,
            )[0].strip(" -–—,")
            if NOME_BANCA.search(orgao):
                continue
            # "Prefeitura Municipal" sem cidade não identifica concurso
            # nenhum. Tentamos completar com o nome que aparece no título
            # da página antes de descartar.
            if not re.search(r"\s+d[aeo]s?\s+\S|\s+[A-ZÀ-Ú]\S{3,}", orgao):
                m_tit = re.search(
                    r"<title>([^<]{6,120})</title>", bruto, re.I)
                titulo_pg = _texto(m_tit.group(1)) if m_tit else ""
                m2 = ORGAO.search(titulo_pg)
                if m2:
                    orgao = re.sub(r"\s+", " ", m2.group(0)).strip()[:120]
            if len(orgao) < 12:
                continue

            inicio = fim = ""
            m_ins = INSCRICAO.search(texto)
            if m_ins:
                try:
                    inicio, fim = _iso(m_ins.group(1)), _iso(m_ins.group(2))
                except ValueError:
                    pass

            valores = []
            for v in SALARIO.findall(texto):
                try:
                    n = float(v.replace(".", "").replace(",", "."))
                    if 1_000 <= n <= 100_000:
                        valores.append(n)
                except ValueError:
                    continue

            # Sem prazo não dá para saber se está aberto; com prazo
            # vencido, não é oportunidade.
            if not fim or _vencido(fim):
                continue

            m_uf = UF_SIGLA.search(texto[:2500])

            achados.append({
                "fonte": nome,
                "fonte_tipo": "banca",
                "titulo": orgao,
                "orgao_bruto": orgao,
                "texto": texto[:4000],
                "url": "",
                "_procedencia": url,
                # Banca organizadora: o link já é a página do concurso.
                "_site_inscricao": url,
                "_pdf_edital": _pdf_abertura(bruto),
                "_cargo": m_cargo.group(1).strip().title(),
                "_uf": m_uf.group(1) if m_uf else "",
                "_salario": max(valores) if valores else 0,
                "_inscricao_inicio": inicio,
                "_inscricao_fim": fim,
                "_banca": nome,
                "_esfera": "municipal",
                "_confianca": "alta" if (fim and valores) else "media",
            })
            encontrados += 1

        print(f"    {nome}: {encontrados} de {len(ids)} concursos")

    return achados
