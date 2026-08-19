# -*- coding: utf-8 -*-
"""
CFC ACADEMY · RADAR DE EDITAIS — configuração do robô de captura.

Ponto único de calibração da varredura. Ajustar os termos aqui muda o que
entra no radar, sem tocar no código das fontes.
"""

import re

# ------------------------------------------------------------------
# Identificação
# ------------------------------------------------------------------
# Um User-Agent honesto: diz quem somos e como nos contatar. Vários
# portais bloqueiam clientes anônimos, e esconder a identidade seria
# tanto ineficaz quanto desleal com quem hospeda os dados.
USER_AGENT = (
    "CFCRadarEditais/1.0 (+https://patrickalvesmg-jpg.github.io/cfc-radar-editais/; "
    "contato via GitHub issues) Python-urllib"
)

CABECALHOS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Accept-Encoding": "gzip, deflate",
}

# Intervalo entre requisições ao MESMO host, em segundos.
# Não é opcional: varredura diária não justifica sobrecarregar
# servidor público mantido com dinheiro de imposto.
PAUSA_ENTRE_REQUISICOES = 1.5

TIMEOUT = 45


# ------------------------------------------------------------------
# Filtro de relevância — duas camadas obrigatórias
# ------------------------------------------------------------------
# Validado contra 2.834 publicações reais do DOU (07/08/2026): filtrar
# só por "contador" trazia licitação, extrato de contrato e resultado de
# julgamento. O texto precisa indicar CONCURSO **e** ÁREA CONTÁBIL.

PADRAO_CONCURSO = re.compile(
    r"concurso p[úu]blico"
    r"|processo seletivo"
    r"|sele[çc][ãa]o p[úu]blica"
    r"|edital\s+de\s+abertura",
    re.I,
)

# É da área contábil? Além do núcleo (contador, ciências contábeis),
# inclui os cargos que exigem ou aceitam essa formação: controle
# interno e externo, tributos, orçamento, tesouraria.
#
# Cargo adjacente (economista, escriturário) NÃO entra aqui de
# propósito: sozinho ele não indica vaga contábil. Quem decide nesse
# caso é o `_confirmar_cargo` da fonte, que lê a página de detalhe.
PADRAO_CONTABIL = re.compile(
    r"\bcontador(?:es|a)?\b"
    r"|\bcontabilidade\b"
    r"|\bcontabilista\b"
    r"|ci[êe]ncias\s+cont[áa]beis"
    r"|t[ée]cnico.{0,20}contabilidade"
    r"|(?:auxiliar|assistente|analista).{0,12}cont[áa]b\w*"
    r"|auditor.{0,30}(?:fiscal|controle|interno|governamental|p[úu]blico)"
    r"|controlador.{0,16}interno"
    r"|(?:analista|t[ée]cnico|oficial|assistente).{0,24}controle\s+(?:interno|externo)"
    r"|fiscal.{0,20}(?:tributos?|receita|rendas?|arrecada[çc][ãa]o)"
    r"|agente.{0,16}(?:tributos?|arrecada[çc][ãa]o|fiscal)"
    r"|analista\s+tribut[áa]rio"
    r"|(?:analista|t[ée]cnico).{0,20}(?:or[çc]ament\w+|financ\w+|custos?)"
    r"|\btesoureiro(?:a)?\b",
    re.I,
)

# Descartados sempre — publicações que citam "contador" mas não são vaga.
#
# Duas famílias de ruído, ambas observadas em dados reais:
#  1. compras públicas (licitação, contrato) — citam "contador" no objeto;
#  2. ATOS DE CONCURSO JÁ EXISTENTE — convocação, nomeação, homologação
#     de resultado. São o falso positivo mais traiçoeiro: têm as palavras
#     "concurso público" E "contador", mas a inscrição fechou há meses.
#     Publicar isso como oportunidade aberta enganaria o candidato.
PADRAO_RUIDO = re.compile(
    # compras e contratos
    r"aviso de licita"
    r"|extrato de (?:contrato|termo|acordo|conv[êe]nio|dispensa)"
    r"|resultado de julgamento"
    r"|dispensa de licita"
    r"|inexigibilidade"
    r"|tomada de pre[çc]os"
    r"|preg[ãa]o\s+(?:eletr[ôo]nico|presencial)"
    r"|ata de registro de pre"
    r"|aviso de homologa"
    # atos posteriores à inscrição
    r"|edital\s+de\s+convoca[çc][ãa]o"
    r"|convoca[çc][ãa]o\s+(?:de|do|dos|da)?\s*candidat"
    r"|edital\s+de\s+nomea[çc][ãa]o"
    r"|portaria\s+de\s+nomea[çc][ãa]o"
    r"|homologa[çc][ãa]o\s+do\s+resultado"
    r"|resultado\s+(?:final|definitivo|preliminar)"
    r"|classifica[çc][ãa]o\s+final"
    r"|lista\s+de\s+(?:inscritos|aprovados|classificados)"
    r"|prorroga[çc][ãa]o\s+de\s+(?:prazo\s+de\s+)?validade"
    r"|candidat[oa]s?\s+aprovad",
    re.I,
)


