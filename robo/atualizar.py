# -*- coding: utf-8 -*-
"""
CFC ACADEMY · RADAR CONCURSOS CONTABILIDADE — varredura diária.

    python robo/atualizar.py [--dias N] [--dry-run]

Junta o que as fontes acharam com o que já está publicado e grava
data/editais.json. Não publica sozinho: quem publica é o Pull Request
aberto pelo GitHub Actions, depois da sua revisão.

REGRA CENTRAL: correção humana nunca é desfeita pelo robô.
"""

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

# O console do Windows usa cp1252 por padrão e quebra ao imprimir acento
# ou seta. Sem isto, um print de log derruba a varredura inteira.
for _fluxo in (sys.stdout, sys.stderr):
    try:
        _fluxo.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, str(Path(__file__).parent))

from fontes import (bancas, cebraspe, consulplan, estrategia,  # noqa: E402
                    ibgp, pci_api,
                    fafipa, pci,
                    portais_wp, querido_diario)
import editorial      # noqa: E402
import organizadoras  # noqa: E402
import extrair                                # noqa: E402

# Fontes ativas. Cada uma expõe coletar() e devolve achados brutos.
# Acrescentar fonte aqui é a única mudança necessária para ampliar a
# varredura — o resto do pipeline não muda.
FONTES = (
    ("CEBRASPE (banca)", cebraspe.coletar),
    ("Fundação FAFIPA (banca)", fafipa.coletar),
    ("Bancas em plataforma comum", bancas.coletar),
    ("Consulplan (conselhos de contabilidade)", consulplan.coletar),
    # A API do IBGP dá o cargo por extenso, o que permite separar
    # "Auditor de Controle Interno - Ciências Contábeis" de
    # "... - Engenharia Civil" no mesmo concurso.
    ("IBGP Concursos (API da banca)", ibgp.coletar),
    # A API do PCI substitui a raspagem de 27 páginas de cargo:
    # 1 requisição, 493 concursos, cargo em lista e data ISO.
    ("PCI Concursos (API)", pci_api.coletar),
    ("Portais WordPress (agregadores)", portais_wp.coletar),
    ("Querido Diário (diários municipais)", querido_diario.coletar),
)

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO = RAIZ / "data" / "editais.json"

# Campos que o robô extrai mal e o humano costuma corrigir à mão.
# Uma vez revisado, o robô não encosta mais neles.
CAMPOS_CURADOS = (
    "cargo", "cidade", "salario", "salarioObs", "vagas", "dataProva",
    "taxaInscricao", "cargaHoraria", "banca", "uf",
)


