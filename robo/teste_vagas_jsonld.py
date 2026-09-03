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
    assert vagas != "658", "pci_api também não pode pescar vaga do JSON-LD"
