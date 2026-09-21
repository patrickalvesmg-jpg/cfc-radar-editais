# -*- coding: utf-8 -*-
"""
Fonte: PCI Concursos — API JSON.

`https://www.pciconcursos.com.br/api/v1/concursos` devolve **todos os
concursos abertos do país numa única requisição** (493 na medição de
19/08/2026), com o dado já estruturado:

    titulo · cargos[] · vagas_salario · formacao · uf.sigla · cidade
    datas.inicio / datas.fim (ISO) · status · noticia.uri

Substitui a varredura de 27 páginas `/vagas/{slug}`:
  · 1 requisição em vez de 27 + ~150 páginas de detalhe
  · superconjunto do que a raspagem via — contém 436/436 de /concursos/
  · `cargos` é lista real, não texto: precisão de 100% na amostra,
    contra o rótulo genérico "Vários Cargos" que a raspagem produzia

Permitido pelo robots.txt (`/api/` não está entre os caminhos vetados).

LIMITE: metade dos registros vem como "Vários Cargos" — a API não
detalha o cargo nesses. Para eles abrimos a matéria e confirmamos, que
é o mesmo trabalho de antes, só que sobre um universo bem menor.
"""

import json
import re

from config import PADRAO_CONTABIL, area_alheia
from http_util import buscar

API = "https://www.pciconcursos.com.br/api/v1/concursos"
MATERIA = "https://www.pciconcursos.com.br/noticias/{uri}"

TAG = re.compile(r"<[^>]+>")

# Cargo contábil na lista `cargos[]` da API.
CARGO_CONTABIL = re.compile(
    r"contador|contabilidade|contabilista|ci[êe]ncias\s+cont[áa]beis"
    r"|cont[áa]bil|auditor|controlador|controle\s+(?:interno|externo)"
    r"|fiscal\s+de\s+(?:tributos?|rendas?|arrecada[çc][ãa]o)"
    r"|tesoureiro|tribut[áa]rio",
    re.I,
)

# Quando a API não detalha ("Vários Cargos"), abrimos a matéria.
GENERICO = re.compile(r"v[áa]rios\s+cargos|diversos\s+cargos", re.I)

# Só o corpo da matéria: a barra lateral de notícias relacionadas
# (class="nXXXXX") cita "Contador" em quase toda página e aprovaria
# qualquer concurso — testado, 4 de 4 vagas de psicólogo passavam.
SIDEBAR = re.compile(r'class="n\d{5,}"')

# Cargo + vagas no corpo: "Contador (1 vaga + CR)".
CARGO_DETALHE = re.compile(
    r"((?:t[ée]cnico\s+(?:em|de)\s+contabilidade"
    r"|(?:auxiliar|assistente|analista)\s+(?:de\s+)?cont[áa]b\w*"
    r"|contador(?:a)?|contabilista"
    r"|auditor[\w\s]{0,26}?(?:cont[áa]b\w*|fiscal|interno|p[úu]blico)"
    r"|controlador[\w\s]{0,14}?interno"
    r"|(?:fiscal|agente)[\w\s]{0,14}?(?:de\s+)?(?:tributos?|rendas?|arrecada[çc][ãa]o)"
    r"|tesoureiro(?:a)?))"
    r"\s*\(([^)]{0,40})\)",
    re.I,
)

# O domínio da banca no texto ("as inscrições são no site X").
#
# A lista de terminações era fechada em org/com/net/gov/edu, e isso
# deixava de fora banca hospedada em domínio novo: a Câmara de Ibirama
# inscreve em `portal.sctreinamentos.selecao.site` e o edital saía SEM
# LINK NENHUM, o que esconde o card do site inteiro (achado em
# 14/09/2026 — 15 dos 31 editais novos ficaram invisíveis assim).
#
# Agora aceita qualquer terminação de 2 a 12 letras e subdomínio de
# vários níveis. O que impede lixo não é mais a lista de TLDs: é o
# DOMINIO_PROIBIDO logo abaixo, que barra agregador e rede social.
SITE_OFICIAL = re.compile(
    r"(?:pelo|no|atrav[ée]s do|por meio do)\s+(?:site|endere[çc]o|portal)\s+"
    r"((?:https?://)?(?:[\w-]+\.){1,4}[a-z]{2,12}(?:\.br)?)",
    re.I,
)
DOMINIO_PROIBIDO = re.compile(
    r"pciconcursos|schema\.org|pci\.app\.br|google|facebook|whatsapp"
    r"|instagram|twitter|youtube|linkedin|leaflet|unpkg|chatgpt"
    # Infraestrutura da própria página, não banca: o fallback de "pega
    # qualquer link externo" mandava o candidato para o servidor de
    # fontes do Google (achado em 14/09/2026 — 11 editais receberam
    # fonts.gstatic.com como "site de inscrição").
    r"|gstatic|googleapis|cloudflare|jsdelivr|bootstrapcdn|jquery"
    r"|fontawesome|cdnjs|/wp-content/|/wp-includes/|adsbygoogle"
    r"|doubleclick|googletagmanager|concursosnobrasil|jcconcursos"
    r"|folhadirigida|qconcursos|grancursos|estrategiaconcursos",
    re.I,
)

