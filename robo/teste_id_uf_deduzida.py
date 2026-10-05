"""Edital capturado sem UF: quando a UF é deduzida pela cidade, o id
tem que ser recalculado — senão o mesmo concurso vira dois cards.

Caso real (05/10/2026): a AMAUC não informa UF. A "Câmara Municipal de
Vereadores de Jaborá" nasceu com id de UF vazia (e-e9de58f11c28) e não
casou com o registro já publicado da mesma câmara, vindo do PCI com
"SC" (e-1b7350f32a74).

Roda sem rede: a base de municípios é montada à mão.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import atualizar  # noqa: E402
import extrair    # noqa: E402
from fontes import estrategia  # noqa: E402

falhas = 0


def checar(nome, cond):
    global falhas
    print(f"  {'ok   ' if cond else 'FALHA'} {nome}")
    if not cond:
        falhas += 1


MUNICIPIOS = {
    f"{estrategia._chave('Jaborá')}|SC": (-27.17, -51.73),
    # "Bom Jesus" existe em vários estados: não pode deduzir
    f"{estrategia._chave('Bom Jesus')}|PI": (-9.07, -44.36),
    f"{estrategia._chave('Bom Jesus')}|RS": (-28.67, -50.43),
}

CARGO, FIM = "Coordenador De Controle Interno", "2026-10-29"


def edital(cidade, uf, id_=None):
    return {
        "id": id_ or extrair.id_estavel(cidade, uf, CARGO, FIM),
        "orgao": f"Câmara Municipal de Vereadores de {cidade}",
        "cidade": cidade, "uf": uf, "cargo": CARGO, "inscricaoFim": FIM,
    }


# 1. Capturado sem UF -> UF deduzida -> id igual ao de quem veio com UF
e = edital("Jaborá", "")
publicado = extrair.id_estavel("Jaborá", "SC", CARGO, FIM)
atualizar.geolocalizar([e], {}, MUNICIPIOS)
checar("UF deduzida pela cidade", e["uf"] == "SC")
checar("id recalculado igual ao do registro publicado", e["id"] == publicado)

# 2. Registro com id de outro formato (já publicado/curado) não é tocado
e = edital("Jaborá", "", id_="e-000000000000")
atualizar.geolocalizar([e], {}, MUNICIPIOS)
checar("id que não nasceu sem UF fica como está", e["id"] == "e-000000000000")

# 3. Cidade ambígua: sem UF deduzida, sem troca de id
e = edital("Bom Jesus", "")
antes = e["id"]
atualizar.geolocalizar([e], {}, MUNICIPIOS)
checar("cidade em vários estados não ganha UF", e["uf"] == "")
checar("e o id não muda", e["id"] == antes)

print(f"\n{falhas} falha(s)")
sys.exit(1 if falhas else 0)
