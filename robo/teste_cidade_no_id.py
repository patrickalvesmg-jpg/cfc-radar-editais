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


def test_uf_colada_no_nome_nao_cria_duplicata():
    """"PONTA PORA MS" e "Ponta Porã" sao a MESMA cidade.

    O CEBRASPE manda a UF colada no nome e o PCI nao. Ate 01/09/2026
    isso gerava dois ids e dois cards do mesmo concurso — foi uma das
    4 duplicatas que estavam no ar.
    """
    a = extrair.id_estavel("Ponta Porã", "MS", "Contador", "2026-09-10")
    b = extrair.id_estavel("PONTA PORA MS", "MS", "Contador", "2026-09-10")
    assert a == b, "UF colada no nome ainda cria id diferente"


def test_cidades_diferentes_com_inicio_igual_nao_se_fundem():
    """A correcao acima nao pode fundir cidade de verdade.

    Cheguei a cortar a chave em 10 caracteres para tambem resolver o
    nome truncado; medido no acervo, isso unia "Conceicao da Barra de
    Minas" com "Conceicao do Mato Dentro" — duas cidades de MG com
    concurso aberto ao mesmo tempo. Fundir seria pior que duplicar.
    """
    a = extrair.id_estavel("Conceição da Barra de Minas", "MG", "Contador", "2026-09-18")
    b = extrair.id_estavel("Conceição do Mato Dentro", "MG", "Contador", "2026-09-18")
    assert a != b, "cidades diferentes foram fundidas"


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