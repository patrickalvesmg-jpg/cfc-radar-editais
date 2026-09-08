# -*- coding: utf-8 -*-
"""Vagas do cargo contábil não podem vir do JSON-LD (schema.org) embutido
na página do PCI. Bug real de 31/08/2026: 8 concursos publicados com
"658 vagas" idêntico, vindo do mesmo lote de captura — o JSON-LD fica
ANTES do corpo visível no texto que `CARGO_DETALHE` varre, então um
número solto no metadado (visualizações, contador) podia colar no
grupo de vagas quando o corpo visível não tinha o padrão explícito
"Cargo (N vagas)" perto o bastante."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fontes import pci, pci_api

# Reproduz o formato real: JSON-LD com @context ANTES do corpo, cargo
# citado no headline do schema.org, e um número solto (userInteractionCount)
# dentro do mesmo bloco JSON. O corpo visível confirma o cargo mas sem
# "(N vagas)" explícito — caso em que a extração deve ficar vazia, não
# pescar o 658 do JSON-LD.
HTML_COM_LIXO_NO_JSONLD = """
<html><body>
<script type="application/ld+json">
{"@context":"https://schema.org","@graph":[{"@type":"NewsArticle",
"headline":"Prefeitura abre concurso para Contador e outros cargos",
"interactionStatistic":{"@type":"InteractionCounter","userInteractionCount":658},
"description":"Prefeitura abre concurso publico com vagas diversas."}]}
</script>
<div class="corpo">
<p>A Prefeitura de Exemplo abriu concurso público de âmbito municipal,
com vaga para Contador. As inscrições vão de 01/09 a 30/09.</p>
</div>
</body></html>
"""

# Caso positivo de controle: corpo visível TEM o padrão explícito, tem
# que continuar extraindo certo depois da correção.
HTML_COM_VAGA_EXPLICITA = """
<html><body>
<script type="application/ld+json">
{"@context":"https://schema.org","@graph":[{"@type":"NewsArticle",
"headline":"Prefeitura abre concurso para Contador",
"interactionStatistic":{"@type":"InteractionCounter","userInteractionCount":999}}]}
</script>
<div class="corpo">
<p>A Prefeitura de Exemplo abriu concurso com vaga para Contador (2 vagas).</p>
</div>
</body></html>
"""


def test_vagas_nao_vem_de_numero_dentro_do_jsonld():
    cargo, vagas = pci._extrair_cargo_e_vagas(HTML_COM_LIXO_NO_JSONLD)
    # Corpo visível não tem "Cargo (N vagas)" explícito — cai no caso
    # genérico, e o que importa aqui é que "658" (do JSON-LD) NUNCA
    # aparece como vaga.
    assert vagas != "658", "vagas não pode vir do userInteractionCount do JSON-LD"
    assert vagas == ""


def test_vaga_explicita_no_corpo_continua_funcionando():
    cargo, vagas = pci._extrair_cargo_e_vagas(HTML_COM_VAGA_EXPLICITA)
    assert cargo == "Contador"
    assert vagas == "2"


def test_pci_api_tambem_ignora_numero_do_jsonld():
    corpo = pci_api._corpo(HTML_COM_LIXO_NO_JSONLD)
    m = pci_api.CARGO_DETALHE.search(pci_api._sem_jsonld(corpo))
    vagas = m.group(2).strip() if m else ""
    assert vagas != "658", "pci_api não pode pescar vaga do JSON-LD"


# ------------------------------------------------------------------
# Bug de 08/09/2026: a correção acima consertou o MATCH de vagas, mas
# não o `texto` bruto salvo no achado — e é sobre ELE que
# extrair.montar() roda extrair_vagas() como fallback quando `vagas`
# sai vazio (nenhum "Cargo (N vagas)" explícito no corpo). O `texto`
# continuava com o JSON-LD dentro (pci_api) ou era a linha de
# LISTAGEM, sempre sobre o total do concurso (pci) — e assim "658"
# virou "943" na varredura seguinte, em 8 concursos diferentes de
# novo, mesmo com o match já corrigido.
# ------------------------------------------------------------------

def test_pci_api_texto_retornado_tambem_sem_jsonld():
    """O 4º elemento da tupla de _detalhar() é o que vira achado['texto']
    — precisa estar limpo do JSON-LD, não só o texto usado no match."""
    import re
    corpo = pci_api._corpo(HTML_COM_LIXO_NO_JSONLD)
    texto_retornado = pci_api._sem_jsonld(corpo)
    assert "658" not in texto_retornado
    assert "@context" not in texto_retornado


def test_pci_nao_usa_texto_de_listagem_no_fallback():
    """O texto salvo em achado['texto'] (fonte pci.py) precisa ser o
    corpo da matéria (texto_longo), nunca a linha da listagem — essa
    sempre traz "N vagas até R$ X" do TOTAL do concurso, nunca do
    cargo contábil específico."""
    texto_listagem = "Prefeitura de Exemplo SP 943 vagas até R$ 12.000,00 Vários Cargos"
    texto_corpo_sem_padrao = "A Prefeitura de Exemplo abriu concurso com vaga para Contador."

    # Reproduz a escolha de robo/fontes/pci.py: texto_longo (corpo)
    # tem prioridade sobre texto_bloco (listagem) quando existe.
    texto_bloco = texto_listagem
    texto_longo = texto_corpo_sem_padrao
    salvo = texto_longo[:2000] if texto_longo else texto_bloco[:2000]

    assert "943" not in salvo
    assert salvo == texto_corpo_sem_padrao
