# -*- coding: utf-8 -*-
"""O nome da cidade sai de dentro do nome do órgão, sem o rótulo junto.

O rótulo pode vir encadeado — "Prefeitura DO MUNICÍPIO DE Trindade" —
e aí a captura começava na segunda palavra: a cidade ia para o site
como "Município de Trindade" (visto em 21/09/2026).

A cidade não é enfeite: ela entra no `id_estavel`, então cidade
escrita de dois jeitos vira dois cards do mesmo concurso.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "fontes"))

from estrategia import nome_cidade

falhas = 0

CASOS = [
    # O caso que revelou o defeito
    ("Prefeitura do Município de Trindade", "Trindade"),
    ("Prefeitura do Municipio de Sao Joao del Rei", "Sao Joao del Rei"),
    # Os que já funcionavam e não podem regredir
    ("Prefeitura Municipal de Limeira", "Limeira"),
    ("Câmara de Governador Valadares", "Governador Valadares"),
    ("Município de Herculândia", "Herculândia"),
    ("Câmara Municipal de Capelinha", "Capelinha"),
    ("Prefeitura de Porto Calvo", "Porto Calvo"),
    ("Prefeitura Municipal de Santana de Pirapama", "Santana de Pirapama"),
    ("Prefeitura Municipal da Estância Turística de Avaré", "Avaré"),
    # Cidade cujo nome começa por preposição ou artigo
    ("Prefeitura Municipal de Bom Jesus dos Perdões", "Bom Jesus dos Perdões"),
    ("Prefeitura de Santa Rita do Passa Quatro", "Santa Rita do Passa Quatro"),
    # Concurso conjunto: dois órgãos, uma cidade só. Sem tratar o "e",
    # a cidade ia para o site como "e Câmara de Siqueira Campos"
    # (6 registros, 21/09/2026).
    ("Prefeitura e Câmara de Siqueira Campos", "Siqueira Campos"),
    ("Prefeitura e Câmara de Nísia Floresta", "Nísia Floresta"),
    ("Prefeitura e Câmara de Equador", "Equador"),
    # "de Vereadores" é parte do nome do órgão, não da cidade. Sem
    # pular, saía "Vereadores de Jaborá" e o edital ficava sem UF
    # (28/09/2026).
    ("Câmara Municipal de Vereadores de Jaborá", "Jaborá"),
    ("Câmara de Vereadores de Santa Rita do Passa Quatro", "Santa Rita do Passa Quatro"),
    # O hífen faz parte do nome. Parar nele truncava a cidade para
    # "São João del", a chave não batia com a do IBGP ("São João
    # Del-Rei") e o mesmo concurso virava dois cards — com salário
    # divergindo 3,7x entre eles (21/09/2026).
    ("Prefeitura de São João del-Rei", "São João del-Rei"),
    ("MUNICÍPIO DE SÃO JOÃO DEL-REI", "SÃO JOÃO DEL-REI"),
    ("Prefeitura de Mogi-Guaçu", "Mogi-Guaçu"),
    ("Prefeitura Municipal de Santa Rita d'Oeste", "Santa Rita d'Oeste"),
    # Mas o hífen CERCADO DE ESPAÇO separa a UF, e ela não é o nome
    ("Prefeitura Municipal de Limeira - SP", "Limeira"),
    ("Prefeitura de Porto Calvo - AL", "Porto Calvo"),
    # Dois órgãos no mesmo concurso: a conjunção não fica pendurada
    ("Prefeitura de São João del-Rei e DAMAE - SJDR", "São João del-Rei"),
    # Órgão que não é prefeitura: campo vazio, não um palpite
    ("Hospital Municipal Dr. Gil Alves", ""),
    ("Instituto de Previdência de São Manuel", ""),
]

for orgao, esperado in CASOS:
    obtido = nome_cidade(orgao)
    if obtido == esperado:
        print(f"  ok   {orgao[:48]:50} -> {obtido!r}")
    else:
        falhas += 1
        print(f"  ERRO {orgao[:48]:50} -> {obtido!r}, esperado {esperado!r}")

print("\nO rótulo nunca sobra no nome:")
for orgao in ["Prefeitura do Município de Trindade",
              "Prefeitura Municipal de Limeira",
              "Câmara Municipal de Capelinha"]:
    nome = nome_cidade(orgao)
    sujo = nome.lower().startswith(("município", "municipio", "prefeitura",
                                    "câmara", "camara"))
    if not sujo:
        print(f"  ok   {orgao[:44]:46} -> {nome!r}")
    else:
        falhas += 1
        print(f"  ERRO {orgao[:44]:46} -> {nome!r} começa com rótulo")

print("\nA UF colada sai do nome exibido, não só da chave:")
# A sigla já era tirada na CHAVE de comparação, para o mesmo concurso
# não virar dois cards. Mas o valor exibido continuava sujo: o site
# mostrava "PONTA PORA MS" (CEBRASPE) e "Ponta Porã" (PCI) lado a lado.
from extrair import _sem_uf_colada

for bruto, esperado in [
    ("PONTA PORA MS", "PONTA PORA"),
    ("CAMARA MUNICIPAL PONTA PORA MS", "CAMARA MUNICIPAL PONTA PORA"),
    ("Sao Luis MA", "Sao Luis"),
    ("Santana do Livramento RS", "Santana do Livramento"),
    # Sem sigla: fica como está
    ("Ponta Porã", "Ponta Porã"),
    ("Rio de Janeiro", "Rio de Janeiro"),
    ("Bela Vista de Goias", "Bela Vista de Goias"),
    # Nome curto demais para sobrar algo: não corta
    ("Barra", "Barra"),
]:
    obtido = _sem_uf_colada(bruto)
    if obtido == esperado:
        print(f"  ok   {bruto[:40]:42} -> {obtido!r}")
    else:
        falhas += 1
        print(f"  ERRO {bruto[:40]:42} -> {obtido!r}, esperado {esperado!r}")

print("\nCorrigir a redação NÃO pode criar duplicata:")
# A chave do id tem que ignorar o rótulo que sobrou na frente. Ao
# limpar "e Câmara de Siqueira Campos" para "Siqueira Campos", o id
# mudava e o mesmo concurso passava a ocupar DOIS cards — 6 pares de
# uma vez (21/09/2026). A chave precisa sobreviver à melhoria do
# extrator, não só às diferenças entre fontes.
from extrair import _chave_cidade

for antiga, nova in [
    ("e Câmara de Siqueira Campos", "Siqueira Campos"),
    ("e Câmara de Nísia Floresta", "Nísia Floresta"),
    ("e Câmara de Portão", "Portão"),
    ("SANTANA DE PIRAPAMA", "Santana de Pirapama"),
    ("PONTA PORA MS", "Ponta Porã"),
    ("Município de Trindade", "Trindade"),
    ("Prefeitura Municipal de Limeira", "Limeira"),
    # As duas fontes escrevem del-Rei com caixa diferente
    ("SÃO JOÃO DEL-REI", "São João del-Rei"),
    ("São João Del-Rei", "São João del-Rei"),
]:
    if _chave_cidade(antiga) == _chave_cidade(nova):
        print(f"  ok   {antiga[:32]:34} == {nova}")
    else:
        falhas += 1
        print(f"  ERRO {antiga[:32]:34} != {nova}  "
              f"({_chave_cidade(antiga)!r} / {_chave_cidade(nova)!r})")

print("\nMas cidades diferentes continuam separadas:")
# Fundir é pior que duplicar: some um concurso de verdade e ninguém vê.
for a, b in [
    ("Conceição da Barra de Minas", "Conceição do Mato Dentro"),
    ("Santana de Pirapama", "Santana do Livramento"),
    ("Portão", "Porto Calvo"),
    ("Trindade", "Trombas"),
]:
    if _chave_cidade(a) != _chave_cidade(b):
        print(f"  ok   {a[:30]:32} != {b}")
    else:
        falhas += 1
        print(f"  ERRO {a[:30]:32} colidiu com {b}")

print(f"\n{falhas} falha(s)")
sys.exit(1 if falhas else 0)
