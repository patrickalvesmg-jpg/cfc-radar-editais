# -*- coding: utf-8 -*-
"""
Aprofundamento: link do concurso, PDF do edital e salário do cargo.

Roda DEPOIS da captura, sobre o acervo já mesclado. Três passos por
edital, cada um só quando o anterior deu certo:

  1. link da página do concurso no site da banca  (descobrir.py)
  2. link do PDF do edital, dentro dessa página
  3. salário do CARGO, lido do PDF                (salario.py)

Por que separado do `atualizar.py`: isto abre navegador e baixa PDF —
é lento (segundos por edital) e falha por motivos que não são nossos
(site fora do ar, certificado vencido). Uma fonte quebrada não pode
derrubar a varredura inteira, então cada edital é protegido e o que
falha simplesmente mantém o que já tinha.

Nunca piora o que existe: só grava campo que estava vazio ou salário
que veio de fonte melhor.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import descobrir
import salario as mod_salario

# Onde mora a tabela cargo x vencimento.
#
# Duas armadilhas, as duas medidas:
#
#   · "anexo i" casa também com "ANEXO ÚNICO ... ISENÇÃO DE TAXA",
#     que não tem salário nenhum. Foi o que aconteceu em Coronel
#     Vivida: guardamos o anexo de isenção e o salário seguiu sendo
#     os R$ 21.525 da manchete, quando o Contador ganha R$ 6.347,27.
#
#   · Nem toda banca separa a tabela num anexo. Na FAFIPA ela está
#     dentro do EDITAL DE ABERTURA (261 mil caracteres) — por isso
#     ele entra como segunda opção.
ANEXO_SALARIO = re.compile(
    r"anexo\s+(?:i|1)\b|vencimento|remunera[çc][ãa]o"
    r"|quadro\s+de\s+(?:cargos|vagas)",
    re.I)

# Segunda opção: o edital de abertura traz a tabela no corpo.
EDITAL_ABERTURA = re.compile(r"edital\s+de\s+abertura", re.I)

# Nunca servem: falam de isenção, recurso, resultado — não de cargo.
ANEXO_INUTIL = re.compile(
    r"isen[çc][ãa]o|declara[çc][ãa]o|laudo|modelo|recurso|resultado"
    r"|homologa|deferimento|cronograma|conte[úu]do\s+program", re.I)

# Arquivos que não são <a href> — ver `_pdf_por_clique`.
_SELETOR_ARQUIVO = (
    "span[class*=row-text], span[class*=link], span[class*=arquivo], "
    "td[onclick], tr[onclick], div[onclick], span[onclick], [role=button]"
)

_JS_PDFS = r"""els => els.map(e => {
  const c = e.closest('div,li,tr,article,section') || e;
  return [e.href, (e.innerText + ' ' + c.innerText)
                    .replace(/\s+/g,' ').trim().slice(0, 220)];
})"""


def _pdfs_da_pagina(pagina, url: str) -> list:
    """[(href, texto)] dos links que levam a PDF."""
    try:
        pagina.goto(url, timeout=30000, wait_until="networkidle")
        pagina.wait_for_timeout(1500)
        dados = pagina.eval_on_selector_all("a[href]", _JS_PDFS)
    except Exception:
        return []
    return [(h, t) for h, t in dados
            if h and re.search(r"\.pdf|/download/|/arquivo", h, re.I)
            and not re.search(r"termos|politica|privacidade|lgpd", h, re.I)]


def _pdf_por_clique(pagina) -> str:
    """Clica no item de edital e devolve o endereço do download.

    Para bancas onde o arquivo não é <a href>: na INEPAM, "ARQUIVOS
    DISPONÍVEIS" são <span> e o downloadAnexo.do só aparece quando o
    navegador começa a baixar.
    """
    try:
        elementos = pagina.query_selector_all(_SELETOR_ARQUIVO)
    except Exception:
        return ""

    # O edital de abertura primeiro; retificação e isenção não têm a
    # tabela de vencimentos.
    def prioridade(texto: str) -> int:
        t = texto.lower()
        # Retificação altera o edital, não o substitui: são poucas
        # linhas, sem a tabela de cargos.
        if re.search(r"rerratifica|retifica|errata", t):
            return 4
        if ANEXO_INUTIL.search(t):
            return 3
        if ANEXO_SALARIO.search(t):
            return 0
        if "abertura" in t or "edital do concurso" in t:
            return 1
        if "edital" in t:
            return 2
        return 3

    candidatos = []
    for el in elementos[:60]:
        try:
            texto = (el.inner_text() or "").strip()
        except Exception:
            continue
        if len(texto) > 6 and "edital" in texto.lower():
            candidatos.append((prioridade(texto), texto, el))

    for _, texto, el in sorted(candidatos, key=lambda x: x[0])[:3]:
        try:
            with pagina.expect_download(timeout=20000) as espera:
                el.click(timeout=8000)
            return espera.value.url
        except Exception:
            continue
    return ""


def _melhor_pdf(pdfs: list) -> str:
    """O PDF com mais chance de ter a tabela cargo x vencimento.

    Ordem: anexo de vencimentos (menor e direto ao ponto), depois o
    edital de abertura (traz a tabela no corpo), depois qualquer um.
    Os que só tratam de isenção, recurso ou resultado ficam de fora.
    """
    uteis = [(h, t) for h, t in pdfs if not ANEXO_INUTIL.search(t)]

    for href, texto in uteis:
        if ANEXO_SALARIO.search(texto):
            return href
    for href, texto in uteis:
        if EDITAL_ABERTURA.search(texto):
            return href
    return uteis[0][0] if uteis else (pdfs[0][0] if pdfs else "")


def _inscricao_do_cargo(links: list, cargo: str) -> str:
    """A inscrição do cargo contábil, quando a banca lista uma por cargo.

    No IBAM cada cargo tem seu link ("004 | ANALISTA FISC.
    MUN.-CONTABILIDADE"). Mandar a pessoa para a inscrição do
    engenheiro seria pior que mandá-la para a home.
    """
    if not cargo:
        return ""
    palavras = [p for p in re.split(r"\W+", cargo.lower()) if len(p) > 3]
    if not palavras:
        return ""

    melhor, nota_melhor = "", 0
    for href, texto in links:
        t = texto.lower()
        if "inscre" in t and len(t) < 16:      # botão "INSCREVA-SE" solto
            continue
        nota = sum(1 for p in palavras if p[:6] in t)
        if nota > nota_melhor:
            melhor, nota_melhor = href, nota
    return melhor if nota_melhor else ""


def aprofundar_um(pagina, edital: dict) -> dict:
    """Enriquece um edital. Devolve o que mudou, para o log."""
    mudou = {}

    # ---- 1. corrige link renomeado (IBGP trocou /informacoes/ por .jsp)
    atual = edital.get("siteInscricao") or ""
    corrigido = descobrir.corrigir_url(atual)
    if corrigido != atual:
        edital["siteInscricao"] = corrigido
        mudou["siteInscricao"] = corrigido
        atual = corrigido

    # ---- 2. página do concurso, quando só temos o domínio da banca
    if atual and atual.count("/") <= 2:
        achado = descobrir.descobrir(pagina, atual, edital)
        if achado:
            edital["siteInscricao"] = achado
            mudou["siteInscricao"] = achado
            atual = achado
        else:
            # Nem toda banca tem página por concurso: o IBAM publica
            # tudo na home, dentro do cartão do município — anexos,
            # edital e um link de inscrição por cargo. Procurar uma
            # página separada ali era buscar o que não existe.
            do_cartao = descobrir.links_do_cartao(
                pagina, descobrir.chaves_do_edital(edital))
            if do_cartao:
                pdf = _melhor_pdf(do_cartao)
                if pdf and mod_salario.baixar_pdf(pdf):
                    edital["pdfEdital"] = pdf
                    mudou["pdfEdital"] = pdf
                # Inscrição: preferimos a do CARGO contábil, se houver.
                inscricao = _inscricao_do_cargo(do_cartao, edital.get("cargo", ""))
                if inscricao:
                    edital["siteInscricao"] = inscricao
                    mudou["siteInscricao"] = inscricao
                    atual = inscricao

    # ---- 3. PDF do edital
    #
    # Vale reabrir a página mesmo com `pdfEdital` preenchido: o que
    # está lá pode ser o PDF ERRADO. Lagoa da Prata tinha o edital do
    # concurso 741 guardado num registro do 665 — o Anexo I certo nunca
    # era baixado, e o salário seguia sendo o da manchete (R$ 21.489
    # para um Técnico em Contabilidade que ganha R$ 3.859).
    #
    # Só troca por um ANEXO de vencimentos: o edital completo que já
    # estava lá continua valendo se nada melhor aparecer.
    if atual and atual.count("/") > 2:
        pdfs = _pdfs_da_pagina(pagina, atual)
        candidato = _melhor_pdf(pdfs)
        if not candidato:
            # A página pode listar o edital sem <a href>.
            candidato = _pdf_por_clique(pagina)
        # Só troca se o candidato ABRIR: link que devolve HTML deixaria
        # o botão "Baixar edital" entregando página de erro.
        if candidato and candidato != edital.get("pdfEdital"):
            if mod_salario.baixar_pdf(candidato):
                edital["pdfEdital"] = candidato
                mudou["pdfEdital"] = candidato

    # ---- 4. salário do cargo
    pdf = edital.get("pdfEdital") or ""
    if pdf:
        texto = mod_salario.baixar_pdf(pdf)
        if texto:
            valor, obs = mod_salario.resolver(edital.get("cargo", ""), texto)
            if valor is not None:
                antes = edital.get("salario")
                edital["salario"] = valor
                edital["salarioObs"] = obs
                if antes != valor:
                    mudou["salario"] = f"{antes} -> {valor}"
    return mudou


def aprofundar(editais: list, limite: int = 0) -> int:
    """Enriquece a lista inteira. Devolve quantos mudaram."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("    playwright não instalado — aprofundamento pulado")
        return 0

    alvos = [e for e in editais if e.get("status") != "encerrado"]
    if limite:
        alvos = alvos[:limite]
    print(f"\n  Aprofundando {len(alvos)} editais (link, PDF, salário)")

    total = 0
    with sync_playwright() as pw:
        navegador = pw.chromium.launch()
        for i, e in enumerate(alvos, 1):
            # Uma aba por edital: reaproveitar faz a navegação seguinte
            # cancelar a anterior e todas falharem por engano.
            pagina = navegador.new_page()
            try:
                mudou = aprofundar_um(pagina, e)
            except Exception as erro:
                mudou = {}
                print(f"    [{i}/{len(alvos)}] {type(erro).__name__} "
                      f"em {(e.get('cidade') or e.get('orgao', ''))[:26]}")
            finally:
                pagina.close()

            if mudou:
                total += 1
                nome = (e.get("cidade") or e.get("orgao", ""))[:24]
                if "salario" in mudou:
                    print(f"    [{i}/{len(alvos)}] {nome:24} salário {mudou['salario']}")
                else:
                    print(f"    [{i}/{len(alvos)}] {nome:24} {', '.join(mudou)}")
        navegador.close()

    print(f"  {total} editais enriquecidos")
    return total


# ------------------------------------------------------------------
# Linha de comando — é assim que o workflow semanal chama.
# ------------------------------------------------------------------

def main() -> int:
    import argparse
    import json

    ap = argparse.ArgumentParser(description="Aprofunda os editais")
    ap.add_argument("--pendentes", action="store_true",
                    help="só os que estão sem link específico ou sem PDF")
    ap.add_argument("--limite", type=int, default=0,
                    help="no máximo N editais (0 = todos)")
    args = ap.parse_args()

    arquivo = Path(__file__).resolve().parent.parent / "data" / "editais.json"
    editais = json.loads(arquivo.read_text(encoding="utf-8"))

    alvos = editais
    if args.pendentes:
        # Quem já tem link do concurso E PDF não precisa ser revisitado
        # toda semana: são ~40 min de navegador para reconfirmar o que
        # já está certo.
        alvos = [e for e in editais
                 if (e.get("siteInscricao") or "").count("/") <= 2
                 or not e.get("pdfEdital")]
        print(f"  pendentes: {len(alvos)} de {len(editais)}")

    if args.limite:
        alvos = alvos[:args.limite]

    aprofundar(alvos)

    arquivo.write_text(json.dumps(editais, ensure_ascii=False, indent=1),
                       encoding="utf-8")
    print(f"  gravado: {len(editais)} editais")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
