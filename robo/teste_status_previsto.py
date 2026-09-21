# -*- coding: utf-8 -*-
"""Edital publicado cuja inscrição ainda não abriu é "previsto".

Bug real de 14/09/2026: `status_por_prazo` só olhava o FIM do prazo,
então concurso que abre daqui a 20 dias entrava como "aberto" — e a
aba "Previstos" do site ficava permanentemente vazia, mesmo com a
API do PCI trazendo 84 concursos nessa situação.

A virada para "aberto" tem de acontecer sozinha no dia em que a
inscrição abre, sem ninguém mexer à mão.
"""
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from atualizar import status_por_prazo

HOJE = date.today()


def _edital(dias_para_abrir, dias_para_fechar, **extra):
    e = {
        "inscricaoInicio": (HOJE + timedelta(days=dias_para_abrir)).isoformat(),
        "inscricaoFim": (HOJE + timedelta(days=dias_para_fechar)).isoformat(),
    }
    e.update(extra)
    return e


def test_inscricao_que_ainda_vai_abrir_e_prevista():
    assert status_por_prazo(_edital(20, 50)) == "previsto"


def test_vira_aberto_no_dia_em_que_a_inscricao_abre():
    """Sem intervenção manual: no dia D o início deixa de ser futuro."""
    assert status_por_prazo(_edital(0, 30)) == "aberto"


def test_inscricao_ja_aberta_continua_aberta():
    assert status_por_prazo(_edital(-10, 30)) == "aberto"


def test_perto_do_fim_e_encerrando():
    assert status_por_prazo(_edital(-10, 3)) == "encerrando"


def test_prazo_vencido_e_encerrado():
    assert status_por_prazo(_edital(-40, -1)) == "encerrado"


def test_previsto_nao_engole_quem_esta_encerrando():
    """Quem já abriu e está perto do fim não pode virar previsto por
    causa de um início mal preenchido no passado."""
    assert status_por_prazo(_edital(-30, 5)) == "encerrando"


def test_sem_data_de_inicio_usa_so_o_fim():
    """Fonte que não informa início não pode travar tudo em previsto."""
    e = {"inscricaoFim": (HOJE + timedelta(days=30)).isoformat()}
    assert status_por_prazo(e) == "aberto"
