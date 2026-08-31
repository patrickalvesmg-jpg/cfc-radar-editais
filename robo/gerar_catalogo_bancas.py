# -*- coding: utf-8 -*-
"""Converte a tabela do CATALOGO-ORGANIZADORAS.md em JSON estruturado.

Rode a partir da raiz do projeto, depois de editar o Markdown:

    python robo/gerar_catalogo_bancas.py

O Markdown continua sendo a fonte para leitura humana — guarda o porquê
de cada situação. O JSON (`data/bancas-catalogo.json`) é o que o robô
consome em `organizadoras.gravar_catalogo`, para que banca sem concurso
aberto não suma do catálogo. Ver CATALOGO-ORGANIZADORAS.md.
"""
import json, re, sys
from pathlib import Path
sys.path.insert(0, "robo")
import organizadoras as org

RAIZ = Path(".")
md = (RAIZ / "CATALOGO-ORGANIZADORAS.md").read_text(encoding="utf-8")

linhas = [l for l in md.splitlines() if l.startswith("| ")]
saida, vistos = [], set()
for l in linhas:
    c = [x.strip() for x in l.strip().strip("|").split("|")]
    if len(c) != 5:
        continue
    nome, site, concursos, estados, situacao = c
    if nome in ("Organizadora", "Marca", "**em uso**", "bloqueia robô",
                "órgão público", "—") or site.startswith("Mapeada"):
        continue
    site = site.strip("`").strip()
    if not site or " " in site:
        continue
    dom = org.dominio("https://" + site)
    if not dom or dom in vistos:
        continue
    vistos.add(dom)
    try:
        n = int(re.sub(r"\D", "", concursos) or 0)
    except ValueError:
        n = 0
    sit = re.sub(r"\*", "", situacao).strip()
    saida.append({
        "dominio": dom,
        "nome": org.CANONICO.get(dom, nome),
        "site": f"https://{site}/",
        "concursosHistorico": n,
        "estados": [e for e in re.split(r"[,\s]+", estados) if len(e) == 2],
        "situacao": {"em uso": "em_uso", "bloqueia robô": "bloqueia",
                     "órgão público": "orgao_publico"}.get(sit, "reserva"),
    })

saida.sort(key=lambda x: (-x["concursosHistorico"], x["nome"]))
print("total:", len(saida))
from collections import Counter
print(Counter(s["situacao"] for s in saida))
Path("data/bancas-catalogo.json").write_text(
    json.dumps(saida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
