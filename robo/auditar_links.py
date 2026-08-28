# -*- coding: utf-8 -*-
"""Testa TODOS os links de TODOS os concursos visíveis.

Três links por edital podem estar quebrados:
  · siteInscricao  — a página do concurso na banca
  · pdfEdital      — o arquivo do edital
  · bancaDominio   — o site da organizadora (vira o link "Organizadora")

Um link que não abre é pior que link ausente: a pessoa clica esperando
o edital e recebe erro. Aqui só diagnostica — a correção vem depois,
caso a caso.
"""
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def testar(url, tempo=25):
    """(ok, detalhe). Segue redirecionamento; HEAD com fallback para GET."""
    if not url:
        return None, "vazio"
    if not url.startswith("http"):
        return False, "sem esquema"
    try:
        req = urllib.request.Request(url, headers=UA, method="HEAD")
        r = urllib.request.urlopen(req, timeout=tempo)
        return (200 <= r.status < 400), f"HTTP {r.status}"
    except urllib.error.HTTPError as e:
        if e.code in (403, 405, 501):        # servidor recusa HEAD
            try:
                req = urllib.request.Request(url, headers=UA)
                r = urllib.request.urlopen(req, timeout=tempo)
                return (200 <= r.status < 400), f"HTTP {r.status} (GET)"
            except Exception as ex2:
                return False, f"{type(ex2).__name__}"
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, type(e).__name__


d = json.loads((BASE / "data/editais.json").read_text(encoding="utf-8"))
vis = [e for e in d
       if e.get("status") != "encerrado"
       and ((e.get("siteInscricao") or "").strip() or (e.get("pdfEdital") or "").strip())]

print(f"testando os links de {len(vis)} editais visíveis\n", flush=True)

quebrados = []
for i, e in enumerate(vis, 1):
    nome = (e.get("cidade") or e.get("orgao", ""))[:26]
    linhas = []

    for campo, url in (("siteInscricao", e.get("siteInscricao")),
                       ("pdfEdital", e.get("pdfEdital"))):
        ok, det = testar(url)
        if ok is False:
            linhas.append((campo, url, det))

    dom = (e.get("bancaDominio") or "").strip()
    if dom:
        ok, det = testar(f"https://{dom}/")
        if ok is False:
            linhas.append(("bancaDominio", dom, det))

    if linhas:
        quebrados.append((e, linhas))
        for campo, url, det in linhas:
            print(f"  [{i}/{len(vis)}] {campo:14} {det:16} {nome:26} {str(url)[:44]}",
                  flush=True)

print(f"\n{'='*60}")
print(f"editais com algum link quebrado: {len(quebrados)} de {len(vis)}")

saida = BASE / "links-quebrados.json"
saida.write_text(json.dumps(
    [{"id": e["id"], "orgao": e.get("orgao"), "cargo": e.get("cargo"),
      "problemas": [{"campo": c, "url": u, "erro": d} for c, u, d in ls]}
     for e, ls in quebrados], ensure_ascii=False, indent=1), encoding="utf-8")
print(f"detalhe em {saida.name}")
