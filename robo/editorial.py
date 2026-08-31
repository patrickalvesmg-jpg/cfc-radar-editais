# -*- coding: utf-8 -*-
"""
Editorial do edital — texto de apoio na página do concurso.

Transforma os campos capturados num artigo curto que ajuda o candidato a
decidir: quem contrata, o que o cargo exige, quanto paga em relação aos
demais do radar, quanto tempo resta e como será a seleção.

REGRAS QUE NÃO SE QUEBRAM:
  · só afirma o que está nos dados — nada de "grande chance de aprovação"
    ou "concorrência baixa", que seriam palpite nosso;
  · dado ausente não vira "não informado": a frase simplesmente não sai;
  · a comparação de salário usa a MEDIANA do próprio acervo, e o texto
    diz isso — não é média de mercado.

Gerado no robô (não no navegador) para ficar no JSON, indexável por
buscador e idêntico para todos os leitores.
"""

from datetime import date

_MEDIANA = {"valor": 0.0}


def preparar(editais):
    """Mediana salarial do acervo — base da comparação.

    Só entram salários LIDOS NO ANEXO (`pdfEdital` preenchido). Os
    demais vêm da manchete da fonte, que anuncia o teto do concurso —
    o do médico, o do procurador. Incluí-los inflava a própria régua
    contra a qual comparamos cada edital: a mediana ficava alta e um
    salário contábil correto parecia "abaixo da mediana".
    """
    valores = sorted(e["salario"] for e in editais
                     if e.get("salario") and (e.get("pdfEdital") or "").strip())
    if valores:
        meio = len(valores) // 2
        _MEDIANA["valor"] = (
            valores[meio] if len(valores) % 2
            else (valores[meio - 1] + valores[meio]) / 2
        )


