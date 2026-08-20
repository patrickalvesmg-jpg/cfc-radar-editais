# -*- coding: utf-8 -*-
"""
Confere o acervo ANTES de ele ir ao ar.

    python robo/conferir.py

Existe porque a varredura passou a publicar sozinha (decisão do Patrick,
ago/2026). Sem revisor humano, alguém precisa segurar o que não pode ser
publicado — e esse alguém é este arquivo.

Sai com código 1 quando encontra problema, o que faz o passo do GitHub
Actions falhar e o site permanecer como estava. **Um dia desatualizado é
melhor que um dia errado**: quem lê o site decide se vai estudar meses
para um concurso com base no que está aqui.

As regras abaixo não são estilo — cada uma nasceu de um erro real,
anotado no comentário.
"""

import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

for _fluxo in (sys.stdout, sys.stderr):
    try:
        _fluxo.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO = RAIZ / "data" / "editais.json"

# Agregadores concorrentes. Regra INEGOCIÁVEL do produto: o site nunca
# manda o visitante para outra plataforma de concurso.
AGREGADOR = re.compile(
    r"pciconcursos|jcconcursos|concursosnobrasil|folhadirigida"
    r"|qconcursos|grancursos|estrategiaconcursos|acheconcursos",
    re.I,
)

# O cargo precisa ter alguma marca contábil. Amplo de propósito: aqui a
# pergunta é "isto tem cara de vaga contábil?", não "qual é o cargo".
CONTABIL = re.compile(
    r"cont[áa]b|contador|tribut|fiscal|control|tesour|or[çc]ament"
    r"|financ|custos|auditor|fazend|receita|arrecad|er[áa]ri",
    re.I,
)

# Cargo que declara formação e ela NÃO é contábil. Caso real: Contagem/MG
# abriu cinco "Auditor de Controle Interno" — Ciências Contábeis, Direito,
# Engenharia Civil, TI e Contador. Três não são vaga contábil.
ESPECIALIDADE_ERRADA = re.compile(
    r"-\s*(?:direito|engenharia|tecnologia|inform[áa]tica|arquitet"
    r"|medicina|enferm|psicolog|pedagog|nutri|odontolog|veterin)"
    r"|saneamento|sanit[áa]ri|tr[âa]nsito|vigil[âa]ncia",
    re.I,
)

UFS = {
    "AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT",
    "PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO",
}


def _chave(texto: str) -> str:
    plano = unicodedata.normalize("NFD", texto or "")
    plano = plano.encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", plano).strip()


def conferir(editais: list[dict]) -> list[str]:
    """Devolve a lista de problemas encontrados. Vazia = pode publicar."""
    problemas: list[str] = []

    if not editais:
        return ["o arquivo está VAZIO — a varredura provavelmente falhou"]

    # Queda brusca de acervo é sinal de fonte quebrada, não de mercado
    # parado. Concurso não some de um dia para o outro.
    if len(editais) < 40:
        problemas.append(
            f"só {len(editais)} editais — abaixo do mínimo razoável (40). "
            "Provável falha de fonte, não escassez real."
        )

    hoje = date.today()
    vistos: dict[str, str] = {}

    for e in editais:
        ident = f"{e.get('orgao', '?')[:40]} — {e.get('cargo', '?')[:28]}"

        # 1. Link para concorrente. O erro mais grave: entrega a
        #    audiência a quem disputa o mesmo público.
        for campo in ("siteInscricao", "pdfEdital", "bancaDominio", "editalUrl"):
            valor = e.get(campo) or ""
            if valor and AGREGADOR.search(valor):
                problemas.append(f"[{ident}] {campo} aponta para AGREGADOR: {valor}")

        # 2. Cargo não-contábil. Já aconteceu: a barra lateral do PCI
        #    citava "Contador" e vagas de psicólogo passavam no filtro.
        cargo = e.get("cargo") or ""
        if not cargo.strip():
            problemas.append(f"[{ident}] sem cargo")
        elif not CONTABIL.search(cargo):
            problemas.append(f"[{ident}] cargo NÃO parece contábil: {cargo!r}")
        elif ESPECIALIDADE_ERRADA.search(cargo):
            problemas.append(f"[{ident}] especialidade não-contábil: {cargo!r}")

        # 3. Prazo. Publicar edital vencido como aberto é o erro que
        #    mais prejudica quem usa o site.
        fim = e.get("inscricaoFim") or ""
        if not fim:
            problemas.append(f"[{ident}] sem data de fim de inscrição")
        else:
            try:
                d_fim = date.fromisoformat(fim[:10])
                if d_fim < hoje and e.get("status") != "encerrado":
                    problemas.append(
                        f"[{ident}] inscrição terminou em {fim[:10]} "
                        f"mas o status é {e.get('status')!r}"
                    )
            except ValueError:
                problemas.append(f"[{ident}] data de fim inválida: {fim!r}")

        # 3b. Encerrado NÃO deve ser publicado, mesmo com o status
        #     correto. O acervo é vitrine de oportunidade: quem abre o
        #     site quer saber onde ainda dá para se inscrever. Cinco
        #     escaparam na primeira publicação automática, porque o
        #     descarte era feito à mão e não havia mais mão nenhuma.
        if e.get("status") == "encerrado":
            problemas.append(f"[{ident}] status 'encerrado' — não deve ir ao ar")

        # 4. UF — sem ela o edital some do mapa.
        uf = (e.get("uf") or "").upper()
        if not uf:
            problemas.append(f"[{ident}] sem UF")
        elif uf not in UFS:
            problemas.append(f"[{ident}] UF inexistente: {uf!r}")

        # 5. Duplicata. O id vem de cidade+uf+cargo+prazo; dois iguais
        #    significam bug no id, e o candidato veria dois cards do
        #    mesmo concurso sem saber qual abrir.
        ident_id = e.get("id") or ""
        if not ident_id:
            problemas.append(f"[{ident}] sem id")
        elif ident_id in vistos:
            problemas.append(f"[{ident}] id DUPLICADO ({ident_id}) — já usado por {vistos[ident_id]}")
        else:
            vistos[ident_id] = ident

    return problemas


def main() -> int:
    if not ARQUIVO.exists():
        print(f"ERRO: {ARQUIVO} não existe.")
        return 1

    try:
        editais = json.loads(ARQUIVO.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erro:
        print(f"ERRO: {ARQUIVO} não é JSON válido ({erro}).")
        return 1

    problemas = conferir(editais)

    print(f"Conferindo {len(editais)} editais...\n")

    if not problemas:
        print("Tudo certo. Pode publicar.")
        return 0

    print(f"{len(problemas)} PROBLEMA(S) — publicação abortada:\n")
    for p in problemas[:40]:
        print(f"  · {p}")
    if len(problemas) > 40:
        print(f"  ... e mais {len(problemas) - 40}")

    print(
        "\nO site NÃO foi atualizado e continua com o conteúdo anterior.\n"
        "Corrija a fonte ou o filtro e rode de novo."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