def carregar_existentes() -> list[dict]:
    if not ARQUIVO.exists():
        return []
    try:
        return json.loads(ARQUIVO.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        # Melhor abortar que sobrescrever um arquivo bom com lixo.
        sys.exit(f"ERRO: {ARQUIVO} está corrompido ({e}). Nada foi alterado.")


def status_por_prazo(edital: dict) -> str:
    """Reavalia o status pela data — um edital aberto ontem pode ter
    encerrado hoje, e ninguém vai corrigir isso à mão todo dia."""
    if edital.get("revisado") and edital.get("status") == "previsto":
        return "previsto"

    fim = edital.get("inscricaoFim")
    if not fim:
        return edital.get("status") or "previsto"

    try:
        dias = (date.fromisoformat(fim[:10]) - date.today()).days
    except ValueError:
        return edital.get("status") or "previsto"

    if dias < 0:
        return "encerrado"
    if dias <= 7:
        return "encerrando"
    return "aberto"


def mesclar(existentes: list[dict], novos: list[dict]) -> tuple[list[dict], int, int]:
    """Funde as duas listas preservando a curadoria.

    Devolve (lista_final, quantidade_nova, quantidade_atualizada).
    """
    por_id = {e["id"]: e for e in existentes if e.get("id")}
    novos_ct = atualizados_ct = 0

    for novo in novos:
        atual = por_id.get(novo["id"])

        if atual is None:
            novo["revisado"] = False
            por_id[novo["id"]] = novo
            novos_ct += 1
            continue

        if atual.get("revisado"):
            # Já passou por olho humano: só deixamos o robô mexer no que
            # é puramente temporal. Sobrescrever aqui apagaria o trabalho
            # de revisão a cada execução.
            #
            # ÚNICA exceção: preencher o link de inscrição quando ele
            # ainda não existe. É acréscimo, não substituição — um edital
            # revisado sem link fica inútil para quem quer se inscrever,
            # e o dado pode ter aparecido numa fonte descoberta depois.
            # Campos que são ACRÉSCIMO, nunca substituição: preenchemos
            # quando ainda não existem. Um edital revisado sem link de
            # inscrição ou sem o PDF fica inútil para quem quer se
            # inscrever, e esse dado pode ter surgido numa fonte
            # descoberta depois da revisão.
            for campo in ("siteInscricao", "pdfEdital"):
                if not atual.get(campo) and novo.get(campo):
                    atual[campo] = novo[campo]
                    atualizados_ct += 1
            continue

        mudou = False
        for campo, valor in novo.items():
            if campo in ("id", "revisado"):
                continue
            # Não troca informação existente por vazio.
            if valor in ("", 0, None) and atual.get(campo) not in ("", 0, None):
                continue
            if atual.get(campo) != valor:
                atual[campo] = valor
                mudou = True
        if mudou:
            atualizados_ct += 1

    final = list(por_id.values())
    for e in final:
        e["status"] = status_por_prazo(e)

    # Mais recentes primeiro; o front reordena conforme a escolha do usuário.
    final.sort(key=lambda e: e.get("capturadoEm", ""), reverse=True)
    return final, novos_ct, atualizados_ct


def geolocalizar(editais: list[dict], geo: dict, municipios: dict) -> None:
    """Coloca lat/long em cada edital, para o mapa poder posicioná-lo.

    Quatro tentativas, da mais precisa para a menos:
      1. órgão + UF batendo com o cadastro do mapa do Estratégia;
      2. cidade (extraída do nome do órgão) na base do IBGE;
      3. cidade no cadastro do Estratégia;
      4. capital do estado — melhor um ponto no estado certo que nenhum.

    O campo `geoAprox` marca o caso 4, para a interface poder dizer que a
    posição é aproximada em vez de fingir precisão.
    """
    orgaos, cidades = geo.get("orgaos", {}), geo.get("cidades", {})

    for e in editais:
        if e.get("lat") and e.get("lon"):
            continue

        uf = (e.get("uf") or "").upper()
        if not uf:
            continue

        # A cidade costuma estar embutida no nome do órgão
        # ("Prefeitura de Limeira" -> Limeira). Preenchemos o campo, que
        # também melhora o que o site exibe no card.
        if not e.get("cidade"):
            cidade = estrategia.nome_cidade(e.get("orgao"))
            if cidade:
                e["cidade"] = cidade

        alvo = orgaos.get(f"{estrategia._chave(e.get('orgao'))}|{uf}")
        if alvo:
            e["lat"], e["lon"] = alvo["lat"], alvo["lon"]
            e["geoAprox"] = False
            if not e.get("cidade") and alvo.get("cidade"):
                e["cidade"] = alvo["cidade"]
            continue

        chave_cidade = estrategia._chave(e.get("cidade") or e.get("orgao"))

        ponto = municipios.get(f"{chave_cidade}|{uf}")
        if ponto:
            e["lat"], e["lon"] = ponto
            e["geoAprox"] = False
            continue

        ponto = cidades.get(f"{chave_cidade}|{uf}")
        if ponto:
            e["lat"], e["lon"] = ponto
            e["geoAprox"] = False
            continue

        capital = estrategia.CAPITAIS.get(uf)
        if capital:
            e["lat"], e["lon"] = capital
            e["geoAprox"] = True


def main() -> int:
    ap = argparse.ArgumentParser(description="Varredura de editais contábeis")
    ap.add_argument("--limite", type=int, default=25,
                    help="resultados por consulta em cada fonte (padrão: 25)")
    ap.add_argument("--dry-run", action="store_true",
                    help="mostra o resultado sem gravar o arquivo")
    args = ap.parse_args()

    print(f"Radar Concursos Contabilidade — varredura de {datetime.now():%d/%m/%Y %H:%M}\n")

    achados: list[dict] = []
    for nome, coletar in FONTES:
        print(f"  {nome}")
        try:
            achados.extend(coletar(args.limite))
        except Exception as e:
            # Falha de uma fonte não pode quebrar a varredura inteira:
            # isto roda sem supervisão e portal fora do ar é rotina.
            print(f"    fonte falhou: {type(e).__name__}: {e}")

    print(f"\n  Candidatos após filtro: {len(achados)}")

    novos = [extrair.montar(a) for a in achados]

    # Coordenadas para o mapa. Fonte separada porque o Estratégia informa
    # a ÁREA do concurso, nunca o cargo — não serve para criar edital,
    # mas é o único lugar com lat/long pronta.
    print("\n  Geolocalização (Radar do Estratégia)")
    try:
        geo = estrategia.coletar_geo()
    except Exception as e:
        print(f"    falhou: {type(e).__name__}: {e}")
        geo = {"orgaos": {}, "cidades": {}}

    existentes = carregar_existentes()
    municipios = estrategia.coletar_municipios()
    geolocalizar(novos + existentes, geo, municipios)
    final, ct_novos, ct_atualizados = mesclar(existentes, novos)

    revisados = sum(1 for e in final if e.get("revisado"))
    pendentes = [e for e in final if not e.get("revisado")]

    print(f"\n  Novos:       {ct_novos}")
    print(f"  Atualizados: {ct_atualizados}")
    print(f"  Total:       {len(final)}  ({revisados} revisados, {len(pendentes)} pendentes)")

    if pendentes:
        print("\n  Aguardando revisão:")
        for e in pendentes[:10]:
            print(f"    [{e['confianca']:5}] {e['orgao'][:52]} — {e['cargo'][:34]}")

    if args.dry_run:
        print("\n  (dry-run — nada gravado)")
        return 0

    if ct_novos == 0 and ct_atualizados == 0:
        print("\n  Nada mudou. Arquivo intacto.")
        return 0

    n_ed = editorial.aplicar(final)
    print(f"  Editoriais: {n_ed}")

    organizadoras.vincular(final)
    organizadoras.gravar_catalogo(final)

    ARQUIVO.write_text(
        json.dumps(final, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\n  Gravado: {ARQUIVO.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
