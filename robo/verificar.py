# -*- coding: utf-8 -*-
"""Verificação obrigatória de TODOS os editais (pedido do Patrick).

Para cada edital visível, o ciclo completo:

    1. abrir a página do concurso na banca
    2. baixar TODOS os PDFs dela
    3. achar o que traz a tabela de vencimentos
    4. ler o salário DO CARGO daquele edital
    5. gravar valor e PDF

Diferente das rodadas anteriores, que só olhavam o PDF já guardado.
Aqui abrimos cada PDF da página até achar o que tem o cargo — foi
assim que o de Primavera do Leste apareceu: o valor certo
(R$ 16.346,38) estava no primeiro de dez arquivos.

Não confia no PDF salvo: relê e regrava.
"""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "robo"))

import aprofundar
import descobrir
import salario as mod_salario

LIXO = re.compile(r"termos|politicas|privacidade|lgpd", re.I)


def pdfs_da_pagina(pg, url):
    """Todo PDF alcançável a partir da página do concurso."""
    try:
        pg.goto(url, timeout=35000, wait_until="networkidle")
        pg.wait_for_timeout(2000)
        hrefs = pg.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
    except Exception:
        return []
    vistos, saida = set(), []
    for h in hrefs:
        if not h or h in vistos or LIXO.search(h):
            continue
        if re.search(r"\.pdf|/download|/arquivo|downloadAnexo", h, re.I):
            vistos.add(h)
            saida.append(h)
    return saida


def melhor_valor(pdfs, cargo):
    """Abre cada PDF e devolve (valor, url) do primeiro que tiver o
    cargo numa tabela de vencimentos."""
    for u in pdfs[:12]:
        texto = mod_salario.baixar_pdf(u)
        if not texto:
            continue
        v = mod_salario.do_texto(texto, cargo)
        if v is not None:
            return v, u
    return None, ""


arq = BASE / "data/editais.json"
editais = json.loads(arq.read_text(encoding="utf-8"))

alvos = [e for e in editais
         if e.get("status") != "encerrado"
         and ((e.get("siteInscricao") or "").strip() or (e.get("pdfEdital") or "").strip())]

print(f"verificando {len(alvos)} editais — abrir página, baixar PDFs, ler o cargo\n",
      flush=True)

from playwright.sync_api import sync_playwright

conferiu = corrigiu = sem_pdf = 0
with sync_playwright() as pw:
    nav = pw.chromium.launch()
    for i, e in enumerate(alvos, 1):
        cargo = e.get("cargo", "")
        nome = (e.get("cidade") or e.get("orgao", ""))[:24]
        site = e.get("siteInscricao") or ""

        candidatos = []
        if site and site.count("/") > 2:
            pg = nav.new_page(accept_downloads=True)
            try:
                candidatos = pdfs_da_pagina(pg, site)
            except Exception:
                candidatos = []
            finally:
                pg.close()

        # o PDF já guardado entra na fila também
        if e.get("pdfEdital") and e["pdfEdital"] not in candidatos:
            candidatos.insert(0, e["pdfEdital"])

        if not candidatos:
            sem_pdf += 1
            print(f"  [{i}/{len(alvos)}] SEM PDF          {nome:24} {cargo[:22]}",
                  flush=True)
            continue

        valor, url = melhor_valor(candidatos, cargo)
        if valor is None:
            sem_pdf += 1
            print(f"  [{i}/{len(alvos)}] cargo não achado  {nome:24} {cargo[:22]} "
                  f"({len(candidatos)} PDFs)", flush=True)
            continue

        atual = e.get("salario")
        if atual is not None and abs(valor - atual) <= 0.01:
            conferiu += 1
            if url != e.get("pdfEdital"):
                e["pdfEdital"] = url
        else:
            corrigiu += 1
            print(f"  [{i}/{len(alvos)}] R$ {atual if atual is not None else 0:>9,.2f} "
                  f"-> R$ {valor:>9,.2f}  {nome:24} {cargo[:20]}", flush=True)
            e["salario"] = valor
            e["salarioObs"] = ""
            e["pdfEdital"] = url

if corrigiu:
    import editorial
    editorial.aplicar(editais)
    print("\n  editoriais regenerados")

arq.write_text(json.dumps(editais, ensure_ascii=False, indent=1), encoding="utf-8")

print(f"\n{'='*58}")
print(f"CONFERIDOS no PDF : {conferiu}")
print(f"CORRIGIDOS        : {corrigiu}")
print(f"sem PDF utilizável: {sem_pdf}")
