# -*- coding: utf-8 -*-
"""
Remove a cópia do PDF dos editais que já encerraram.

Política decidida pelo Patrick (31/08/2026): **guardar o PDF enquanto o
concurso está aberto, apagar quando encerra.**

O motivo é o peso do repositório. Cada edital pesa de 200 KB a 2 MB, e
sem limpeza o `data/editais-pdf/` cresce para sempre — o GitHub Pages
tem teto de 1 GB, e um repositório pesado é lento de clonar.

**Importante, e a razão de isto estar escrito aqui:** apagar o arquivo
do disco NÃO o tira do histórico do Git. Quem clonar o repositório
inteiro continua baixando todos os PDFs que já passaram por aqui. O que
esta rotina evita é o crescimento da árvore de trabalho e do Pages, não
o do histórico. Para limpar o histórico seria preciso reescrevê-lo
(`git filter-repo`), o que muda todos os commits — decisão bem maior,
não tomada aqui.

Editais encerrados continuam no site, na aba própria: quem some é só o
arquivo. A página mantém o link oficial da banca.

    python robo/limpar_pdf.py            # mostra o que sairia
    python robo/limpar_pdf.py --aplicar  # apaga de verdade
"""

import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "robo"))

import arquivo_pdf  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true",
                    help="apaga de verdade (sem isto, só lista)")
    args = ap.parse_args()

    editais = json.loads((BASE / "data/editais.json").read_text(encoding="utf-8"))
    encerrados = {e["id"] for e in editais if e.get("status") == "encerrado"}

    idx = arquivo_pdf._indice()
    alvos = [(eid, reg) for eid, reg in idx.items() if eid in encerrados]

    if not alvos:
        print("Nenhum PDF de edital encerrado. Nada a fazer.")
        return 0

    total = sum(reg["bytes"] for _, reg in alvos)
    for eid, reg in alvos:
        ed = next((e for e in editais if e["id"] == eid), {})
        nome = (ed.get("cidade") or ed.get("orgao", ""))[:30]
        print(f"  {reg['bytes']/1024:>7.0f} KB  {nome:32} {ed.get('cargo','')[:24]}")

    print(f"\n{len(alvos)} arquivo(s), {total/1024/1024:.1f} MB")

    if not args.aplicar:
        print("\n(simulação — rode com --aplicar para apagar)")
        return 0

    apagados = 0
    for eid, reg in alvos:
        caminho = BASE / reg["arquivo"]
        if caminho.exists():
            caminho.unlink()
            apagados += 1
        idx.pop(eid, None)
    arquivo_pdf._gravar_indice(idx)

    # Tira o campo dos editais que perderam a cópia.
    for e in editais:
        if e["id"] in encerrados:
            e.pop("pdfArquivo", None)
            e.pop("pdfArquivoEm", None)
    (BASE / "data/editais.json").write_text(
        json.dumps(editais, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\nApagados: {apagados} arquivo(s), {total/1024/1024:.1f} MB liberados")
    print("Lembre: o histórico do Git ainda guarda o que já foi commitado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