def _brl(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _data_br(iso):
    if not iso:
        return ""
    a, m, d = iso[:10].split("-")
    return f"{d}/{m}/{a}"


def _dias(iso):
    try:
        return (date.fromisoformat(iso[:10]) - date.today()).days
    except (ValueError, TypeError):
        return None


# Concordância do artigo com o nome do órgão: "A Prefeitura", "O
# Município", "A Câmara". Sem isto o texto saía "O Prefeitura de X".
_FEMININOS = (
    "prefeitura", "câmara", "camara", "secretaria", "fundação", "fundacao",
    "universidade", "autarquia", "agência", "agencia", "companhia",
    "empresa", "assembleia", "defensoria", "procuradoria", "controladoria",
)


def _artigo(orgao: str) -> str:
    """Nome do órgão precedido do artigo correto."""
    nome = (orgao or "").strip()
    if not nome:
        return "O órgão"
    primeira = nome.split()[0].lower()
    # Sigla (TCE, IPREM, CRC) fica sem artigo: "TCE MA abriu concurso".
    if nome.split()[0].isupper() and len(nome.split()[0]) <= 6:
        return nome
    return f"{'A' if primeira in _FEMININOS else 'O'} {nome}"


def _abertura(e):
    esferas = {
        "municipal": " de âmbito municipal",
        "estadual": " de âmbito estadual",
        "federal": " de âmbito federal",
    }
    txt = f"{_artigo(e.get('orgao',''))} abriu concurso público"
    txt += esferas.get(e.get("nivel", ""), "")

    local = " / ".join(x for x in (e.get("cidade"), e.get("uf")) if x)
    if local:
        txt += f", em {local}"
    txt += f", com vaga para <b>{e.get('cargo','').strip()}</b>"

    vagas = str(e.get("vagas") or "").strip()
    if vagas:
        alto = vagas.upper()
        if alto in ("CR", "CADASTRO DE RESERVA"):
            txt += ". A oferta é para cadastro de reserva"
        elif "CR" in alto:
            n = alto.replace("+ CR", "").replace("CR", "").strip()
            if n:
                txt += f". São {n} vaga(s) imediata(s) mais cadastro de reserva"
        else:
            txt += f". São {vagas} vaga(s)"
    return txt + "."


def _remuneracao(e):
    sal = e.get("salario") or 0
    if not sal:
        return ""

    # Sem `pdfEdital` não abrimos o anexo: o número veio da manchete da
    # fonte, que anuncia o TETO do concurso — quase sempre de outro
    # cargo. Em Floresta/PE o editorial dizia "chega a R$ 15.005,27" e
    # ainda concluía "acima da mediana"; o Fiscal de Tributos ganha
    # R$ 1.688,08 e os R$ 15 mil eram do Médico UBS. Escrever isso por
    # extenso é pior que no card: é a frase que a pessoa lê e acredita.
    verificado = bool((e.get("pdfEdital") or "").strip())

    if verificado:
        txt = f"A remuneração do cargo é de <b>{_brl(sal)}</b>"
    else:
        txt = f"A remuneração divulgada para o concurso é de <b>{_brl(sal)}</b>"
    carga = (e.get("cargaHoraria") or "").strip()
    if carga:
        txt += f", para jornada de {carga}"
    txt += "."

    if not verificado:
        txt += (" Esse valor ainda não foi conferido no anexo de vencimentos"
                " e pode ser de outro cargo do mesmo edital — confirme antes"
                " de se inscrever.")

    # A comparação com a mediana só faz sentido sobre valor verificado:
    # comparar um teto de outro cargo com a mediana dá uma conclusão
    # confiante sobre um número errado.
    med = _MEDIANA["valor"]
    if med and verificado:
        if sal >= med * 1.35:
            txt += " É um valor acima da mediana dos concursos contábeis hoje no radar"
        elif sal <= med * 0.7:
            txt += " O valor fica abaixo da mediana dos concursos contábeis hoje no radar"
        else:
            txt += " O valor está em linha com a mediana dos concursos contábeis hoje no radar"
        txt += f" ({_brl(med)})."

    if e.get("salarioObs"):
        txt += f" {e['salarioObs']}."
    return txt


def _prazo(e):
    fim = e.get("inscricaoFim")
    if not fim:
        return ("O período de inscrição ainda não foi confirmado. "
                "Acompanhe o edital oficial para não perder a abertura.")

    inicio = e.get("inscricaoInicio")
    if inicio:
        txt = f"As inscrições vão de {_data_br(inicio)} a <b>{_data_br(fim)}</b>"
    else:
        txt = f"As inscrições seguem até <b>{_data_br(fim)}</b>"

    d = _dias(fim)
    if d is not None:
        if d < 0:
            txt += ". O prazo já encerrou"
        elif d == 0:
            txt += " — <b>hoje é o último dia</b>"
        elif d <= 7:
            txt += f" — restam apenas {d} dia(s)"
        else:
            txt += f", ou seja, {d} dias a partir de hoje"

    taxa = e.get("taxaInscricao") or 0
    if taxa:
        txt += f". A taxa de inscrição é de {_brl(taxa)}"
    return txt + "."


def _selecao(e):
    det = e.get("detalhes") or {}
    etapas = det.get("etapas") or []
    if not etapas:
        return ""

    unicas = list(dict.fromkeys(x.strip().lower() for x in etapas))[:4]
    nomes = [u[0].upper() + u[1:] for u in unicas]
    lista = (", ".join(nomes[:-1]) + " e " + nomes[-1]) if len(nomes) > 1 else nomes[0]

    txt = f"A seleção prevê {lista.lower()}"
    if e.get("dataProva"):
        txt += f", com prova marcada para {_data_br(e['dataProva'])}"
    return txt + "."


def _quem_pode(e):
    cargo = (e.get("cargo") or "").lower()
    if e.get("escolaridade") == "medio":
        txt = ("A vaga é de nível médio/técnico — o requisito costuma ser "
               "curso técnico em contabilidade com registro no CRC")
    else:
        txt = ("A vaga é de nível superior — o requisito costuma ser "
               "bacharelado em Ciências Contábeis com registro no CRC")

    if "auditor" in cargo or "fiscal" in cargo:
        txt += (". Cargos de auditoria e fiscalização costumam aceitar também "
                "formações afins, o que tende a ampliar a concorrência")
    return txt + ". Confirme a exigência exata no edital."


def _banca(e):
    banca = (e.get("banca") or "").strip()
    if not banca:
        return ""
    return (f"A organização é da <b>{banca}</b>. Vale consultar provas "
            f"anteriores da banca: o estilo de cobrança costuma se repetir "
            f"de um certame para outro.")


def gerar(e):
    """Editorial em parágrafos HTML. Devolve '' se faltar o básico."""
    if not e.get("orgao") or not e.get("cargo"):
        return ""
    blocos = [_abertura(e), _remuneracao(e), _prazo(e),
              _selecao(e), _quem_pode(e), _banca(e)]
    return "".join(f"<p>{b}</p>" for b in blocos if b)


def aplicar(editais):
    """Gera o editorial de todos. Devolve quantos receberam texto."""
    preparar(editais)
    n = 0
    for e in editais:
        texto = gerar(e)
        if texto:
            e["editorial"] = texto
            n += 1
        else:
            e.pop("editorial", None)
    return n
