"""Aplica as correções da página de conferência.

Uso: python robo/aplicar_correcoes.py 19-10 [--uf ID=UF ...]
Lê Downloads/correcoes-radar-<tag>.json e conferencia-<tag>.html.
- salário informado -> grava e marca revisado
- "não publicar" (vence o salário, se vierem juntos) -> removidos.json e sai do editais.json
- listado na página sem correção -> conferido como está: revisado
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TAG = sys.argv[1]
UFS = dict(a.split("=") for a in sys.argv[2:] if "=" in a)

corr = json.loads((Path.home() / "Downloads" / f"correcoes-radar-{TAG}.json").read_text(encoding="utf-8"))["correcoes"]
pagina = (RAIZ / f"conferencia-{TAG}.html").read_text(encoding="utf-8")
listados = set(re.findall(r'<tr id="r-([^"]+)"', pagina))

caminho = RAIZ / "data/editais.json"
dados = json.loads(caminho.read_text(encoding="utf-8"))
L = dados if isinstance(dados, list) else dados["editais"]
por_id = {e["id"]: e for e in L}
rem_c = RAIZ / "data/removidos.json"
rem = json.loads(rem_c.read_text(encoding="utf-8"))


def valor(s):
    s = re.sub(r"^(R\$|\$)\s*", "", s.strip())
    if re.fullmatch(r"\d+,\d{1,2}", s):  # "3032,75" sem ponto de milhar
        return float(s.replace(",", "."))
    if re.fullmatch(r"\d{1,3}(\.\d{3})*,\d{1,2}", s):
        return float(s.replace(".", "").replace(",", "."))
    if re.fullmatch(r"\d{1,3}(\.\d{3})+\.\d{2}", s):  # "3.552.47" digitado com ponto
        return float(s.replace(".", "")[:-2] + "." + s[-2:])
    if re.fullmatch(r"\d+(\.\d{3})*", s):
        return float(s.replace(".", ""))
    if re.fullmatch(r"\d+\.\d{1,2}", s):
        return float(s)
    raise ValueError(s)


removidos, salarios, ok = [], [], 0
for i in listados | set(corr):
    e = por_id.get(i)
    if not e:
        print("  ! id não encontrado:", i)
        continue
    c = corr.get(i, {})
    if c.get("remover"):
        rem[i] = {"orgao": e["orgao"], "cargo": e["cargo"],
                  "motivo": "removido na conferência do Patrick", "em": date.today().isoformat()}
        removidos.append(i)
        continue
    if c.get("salario"):
        novo = valor(c["salario"])
        if novo != e.get("salario"):
            salarios.append((e["orgao"][:32], e["cargo"][:24], e.get("salario"), novo))
        e["salario"] = novo
        e["salarioObs"] = ""
    if i in UFS:
        e["uf"] = UFS[i]
    e["revisado"] = True
    ok += 1

L[:] = [e for e in L if e["id"] not in removidos]
for e in L:
    e.pop("_salarioDivergente", None)
caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
rem_c.write_text(json.dumps(rem, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"revisados: {ok} | removidos: {len(removidos)} | salários trocados: {len(salarios)} | arquivo: {len(L)}")
for s in salarios:
    print("  ", *s)
