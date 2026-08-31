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

# Cargo que declara área e ela NÃO é contábil. A regra vive em
# config.py para que fonte e conferência usem EXATAMENTE a mesma —
# duas listas separadas divergem com o tempo, e aí o que a fonte deixa
# passar a conferência não pega (ou o contrário).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import area_alheia   # noqa: E402
from extrair import id_estavel  # noqa: E402

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
        elif area_alheia(cargo):
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

        # 3b. Encerrado PODE ir ao ar desde 21/08/2026: o site tem aba
        #     própria para eles, e um edital fechado mostra que aquela
        #     prefeitura abre concurso contábil.
        #
        #     O que ainda barramos é o MUITO antigo — passados 2 anos, o
        #     registro não serve nem como referência, e sua presença
        #     indica que o corte por idade em `atualizar.py` falhou.
        if fim:
            try:
                if date.fromisoformat(fim[:10]) < hoje.replace(year=hoje.year - 2):
                    problemas.append(
                        f"[{ident}] inscrição de {fim[:10]} — mais de 2 anos, "
                        "deveria ter saído no corte por idade"
                    )
            except ValueError:
                pass

        # 4. UF — sem ela o edital some do mapa.
        uf = (e.get("uf") or "").upper()
        if not uf:
            problemas.append(f"[{ident}] sem UF")
        elif uf not in UFS:
            problemas.append(f"[{ident}] UF inexistente: {uf!r}")

        # 5. Duplicata. Conferimos de DUAS formas, porque a primeira
        #    sozinha deixou passar quatro cards repetidos no ar.
        ident_id = e.get("id") or ""
        if not ident_id:
            problemas.append(f"[{ident}] sem id")
        elif ident_id in vistos:
            problemas.append(f"[{ident}] id DUPLICADO ({ident_id}) — já usado por {vistos[ident_id]}")
        else:
            vistos[ident_id] = ident

        # 5b. Id que NÃO corresponde ao próprio conteúdo.
        #
        #     O id sai de cidade+uf+cargo+prazo. Quando essa fórmula
        #     mudou, os registros gravados antes ficaram órfãos: o robô
        #     não os reconhece na recaptura e cria um segundo registro
        #     do mesmo concurso, com id novo. O teste de id repetido
        #     não pega isso — os dois ids são diferentes.
        #
        #     Foi assim que Câmara de Belo Jardim e Prefeitura de Santos
        #     apareceram duplicadas no site.
        esperado = id_estavel(
            e.get("cidade", ""), e.get("uf", ""),
            e.get("cargo", ""), e.get("inscricaoFim", ""),
        )
        if ident_id and ident_id != esperado:
            problemas.append(
                f"[{ident}] id {ident_id} não corresponde ao conteúdo "
                f"(esperado {esperado}) — registro de esquema antigo, "
                "vai duplicar na próxima captura"
            )

        # 6. Link malformado.
        #
        #    `bancaDominio` chegou a valer "net.br" — sufixo, não
        #    domínio — e o site montava https://net.br/, que não
        #    existe. Domínio precisa de nome E sufixo.
        dom = (e.get("bancaDominio") or "").strip()
        if dom:
            if re.match(r"^(com|net|org|gov|edu)\.br$", dom, re.I) or "." not in dom:
                problemas.append(
                    f"[{ident}] bancaDominio '{dom}' não é domínio — "
                    "o link da organizadora vai quebrar"
                )

        #    Link de inscrição sem esquema não abre em lugar nenhum.
        for campo in ("siteInscricao", "pdfEdital"):
            url = (e.get(campo) or "").strip()
            if url and not url.startswith(("http://", "https://")):
                problemas.append(
                    f"[{ident}] {campo} sem http(s): '{url[:50]}'"
                )

        # 7. Salário implausível para a escolaridade.
        #
        #    Floresta/PE publicava "Fiscal de Tributos — R$ 15.005,27".
        #    O cargo é de ENSINO MÉDIO e ganha R$ 1.688,08; os R$ 15 mil
        #    eram do Médico UBS do mesmo edital. Erro de 8,9x, com
        #    `confianca: alta` e sem PDF nenhum.
        #
        #    Cargo de nível médio com salário alto é sinal, não prova:
        #    o TCE-GO paga R$ 11.862,19 a Técnico de Controle Externo, e
        #    a própria matéria diz "cargos de nível médio". Barrar isso
        #    seria trocar um erro por outro.
        #
        #    O que separa os dois casos é a ESFERA. Tribunal de contas,
        #    assembleia e órgão federal pagam bem a nível médio; uma
        #    PREFEITURA pagando R$ 15 mil a fiscal é teto de médico.
        #    Por isso a regra vale só para o municipal, e só sem PDF —
        #    com anexo lido, confiamos no que lemos.
        sal = e.get("salario") or 0
        tem_pdf = bool((e.get("pdfEdital") or "").strip())
        if (sal > 10000 and e.get("escolaridade") == "medio"
                and e.get("nivel") == "municipal" and not tem_pdf):
            problemas.append(
                f"[{ident}] R$ {sal:,.2f} para cargo de nível médio em concurso "
                "municipal, sem PDF conferido — provável salário de outro cargo"
            )

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
