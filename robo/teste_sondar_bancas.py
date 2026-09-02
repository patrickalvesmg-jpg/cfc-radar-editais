# -*- coding: utf-8 -*-
"""Testes do robo/sondar_bancas.py — sem rede, sobre casos REAIS achados
na auditoria manual de 01/09/2026.

Cada caso aqui é um falso positivo ou falso negativo que passou pela
primeira versão do script e só foi pego revendo os 10 achados brutos
um a um, abrindo cada página. Sem estes testes, uma futura edição do
regex de recência pode reintroduzir qualquer um deles em silêncio.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import sondar_bancas as sb

# Textos reais (resumidos) dos 4 casos que motivaram a lógica atual.
CURITIBANOS_2018 = (
    "IVAN FRANÇA MOREIRA, PRESIDENTE DA CÂMARA DE VEREADORES DE "
    "CURITIBANOS, TORNA PÚBLICO que realizará CONCURSO PÚBLICO. "
    "Inscrições de 08/01/2018 - 14:00:00 a 06/02/2018 - 23:59:59."
)

CONCORDIA_ATUAL = (
    "Câmara Municipal de Concórdia/SC - Ed. 01/26. CONCURSO PÚBLICO "
    "para Contador do quadro permanente da Câmara. Inscrições: das "
    "06h do dia 19/08 às 18h do dia 18/09/2026."
)

UEL_JA_ENCERRADO = (
    "PSS UEL - CONTADOR / PEDAGOGO (EDUCAÇÃO ESPECIAL). Edital PRORH "
    "nº 155/2026 - Convocação para Avaliação Médica 18/05/2026 (10h). "
    "Resultado da Análise dos Laudos Médicos 14/05/2026. Edital PRORH "
    "nº 154/2026 - Resultado Final. Edital nº 101/2026 - Homologação "
    "de Inscrições 19/03/2026."
)

SEFAZ_AL = "SEFAZ/AL abre oportunidades para Auditor Fiscal da Administração Tributária Estadual"


def teste_concurso_de_2018_nao_passa():
    """O card genérico de Curitibanos não tinha ano nenhum — só a
    página de detalhe revelava 2018. `parece_concurso_atual` sozinho
    já pega isso quando o texto tem o ano explícito."""
    assert sb.parece_concurso_atual(CURITIBANOS_2018) is False


def teste_concurso_atual_passa():
    assert sb.parece_concurso_atual(CONCORDIA_ATUAL) is True
    assert sb.parece_ainda_aberto(CONCORDIA_ATUAL) is True


def teste_processo_ja_encerrado_nao_passa_mesmo_com_ano_atual():
    """O caso que faltava na v1: o texto TINHA "2026" e "inscrições",
    então `parece_concurso_atual` sozinho dizia True — mas era sobre
    HOMOLOGAÇÃO de inscrições já fechadas e RESULTADO FINAL, não
    abertura. É por isso que existe uma segunda checagem separada."""
    assert sb.parece_concurso_atual(UEL_JA_ENCERRADO) is True  # tem ano e "inscrições"
    assert sb.parece_ainda_aberto(UEL_JA_ENCERRADO) is False   # mas já encerrou


def teste_texto_sem_ano_nenhum_e_aceito():
    """Nem toda página cita o ano por extenso — sem nenhum ano no
    texto, não dá para provar que é velho, então aceita (a decisão
    final ainda passa pela confirmação na página de detalhe)."""
    assert sb.parece_concurso_atual("Concurso público. Inscrições abertas.") is True


def teste_dedup_acha_concurso_ja_capturado_por_cidade():
    """IBAM/Concórdia: real e aberto, mas o PCI já tinha capturado.
    Usa o data/editais.json de verdade do projeto — teste de
    integração leve, não isolado, porque o objetivo é justamente
    verificar contra o acervo real."""
    chaves = sb._chaves_dos_editais_existentes()
    assert sb._ja_no_radar(chaves, CONCORDIA_ATUAL) is True


def teste_dedup_acha_concurso_ja_capturado_por_orgao():
    chaves = sb._chaves_dos_editais_existentes()
    assert sb._ja_no_radar(chaves, SEFAZ_AL) is True


def teste_dedup_nao_acha_cidade_inventada():
    """A palavra genérica sozinha ("Contador", "Concurso", "Prefeitura")
    NÃO pode contar como acerto — foi o primeiro bug da função de
    dedup: um texto sobre uma cidade totalmente inventada batia como
    "já no radar" só por causa do vocabulário comum de edital."""
    chaves = sb._chaves_dos_editais_existentes()
    texto = "Prefeitura de Alguma Cidade Nova Nunca Vista abre concurso para Contador"
    assert sb._ja_no_radar(chaves, texto) is False


def teste_dedup_com_texto_vazio_nao_quebra():
    chaves = sb._chaves_dos_editais_existentes()
    assert sb._ja_no_radar(chaves, "") is False
    assert sb._ja_no_radar(set(), CONCORDIA_ATUAL) is False


def teste_palavra_generica_nao_conta_como_especifica():
    for termo in ("CONTADOR", "CONCURSO", "PREFEITURA", "EDITAL"):
        assert termo in sb._PALAVRA_GENERICA, f"{termo} deveria estar na lista genérica"


if __name__ == "__main__":
    testes = [v for k, v in sorted(globals().items()) if k.startswith("teste_")]
    falhas = 0
    for t in testes:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except AssertionError as e:
            falhas += 1
            print(f"  FALHA {t.__name__}: {e}")
    print(f"\n{len(testes) - falhas} de {len(testes)} passaram")
    raise SystemExit(1 if falhas else 0)