# Marca de que o documento ABRE inscrição, e não apenas fala de concurso.
# Sem isto, entram acórdãos de tribunal de contas que *determinam* a
# realização de concurso, atas de sessão e contratação de serviços
# contábeis — todos citam "concurso público" e "cargo de contador".
# Medido: de 34 achados em diários municipais, ZERO tinham período de
# inscrição e 18 eram de mais de 180 dias atrás.
PADRAO_ABERTURA = re.compile(
    r"edital\s+(?:de\s+)?(?:abertura|de\s+concurso)"
    r"|torna\s+p[úu]blic\w+\s+a\s+abertura"
    r"|abertura\s+(?:das\s+)?inscri[çc][õo]es"
    r"|estar[ãa]o\s+abertas\s+as\s+inscri[çc][õo]es"
    r"|as\s+inscri[çc][õo]es\s+(?:estar[ãa]o|ser[ãa]o|poder[ãa]o)"
    r"|per[íi]odo\s+de\s+inscri[çc][õo]es"
    r"|inscri[çc][õo]es\s+(?:de|no\s+per[íi]odo|a\s+partir)",
    re.I,
)

# Documentos que só CITAM concurso, sem abrir vaga.
#
# Inclui os atos de ENCERRAMENTO, que são o falso positivo mais comum
# nos diários municipais: uma homologação ou nomeação sempre menciona o
# "Edital de Abertura" que a originou, então passa pela marca positiva.
# Casos reais capturados: Sarutaiá/SP (homologação) e Marília/SP
# (nomeação de candidata classificada em 6º lugar).
PADRAO_NAO_ABERTURA = re.compile(
    # pareceres e contas
    r"ac[óo]rd[ãa]o"
    r"|julgou\s+regulares"
    r"|contas\s+anuais"
    r"|determinando\s+ao\s+(?:atual\s+)?gestor"
    r"|realize.{0,40}concurso\s+p[úu]blico"
    r"|no\s+prazo\s+de\s+\d+\s*\(?\w*\)?\s*dias\s*,?\s*concurso"
    r"|presta[çc][ãa]o\s+de\s+contas"
    r"|contrata[çc][ãa]o\s+de\s+servi[çc]os"
    r"|sess[ãa]o\s+(?:ordin[áa]ria|plen[áa]ria)"
    # atos de encerramento do certame
    r"|homologa[çc][ãa]o\s+do\s+concurso"
    r"|torna\s+p[úu]blica\s+a\s+homologa"
    r"|\bNOMEIA\b"
    r"|nomeia,?\s+em\s+car[áa]ter\s+efetivo"
    r"|classificad[oa]\s+em\s+\d+"
    r"|prorroga[çc][ãa]o\s+(?:de\s+posse|do\s+prazo\s+de\s+validade)"
    r"|conclus[ãa]o\s+dos\s+trabalhos"
    r"|prazos?\s+recursa\w+",
    re.I,
)


def eh_abertura(texto: str) -> bool:
    """Distingue 'concurso está abrindo' de 'documento fala de concurso'.

    Exigimos marca positiva de abertura E ausência de marca de outro tipo
    de ato. Sem esta camada o site se enche de oportunidades que não
    existem — inclusive de anos atrás.
    """
    if PADRAO_NAO_ABERTURA.search(texto):
        return False
    return bool(PADRAO_ABERTURA.search(texto))


def eh_relevante(texto: str, titulo: str = "") -> bool:
    """Aplica as três camadas. Conservador de propósito: é melhor perder
    um edital (o revisor humano completa) do que publicar lixo como se
    fosse concurso — o site é lido por quem depende da informação.

    O ruído é procurado no texto inteiro, não só no título: nos diários
    municipais o documento não tem título próprio, e a natureza do ato
    ('EDITAL DE CONVOCAÇÃO') aparece no corpo.
    """
    if PADRAO_RUIDO.search(f"{titulo} {texto}"):
        return False
    return bool(PADRAO_CONCURSO.search(texto) and PADRAO_CONTABIL.search(texto))


# ------------------------------------------------------------------
# Normalização
# ------------------------------------------------------------------
UFS = {
    "AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT",
    "PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO",
}

# Bancas conhecidas → forma canônica, para não termos "CEBRASPE",
# "Cespe/Cebraspe" e "CESPE" como três bancas diferentes no filtro.
BANCAS = {
    "cebraspe": "CESPE/CEBRASPE",
    "cespe": "CESPE/CEBRASPE",
    "fgv": "FGV",
    "fcc": "FCC",
    "vunesp": "VUNESP",
    "ibfc": "IBFC",
    "quadrix": "Quadrix",
    "aocp": "AOCP",
    "idecan": "IDECAN",
    "consulplan": "Consulplan",
    "fundatec": "FUNDATEC",
    "instituto access": "Instituto Access",
    "avancasp": "AvançaSP",
    "objetiva": "Objetiva Concursos",
    "fepese": "FEPESE",
    "comperve": "COMPERVE",
    "fumarc": "FUMARC",
    "ibade": "IBADE",
    "selecon": "SELECON",
    "legalle": "Legalle",
    "unifil": "UNIFIL",
}