# Documento LEGÍTIMO do processo seletivo, mas nunca o edital em si —
# link para um desses não pode virar "a página do concurso". Achado
# em 08/09/2026: UFPE mandava para "baixar_noticia.php?id=..." que
# era o resultado de isenção de taxa (lista com CPF de candidatos),
# não o edital — o card levava quem clicasse a um documento errado.
CAMINHO_NAO_E_EDITAL = re.compile(
    r"isen[çc][ãa]o|resultado|convoca[çc][ãa]o|recurso|gabarito"
    r"|homologa[çc][ãa]o|classifica[çc][ãa]o"
    # Tela de login / área do candidato: quem chega ali não vê o
    # concurso, vê um formulário de senha. O portal da banca é sempre
    # melhor destino — de lá a pessoa acha o certame. Achado pelo
    # Patrick em 14/09/2026: a CPCON/UEPB entrava como
    # `sistemas.cpcon.uepb.edu.br/sigeps-app/login` em vez de
    # `cpcon.uepb.edu.br`. O pci.py já barrava isso em _e_util; aqui
    # faltava.
    r"|/login|/entrar|/acesso|area[-_]?do[-_]?candidato|minha[-_]?conta"
    r"|/cadastr|/inscricao/novo",
    re.I,
)


def _corpo(html: str) -> str:
    return re.sub(r"\s+", " ", TAG.sub(" ", SIDEBAR.split(html)[0]))


# O JSON-LD (schema.org) vem ANTES do corpo no HTML da matéria, com
# headline, contador de interações e outros números sem relação com
# vaga nenhuma. CARGO_DETALHE rodando sobre o texto com o JSON-LD ainda
# dentro puxava esse lixo para o grupo de vagas — foi assim que "658"
# (contador do JSON-LD, não vaga) saiu idêntico em 8 concursos de
# estados diferentes na mesma varredura (31/08/2026). Ver mesma
# correção em fontes/pci.py.
JSONLD = re.compile(r'\{"@context".*?\}\]\}', re.S)


def _sem_jsonld(texto: str) -> str:
    return re.sub(r"\s+", " ", JSONLD.sub(" ", texto)).strip()


def _salario(texto: str) -> float:
    """Maior valor plausível de remuneração citado."""
    valores = []
    for bruto in re.findall(r"R\$\s*([\d.]+(?:,\d{2})?)", texto or ""):
        try:
            v = float(bruto.replace(".", "").replace(",", "."))
        except ValueError:
            continue
        if 1_000 <= v <= 100_000:
            valores.append(v)
    return max(valores) if valores else 0.0


def _site_inscricao(texto: str, html: str) -> str:
    """Endereço para onde mandar o candidato.

    Preferimos a página do concurso; o site da banca é o plano B.
    Decisão do Patrick (14/09/2026): quando não achamos a página
    específica, vale mandar para a home da banca — de lá a pessoa
    encontra o concurso. Ficar SEM LINK é pior, porque o card some do
    site (a regra de "beco sem saída" esconde quem não tem para onde
    ir), e o concurso deixa de existir para quem procura.
    """
    externos = [u for u in dict.fromkeys(re.findall(r'href="(https?://[^"]+)"', html))
                if not DOMINIO_PROIBIDO.search(u) and not CAMINHO_NAO_E_EDITAL.search(u)]

    # 1ª escolha: o link já aponta para a página do certame.
    for u in externos:
        if re.search(r"/(?:concurso|edital|informacoes|processo)", u, re.I):
            return u

    # 2ª escolha: o domínio citado no texto ("inscrições no site X").
    m = SITE_OFICIAL.search(texto)
    if m and not DOMINIO_PROIBIDO.search(m.group(1)):
        alvo = m.group(1)
        return alvo if alvo.startswith("http") else f"https://{alvo}"

    # 3ª escolha: qualquer link externo da matéria que tenha cara de
    # banca. Prefere o que NÃO é site de prefeitura (.gov.br costuma
    # ser o órgão, que raramente hospeda a inscrição).
    naogov = [u for u in externos if ".gov.br" not in u.lower()]
    for u in (naogov or externos):
        return u

    return ""


