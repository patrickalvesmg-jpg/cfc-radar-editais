# -*- coding: utf-8 -*-
"""
Auditoria de salário: acha o PDF de quem nunca teve um, e lê o cargo.

Por que existe (caso Floresta/PE, 31/08/2026): o radar publicava
"Fiscal de Tributos — R$ 15.005,27". O edital diz **R$ 1.688,08**; os
R$ 15.005,27 são do **Médico UBS** do mesmo concurso. Erro de 8,9x, e
o registro estava marcado `confianca: alta`.

O que esse caso ensinou, e que mudou o alvo desta rotina:

  · **`salarioObs` vazio NÃO significa verificado.** Floresta tinha obs
    vazia — porque o valor não veio de faixa, veio da MANCHETE do PCI.
    O marcador honesto de "não verificado" é não ter `pdfEdital`.
  · **`confianca: alta` também não significa verificado.** Ela só diz
    que a fonte trouxe cargo, prazo e salário — não que o salário seja
    do nosso cargo.

Por isso o alvo aqui é: **todo edital visível sem `pdfEdital`**.

Como acha a página do concurso — três coisas que o `descobrir.py` não
fazia e que foram medidas uma a uma:

  1. **Sobe até um elemento COM TEXTO.** O `closest('div,li,...')` para
     no primeiro container, e na FUNDATEC o <a> mora num `box-btn`
     vazio: o nome da cidade está num irmão. Resultado: 0 casamentos
     numa página que tinha o concurso.
  2. **A chave é a palavra distintiva, não o começo do nome.** "e
     Câmara de Redentora" virava "E CAMARA DE RE" e nunca casava com
     "Redentora".
  3. **O site do ÓRGÃO também serve.** Quando a banca não publica
     página por concurso, a prefeitura publica o edital (foi assim em
     Heitoraí).

E uma armadilha de casamento: **casar só pelo município pega o
concurso errado.** Embu das Artes tinha quatro concursos abertos na
mesma banca; o Contador está no 003/2026 e o primeiro que casa por
cidade é o 001/2026, só da Saúde. Por isso, quando há mais de um
candidato, esta rotina prefere aquele cujo PDF contém o cargo.

    python robo/auditar_salario.py                # todos sem pdfEdital
    python robo/auditar_salario.py --limite 10    # só os 10 primeiros
    python robo/auditar_salario.py --so-suspeitos # só salário anômalo
    python robo/auditar_salario.py --aplicar      # grava

**Ao conferir o resultado, cuidado com R$ 1.621,00.** É o salário
mínimo de 2026, e ver o mesmo valor em cidades diferentes parece bug de
leitura — o `do_texto` fica com o MENOR valor perto do cargo, então a
suspeita natural é que ele pescou o mínimo de outra linha da tabela.

Foi verificado em 31/08/2026 e **não é bug**: o edital de Equador/RN
diz, no bloco do cargo, "Cargo 16: AUDITOR DE CONTROLE INTERNO ...
Remuneração: R$ 1.621,00 ... Curso Superior em Ciências Contábeis ...
40 horas semanais". Prefeitura pequena paga mínimo a cargo de nível
superior mesmo. No mesmo PDF, os R$ 4.875,71 que tínhamos publicado são
o salário dos PROFESSORES — apareciam 7 vezes, sempre em "Cargo 1..8:
PROFESSOR".

Ou seja: o valor repetido era o certo, e o valor "plausível" era o de
outro cargo. Confirme no PDF antes de descartar leitura por parecer
baixa demais.
"""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "robo"))

import arquivo_pdf  # noqa: E402
import salario as mod_salario  # noqa: E402

ARQ = BASE / "data" / "editais.json"

# Contexto do link: sobe até um elemento que REALMENTE tenha texto.
JS_CARDS = """els => els.map(e => {
  let c = e, txt = '';
  for (let i = 0; i < 6 && c; i++) {
    txt = (c.innerText || '').replace(/\\s+/g, ' ').trim();
    if (txt.length > 25) break;
    c = c.parentElement;
  }
  return [e.href, txt.slice(0, 240)];
})"""
JS_LINKS = "els => els.map(e => [e.href, (e.textContent || '').trim().slice(0, 90)])"

PALAVRA_VAZIA = {
    "DE", "DA", "DO", "DAS", "DOS", "MUNICIPAL", "PREFEITURA", "CAMARA",
    "MUNICIPIO", "DEPARTAMENTO", "INSTITUTO", "AUTARQUIA", "AGUA", "ESGOTO",
    "SANEAMENTO", "CONSORCIO", "SERVICO", "FUNDO", "SECRETARIA", "ESTADO",
    "VEREADORES", "PREVIDENCIA", "TRIBUNAL", "CONSELHO", "REGIONAL",
}

