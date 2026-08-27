# -*- coding: utf-8 -*-
"""O id precisa da cidade, mesmo quando a fonte não a informa.

Em 26/08/2026 a API do PCI parou de preencher `cidade.nome`: o objeto
continua na resposta, com todas as chaves nulas, em 463 de 463
concursos — inclusive nos 278 municipais. Nosso código estava certo; a
fonte mudou.

O efeito: sem cidade, o id vira só uf|cargo|prazo. Aí "Prefeitura de
Matinhos" e "MatinhosPREV" colidem num id só, e o MESMO concurso com
prazo diferente vira dois ids. Na varredura de teste, 120 de 146
capturados apareceram como "novos" — o acervo inteiro ia duplicar.

A dedução pelo nome do órgão já existia, mas rodava em
`geolocalizar()`, DEPOIS de `montar()` ter calculado o id.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import extrair


def test_cidade_deduzida_do_orgao_entra_no_id():
    """Dois registros do mesmo concurso, um com cidade e outro sem,
    têm de gerar o MESMO id."""
    base = {
        "fonte": "PCI Concursos", "titulo": "", "texto": "",
        "url": "", "_cargo": "Contador", "_uf": "PR",
        "_inscricao_fim": "2026-09-03",
    }
    com = extrair.montar({**base, "orgao_bruto": "Prefeitura de Matinhos",
                          "_cidade": "Matinhos"})
    sem = extrair.montar({**base, "orgao_bruto": "Prefeitura de Matinhos",
                          "_cidade": ""})
    assert sem["cidade"] == "Matinhos", (
        f"cidade não deduzida do órgão: {sem['cidade']!r}")
    assert com["id"] == sem["id"], (
        f"ids divergem: com cidade {com['id']}, sem cidade {sem['id']}")


def test_orgaos_diferentes_nao_colidem():
    """Sem cidade, MatinhosPREV e a Prefeitura caíam no mesmo id."""
    base = {
        "fonte": "PCI Concursos", "titulo": "", "texto": "",
        "url": "", "_cargo": "Contador", "_uf": "PR",
        "_inscricao_fim": "2026-09-03", "_cidade": "",
    }
    a = extrair.montar({**base, "orgao_bruto": "Prefeitura de Matinhos"})
    b = extrair.montar({**base, "orgao_bruto": "Prefeitura de Curitiba"})
    assert a["id"] != b["id"], "cidades distintas geraram o mesmo id"


if __name__ == "__main__":
    falhas = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            try:
                fn()
                print(f"  ok   {nome}")
            except AssertionError as e:
                print(f"  FALHA {nome}: {e}")
                falhas += 1
    print(f"\n{falhas} falha(s)")
    sys.exit(1 if falhas else 0)
