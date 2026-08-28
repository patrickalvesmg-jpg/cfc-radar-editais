# -*- coding: utf-8 -*-
"""Testes do salário por cargo. Sem rede: os trechos são reais,
copiados dos editais e das matérias que investigamos."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import salario

# ANEXO I do concurso de São João del-Rei (IBGP), texto real do PDF.
ANEXO_DEL_REI = (
    "330 - AGENTE FISCAL DE SANEAMENTO Ensino Médio Completo. 40 horas "
    "semanais 04 01 05 R$ 2.693,37 331 - ASSISTENTE ADMINISTRATIVO Ensino "
    "Médio Completo. 40 horas semanais 02 00 02 R$ 2.693,37 "
    "ENSINO MÉDIO/TÉCNICO COMPLETO 404 - TÉCNICO EM CONTABILIDADE Ensino "
    "Médio Completo e Curso Técnico de Contabilidade e registro no Conselho "
    "Regional competente (CRC). 40 horas semanais 01 00 01 R$ 2.693,37 "
    "405 - TÉCNICO EM QUÍMICA Ensino Médio Completo e Curso Técnico em "
    "Quimica. 25 horas semanais 01 00 01 R$ 1.683,36"
)

# Coromandel: Contador e Controlador Interno no MESMO edital.
ANEXO_COROMANDEL = (
    "CONTADOR Superior em Ciências Contábeis e registro no CRC. 40 horas "
    "semanais 01 00 01 R$ 4.562,82 "
    "CONTROLADOR INTERNO Superior. 40 horas semanais 01 00 01 R$ 7.821,98"
)

# Matéria do PCI: só a faixa, e o teto é de outro cargo.
MATERIA_CORONEL = (
    "A jornada semanal varia entre 20 e 44 horas, conforme o cargo, com "
    "remuneração inicial de R$ 2.565,32 a R$ 21.525,56. As inscrições "
    "estarão abertas... As taxas variam de R$ 100,00 a R$ 150,00."
)


def test_pega_o_salario_do_cargo_certo():
    assert salario.do_texto(ANEXO_DEL_REI, "Técnico Em Contabilidade") == 2693.37


def test_distingue_cargos_contabeis_do_mesmo_edital():
    """O radar mostrava R$ 7.822 para o Contador de Coromandel — que é
    o vencimento do Controlador Interno."""
    assert salario.do_texto(ANEXO_COROMANDEL, "Contador") == 4562.82
    assert salario.do_texto(ANEXO_COROMANDEL, "Controlador Interno") == 7821.98


def test_tolera_diferenca_de_redacao():
    """O acervo diz 'Técnico De Contabilidade'; o PDF, 'TÉCNICO EM
    CONTABILIDADE'."""
    assert salario.do_texto(ANEXO_DEL_REI, "Técnico De Contabilidade") == 2693.37


def test_piso_da_faixa_em_vez_do_teto():
    """Sem valor por cargo, o piso — nunca o teto, que é do médico."""
    assert salario.piso_da_faixa(MATERIA_CORONEL) == 2565.32


def test_faixa_ignora_taxa_de_inscricao():
    """'de R$ 100,00 a R$ 150,00' é taxa: abaixo do mínimo."""
    assert salario.piso_da_faixa("As taxas variam de R$ 100,00 a R$ 150,00.") is None


def test_resolver_prefere_o_exato():
    v, obs = salario.resolver("Contador", ANEXO_COROMANDEL, MATERIA_CORONEL)
    assert (v, obs) == (4562.82, "")


def test_resolver_cai_para_o_piso():
    v, obs = salario.resolver("Contador", "", MATERIA_CORONEL)
    assert (v, obs) == (2565.32, "a partir de")


def test_resolver_sem_dado_nao_inventa():
    assert salario.resolver("Contador", "", "") == (None, "")


def test_nao_confunde_taxa_com_salario():
    """Na Objetivas a tabela é CÓD./VAGA/ESCOLARIDADE/TAXA — o valor ao
    lado do Contador é a taxa de inscrição."""
    tabela = "Contador - - Vide Edital R$ 243,80 Controlador Interno - - Vide Edital R$ 243,80"
    assert salario.do_texto(tabela, "Contador") is None





# --- escolha do PDF (regressão de Coronel Vivida) -------------------

def test_descarta_anexo_de_isencao():
    """'ANEXO ÚNICO ... ISENÇÃO' não tem salário. Guardá-lo deixou o
    Contador de Coronel Vivida com os R$ 21.525 da manchete."""
    import aprofundar
    pdfs = [
        ("https://x/isencao.pdf",
         "ANEXO ÚNICO DO EDITAL N.° 02.001/2026 - DEFERIMENTO DAS SOLICITAÇÕES DE ISENÇÃO"),
        ("https://x/abertura.pdf",
         "EDITAL DE ABERTURA N.º 001/2026 - CP PM CORONEL VIVIDA - PR"),
    ]
    assert aprofundar._melhor_pdf(pdfs) == "https://x/abertura.pdf"


def test_prefere_anexo_de_vencimentos():
    import aprofundar
    pdfs = [
        ("https://x/edital.pdf", "EDITAL DE ABERTURA N.º 01/2026"),
        ("https://x/anexo1.pdf", "ANEXO I - CARGO, ESCOLARIDADE E VENCIMENTO INICIAL"),
    ]
    assert aprofundar._melhor_pdf(pdfs) == "https://x/anexo1.pdf"


# --- valor sem "R$" (auditoria de 28/08/2026) ----------------------

# Anexo de Cachoeira do Sul: a coluna traz o cifrão só no cabeçalho.
TABELA_SEM_CIFRAO = (
    "G02 Contador Ensino Superior completo e habilitacao legal para "
    "exercicio da profissao de Contador 40h 01+CR 01 - - 4.486,69 243,80 "
    "G01 Controlador Interno Possuir, no minimo, 21 anos"
)


def test_le_valor_sem_cifrao():
    """O card mostrava R$ 19.535 porque o extrator exigia 'R$' e a
    tabela não usa."""
    assert salario.do_texto(TABELA_SEM_CIFRAO, "Contador") == 4486.69


def test_nao_pesca_numero_solto_quando_ha_cifrao():
    """Com 'R$' na janela, número solto não vale: seria nota de prova,
    número de lei, percentual."""
    texto = "Contador 40h 10 questoes 7,50 pontos R$ 4.000,00"
    assert salario.do_texto(texto, "Contador") == 4000.00


def test_valor_solto_exige_formato_de_dinheiro():
    """'7,50' e '40' não são salário — sem milhar com ponto, ignora."""
    texto = "Contador 40h nota minima 7,50 aprovados 40"
    assert salario.do_texto(texto, "Contador") is None


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