ARQUIVO_INUTIL = re.compile(
    r"termos|politica|privacid|lgpd|cookie|manual|tutorial", re.I)


def plano(texto: str) -> str:
    return ''.join(c for c in unicodedata.normalize("NFD", (texto or "").upper())
                   if unicodedata.category(c) != "Mn")


def chaves(edital: dict) -> list[str]:
    """Palavras que identificam o concurso, mais longas primeiro."""
    fonte = f"{edital.get('cidade', '')} {edital.get('orgao', '')}"
    ps = [p for p in re.split(r"[^A-Za-zÀ-ÿ]+", plano(fonte))
          if len(p) >= 4 and p not in PALAVRA_VAZIA]
    return sorted(dict.fromkeys(ps), key=len, reverse=True)[:3]


def pdfs_da_pagina(pagina) -> list[str]:
    """Todo PDF alcançável: <a href>, javascript:...('...pdf') e cliques."""
    achados = []
    try:
        for h, _ in pagina.eval_on_selector_all("a[href]", JS_LINKS):
            if not h or ARQUIVO_INUTIL.search(h):
                continue
            if re.search(r"\.pdf|/download|/arquivo|/anexo|s3\.amazonaws", h, re.I):
                achados.append(h)
        # A URL do PDF às vezes está DENTRO do javascript: do link.
        for h, _ in pagina.eval_on_selector_all("a[href^='javascript']", JS_LINKS):
            m = re.search(r"(https?://[^'\")]+\.pdf[^'\")]*)", h or "")
            if m:
                achados.append(m.group(1))
    except Exception:
        pass
    return list(dict.fromkeys(achados))


def pdfs_por_clique(pagina) -> list[str]:
    """Bancas onde o arquivo é <span>/<td>, não <a> — INEPAM, Itame."""
    achados = []
    try:
        alvos = [e for e in pagina.query_selector_all("[onclick], span, td")
                 if "edital" in ((e.inner_text() or "").lower())]
    except Exception:
        return []
    for el in alvos[:8]:
        try:
            with pagina.expect_download(timeout=12000) as espera:
                el.click(timeout=6000)
            achados.append(espera.value.url)
        except Exception:
            continue
    return list(dict.fromkeys(achados))


def ler_cargo(edital: dict, urls: list[str]) -> tuple[float | None, str]:
    """Primeiro PDF que traz o cargo numa tabela de vencimentos."""
    for u in urls[:16]:
        texto, dados = mod_salario.baixar_pdf_completo(u)
        if not texto:
            continue
        v = mod_salario.do_texto(texto, edital.get("cargo", ""))
        if v is not None:
            if edital.get("id"):
                arquivo_pdf.guardar_bytes(edital["id"], u, dados)
            return v, u
    return None, ""


