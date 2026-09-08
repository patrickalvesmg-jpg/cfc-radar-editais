# -*- coding: utf-8 -*-
"""O salário lido do ANEXO não pode ser desfeito pela varredura.

Bug real de 08/09/2026: a varredura semanal sobrescreveu com a
manchete do PCI ("salários de até R$ 19.535") o valor que o
aprofundar.py já tinha lido do PDF (Contador de Cachoeira do Sul,
R$ 4.486,69). Como o aprofundamento roda com `--pendentes` e não
revisita quem já tem PDF, o erro ficava publicado a semana inteira.
Foram 5 regressões numa varredura só.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from atualizar import mesclar


def _existente(**extra):
    base = {
        "id": "e-teste", "cargo": "Contador", "salario": 4486.69,
        "salarioObs": "", "pdfEdital": "https://banca.org.br/anexo.pdf",
        "inscricaoFim": "2026-12-31", "revisado": False,
    }
    base.update(extra)
    return base


def test_salario_do_pdf_sobrevive_a_manchete_da_varredura():
    """Com pdfEdital preenchido, a varredura não mexe no salário."""
    novo = {"id": "e-teste", "cargo": "Contador", "salario": 19535.28,
            "inscricaoFim": "2026-12-31"}
    final, _, _ = mesclar([_existente()], [novo])
    assert final[0]["salario"] == 4486.69


def test_sem_pdf_a_varredura_ainda_atualiza_o_salario():
    """Sem PDF não há o que proteger — o dado da fonte é o melhor que
    temos, e recusá-lo deixaria o card desatualizado para sempre."""
    novo = {"id": "e-teste", "cargo": "Contador", "salario": 5000.0,
            "inscricaoFim": "2026-12-31"}
    final, _, _ = mesclar([_existente(pdfEdital="", salario=3000.0)], [novo])
    assert final[0]["salario"] == 5000.0


def test_outros_campos_continuam_atualizando_mesmo_com_pdf():
    """A trava é só do salário: prazo, banca e afins têm de continuar
    acompanhando a fonte, senão uma prorrogação nunca apareceria."""
    novo = {"id": "e-teste", "cargo": "Contador", "salario": 19535.28,
            "inscricaoFim": "2027-03-15", "banca": "Nova Banca"}
    final, _, _ = mesclar([_existente()], [novo])
    assert final[0]["salario"] == 4486.69
    assert final[0]["inscricaoFim"] == "2027-03-15"
    assert final[0]["banca"] == "Nova Banca"
