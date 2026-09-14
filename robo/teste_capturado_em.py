# -*- coding: utf-8 -*-
"""`capturadoEm` é quando o edital ENTROU no radar, e não muda mais.

Bug real de 14/09/2026: `extrair.montar()` grava a hora de agora a
cada passagem, e o `mesclar()` deixava isso sobrescrever o registro
existente. Resultado: todo edital ainda listado pela fonte "nascia"
de novo toda semana, e o filtro "Novos concursos" mostrou 93 quando
só 26 eram novos de fato.

Quem foi visto pela última vez agora é `vistoEm`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from atualizar import mesclar


def _existente(**extra):
    base = {
        "id": "e-teste", "cargo": "Contador", "salario": 4000.0,
        "inscricaoFim": "2026-12-31", "revisado": False,
        "capturadoEm": "2026-08-31T10:00:00",
    }
    base.update(extra)
    return base


def test_capturado_em_nao_muda_em_edital_que_ja_existia():
    novo = {"id": "e-teste", "cargo": "Contador", "inscricaoFim": "2026-12-31",
            "capturadoEm": "2026-09-14T09:00:00"}
    final, _, _ = mesclar([_existente()], [novo])
    assert final[0]["capturadoEm"] == "2026-08-31T10:00:00"


def test_visto_em_registra_a_passagem_mais_recente():
    """Saber que a fonte ainda publica o edital continua sendo útil —
    só não pode ser confundido com novidade."""
    novo = {"id": "e-teste", "cargo": "Contador", "inscricaoFim": "2026-12-31",
            "capturadoEm": "2026-09-14T09:00:00"}
    final, _, _ = mesclar([_existente()], [novo])
    assert final[0]["vistoEm"] == "2026-09-14T09:00:00"


def test_edital_novo_de_verdade_mantem_a_data_da_captura():
    novo = {"id": "e-outro", "cargo": "Contador", "inscricaoFim": "2026-12-31",
            "capturadoEm": "2026-09-14T09:00:00"}
    final, qtd_novos, _ = mesclar([], [novo])
    assert qtd_novos == 1
    assert final[0]["capturadoEm"] == "2026-09-14T09:00:00"


def test_prazo_e_outros_campos_continuam_atualizando():
    """A trava é só da data de entrada — o resto tem de acompanhar a
    fonte, senão uma prorrogação nunca apareceria."""
    novo = {"id": "e-teste", "cargo": "Contador", "inscricaoFim": "2027-03-15",
            "banca": "Nova Banca", "capturadoEm": "2026-09-14T09:00:00"}
    final, _, _ = mesclar([_existente()], [novo])
    assert final[0]["inscricaoFim"] == "2027-03-15"
    assert final[0]["banca"] == "Nova Banca"
    assert final[0]["capturadoEm"] == "2026-08-31T10:00:00"