def _detalhar(uri: str, cargo_api: str) -> tuple | None:
    """Abre a matéria para confirmar cargo e pegar link. None = descarta."""
    html = buscar(MATERIA.format(uri=uri))
    if not html:
        return None

    texto = _corpo(html)
    if not PADRAO_CONTABIL.search(texto):
        return None

    m = CARGO_DETALHE.search(_sem_jsonld(texto))
    if m:
        cargo = re.sub(r"\s+", " ", m.group(1)).strip().title()
        vagas = re.sub(r"\s*vagas?\s*", " ", m.group(2), flags=re.I).strip()
    elif GENERICO.search(cargo_api):
        # Termo contábil no corpo mas sem "Cargo (n vagas)": não dá para
        # afirmar qual é a vaga. Descartamos — card sem cargo não ajuda.
        return None
    else:
        cargo, vagas = cargo_api.strip().title(), ""

    # O cargo pode declarar uma área que não é a nossa. "Auditor-Fiscal
    # Agropecuário/Médico Veterinário" casa em PADRAO_CONTABIL por
    # "auditor...fiscal", mas é inspeção sanitária animal.
    #
    # Esta checagem existia SÓ no conferir.py, e o efeito foi um loop
    # diário: o robô capturava, a conferência barrava, a publicação
    # falhava, e chegava e-mail de erro todo dia sem nada mudar.
    # Filtrar na captura corta o problema na origem.
    if area_alheia(cargo):
        return None

    # O `texto` retornado aqui vira o achado["texto"] salvo — e é sobre
    # ELE que extrair.montar() roda o fallback extrair_vagas() quando
    # `vagas` sai vazio daqui (nenhum "Cargo (N vagas)" explícito no
    # corpo). Devolver o texto AINDA COM o JSON-LD reabriu exatamente o
    # mesmo bug do "658"/"943": o fallback pescava um número solto do
    # metadado como se fosse vaga. `vagas` sozinho não bastava corrigir
    # — o texto bruto salvo também precisa estar limpo.
    return cargo, vagas, _site_inscricao(texto, html), _sem_jsonld(texto)


def coletar(_limite: int = 0) -> list[dict]:
    corpo = buscar(API)
    if not corpo:
        print("    API indisponível")
        return []

    try:
        dados = json.loads(corpo).get("data") or []
    except json.JSONDecodeError:
        print("    resposta não-JSON")
        return []

    print(f"    {len(dados)} concursos na API")

    achados: list[dict] = []
    abertos = 0
    for c in dados:
        datas = c.get("datas") or {}
        fim = (datas.get("fim") or "")[:10]
        if not fim:
            continue
        abertos += 1

        cargos = c.get("cargos") or []
        texto_cargos = " ".join(cargos)
        uri = (c.get("noticia") or {}).get("uri") or ""
        if not uri:
            continue

        # A API já diz o cargo? Então só confirmamos os que interessam.
        # Se vier genérico, precisamos abrir para saber.
        tem_contabil = bool(CARGO_CONTABIL.search(texto_cargos))
        if not tem_contabil and not GENERICO.search(texto_cargos):
            continue

        cargo_api = next(
            (x for x in cargos if CARGO_CONTABIL.search(x)), texto_cargos
        )
        det = _detalhar(uri, cargo_api)
        if not det:
            continue
        cargo, vagas, site, texto = det

        uf = (c.get("uf") or {}).get("sigla") or ""
        cidade = (c.get("cidade") or {}).get("nome") or ""
        formacao = (c.get("formacao") or "").lower()
        escolaridade = "medio" if ("superior" not in formacao
                                   and ("médio" in formacao or "técnico" in formacao)) else "superior"

        achados.append({
            "fonte": "PCI Concursos",
            "fonte_tipo": "pci_api",
            "titulo": c.get("titulo", ""),
            "orgao_bruto": c.get("titulo", ""),
            "texto": texto[:4000],
            "url": "",
            "_procedencia": MATERIA.format(uri=uri),
            "_site_inscricao": site,
            "_cargo": cargo,
            "_vagas": vagas,
            "_uf": uf,
            "_cidade": cidade,
            "_salario": _salario(c.get("vagas_salario", "") or texto),
            "_inscricao_inicio": (datas.get("inicio") or "")[:10],
            "_inscricao_fim": fim,
            "_escolaridade": escolaridade,
            "_confianca": "alta" if (fim and vagas) else "media",
        })
        print(f"      {c.get('titulo','')[:44]:44} {cargo[:24]}")

    print(f"    {abertos} com prazo · {len(achados)} contábeis confirmados")
    return achados