def paginas_candidatas(pagina, edital: dict, home: str) -> list[str]:
    """Páginas de concurso que casam com o edital, na banca ou no órgão."""
    ks = chaves(edital)
    if not ks:
        return []
    vistas, candidatas, fila = set(), [], [home]

    # A lista de concursos costuma estar um clique adiante da home.
    try:
        pagina.goto(home, timeout=40000, wait_until="networkidle")
        pagina.wait_for_timeout(2500)
        for h, t in pagina.eval_on_selector_all("a[href]", JS_LINKS):
            if h and h.startswith("http") and re.search(
                    r"concurso|seletivo|edital|inscri|andamento|aberto", h + " " + t, re.I):
                fila.append(h)
    except Exception:
        return []

    for url in fila[:8]:
        if url in vistas:
            continue
        vistas.add(url)
        try:
            pagina.goto(url, timeout=40000, wait_until="networkidle")
            pagina.wait_for_timeout(2800)
            cards = pagina.eval_on_selector_all("a[href]", JS_CARDS)
        except Exception:
            continue
        for href, contexto in cards:
            if not href or href.startswith("javascript") or href in candidatas:
                continue
            if any(k in plano(contexto) for k in ks):
                candidatas.append(href)

    # A página do CONCURSO vem antes da home da banca. Sem isto o
    # orçamento de PDFs se gasta nos arquivos institucionais da
    # instituição (a UEPB serve 10 PDFs de vestibular na home) e o
    # edital, que estava na página seguinte, nunca é aberto.
    def especificidade(url: str) -> tuple:
        u = plano(url)
        return (
            0 if any(k in u for k in ks) else 1,   # a URL cita a cidade
            -u.count("/"),                          # mais fundo = mais específico
        )

    return sorted(dict.fromkeys(candidatas), key=especificidade)[:6]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limite", type=int, default=0)
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--so-suspeitos", action="store_true",
                    help="só os de salário anômalo para o cargo")
    args = ap.parse_args()

    editais = json.loads(ARQ.read_text(encoding="utf-8"))
    alvos = [e for e in editais
             if e.get("status") != "encerrado"
             and not (e.get("pdfEdital") or "").strip()]
    if args.so_suspeitos:
        alvos = [e for e in alvos if (e.get("salario") or 0) >= 8000]
    if args.limite:
        alvos = alvos[:args.limite]

    print(f"auditando {len(alvos)} editais sem PDF "
          f"({'GRAVA' if args.aplicar else 'simulação'})\n", flush=True)

    from playwright.sync_api import sync_playwright
    mudancas = []
    with sync_playwright() as pw:
        nav = pw.chromium.launch(args=["--ignore-certificate-errors"])
        ctx = nav.new_context(ignore_https_errors=True, accept_downloads=True)
        for i, e in enumerate(alvos, 1):
            nome = (e.get("cidade") or e.get("orgao", ""))[:24]
            dom = e.get("bancaDominio") or ""
            home = e.get("siteInscricao") or (f"https://{dom}/" if dom else "")
            print(f"[{i}/{len(alvos)}] {nome:26} {e.get('cargo','')[:22]:24} "
                  f"R$ {e.get('salario') or 0:>10,.2f}", flush=True)
            if not home:
                print("        sem banca conhecida", flush=True)
                continue
            pagina = ctx.new_page()
            try:
                candidatas = paginas_candidatas(pagina, e, home)
                if not candidatas:
                    print("        pagina do concurso nao encontrada", flush=True)
                    continue
                valor = None
                for cand in candidatas:
                    try:
                        pagina.goto(cand, timeout=40000, wait_until="networkidle")
                        pagina.wait_for_timeout(2500)
                    except Exception:
                        continue
                    urls = pdfs_da_pagina(pagina) or pdfs_por_clique(pagina)
                    if not urls:
                        # A página casou pelo nome mas só tem navegação
                        # (foi o caso da CPCON/UEPB em Guarabira). O
                        # edital costuma estar a um clique, num link que
                        # fala de edital/anexo.
                        try:
                            adiante = [h for h, t in pagina.eval_on_selector_all(
                                           "a[href]", JS_LINKS)
                                       if h and h.startswith("http")
                                       and re.search(r"edital|anexo|abert|inscri",
                                                     h + " " + t, re.I)][:3]
                        except Exception:
                            adiante = []
                        for prox in adiante:
                            try:
                                pagina.goto(prox, timeout=35000, wait_until="networkidle")
                                pagina.wait_for_timeout(2200)
                            except Exception:
                                continue
                            urls = pdfs_da_pagina(pagina) or pdfs_por_clique(pagina)
                            if urls:
                                break
                    if not urls:
                        continue
                    valor, pdf = ler_cargo(e, urls)
                    if valor is not None:
                        antes = e.get("salario")
                        razao = (antes / valor) if (antes and valor) else 1
                        print(f"        R$ {antes or 0:,.2f} -> R$ {valor:,.2f}"
                              f"   ({razao:.1f}x)   {cand[:52]}", flush=True)
                        mudancas.append((e, valor, pdf, cand))
                        break
                if valor is None:
                    print("        cargo nao achado nos PDFs", flush=True)
            except Exception as ex:
                print(f"        ERRO {type(ex).__name__}: {str(ex)[:60]}", flush=True)
            finally:
                pagina.close()
        nav.close()

    print("\n" + "=" * 64)
    print(f"verificados com PDF: {len(mudancas)} de {len(alvos)}")
    piores = sorted(mudancas, key=lambda m: -((m[0].get("salario") or 0) / m[1]))
    for e, v, _, _ in piores[:12]:
        antes = e.get("salario") or 0
        print(f"  {antes/v:>5.1f}x  {(e.get('cidade') or e.get('orgao',''))[:24]:26} "
              f"R$ {antes:>10,.2f} -> R$ {v:>9,.2f}")

    if args.aplicar and mudancas:
        for e, v, pdf, pagina_url in mudancas:
            e["salario"] = v
            e["salarioObs"] = ""
            e["pdfEdital"] = pdf
            e["siteInscricao"] = pagina_url
        import editorial
        editorial.aplicar(editais)
        arquivo_pdf.aplicar_aos_editais(editais)
        ARQ.write_text(json.dumps(editais, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        print(f"\nGravado: {len(mudancas)} editais atualizados")
    elif mudancas:
        print("\n(simulação — rode com --aplicar para gravar)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
