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

PADRAO_CONTABIL = re.compile(
    r"\bcontador(?:es|a)?\b"
    r"|\bcontabilidade\b"
    r"|ci[êe]ncias\s+cont[áa]beis"
    r"|t[ée]cnico.{0,20}contabilidade"
    r"|auditor.{0,30}(?:fiscal|controle|interno|governamental)"
    r"|anal(?:ista|ítico).{0,30}cont[áa]b"
    r"|fiscal.{0,20}(?:tributos|receita|renda)"
    r"|controlador(?:ia)?\s+(?:interno|geral)",
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
