# -*- coding: utf-8 -*-
"""
Salário do CARGO, não o maior número do edital.

O problema (levantado pelo Patrick, 27/08/2026): o radar mostrava
"Contador — até R$ 8.000" quando o contador ganha R$ 2.000 e os R$ 8.000
eram do médico do mesmo concurso.

A causa: `extrair_salario` pegava `max()` de todos os valores do texto.
E o texto do PCI é a manchete ("salários de até R$ 36.619,86") ou a
faixa ("remuneração inicial de R$ 2.565,32 a R$ 21.525,56") — o teto é
sempre do cargo mais bem pago, nunca do contábil.

Medido no acervo: 11 casos com cargo de nível médio acima de R$ 12.000.
O pior era um Tesoureiro de prefeitura pequena a R$ 36.619.

Duas fontes, nesta ordem:

  1. O PDF do edital (o "ANEXO I" traz cargo x vencimento). É o dado
     exato. Confirmado em 5 de 5 editais do IBGP, e distingue Contador
     de Controlador Interno no MESMO edital — em Coromandel o radar
     mostrava R$ 7.822 para Contador, que é o vencimento do
     Controlador; o do Contador é R$ 4.562,82.

  2. O piso da faixa, quando só há faixa. "A partir de R$ 2.565" em vez
     de "até R$ 21.525". Subestima, e é de propósito: o contábil quase
     nunca é o teto, e errar para baixo não faz ninguém se inscrever
     esperando três vezes o que vai receber.

O que NÃO fazemos: pegar o número mais próximo do cargo na página da
banca. Em Objetivas e Aplicativa a tabela tem só CÓD./VAGA/ESCOLARIDADE/
TAXA — o valor ao lado do "Contador" é a taxa de inscrição (R$ 243,80).
Trocaria um erro por outro. Por isso a leitura de tabela exige achar a
coluna de salário pelo CABEÇALHO.
"""

import io
import re
import unicodedata
import urllib.request

# Valor em reais com centavos. Exige a vírgula: sem ela "R$ 1.000"
# casaria com número de processo e artigo de lei.
VALOR = re.compile(r"R\$\s*([\d]{1,3}(?:\.\d{3})*,\d{2})")

# O mesmo valor SEM o "R$" — várias tabelas põem o cifrão só no
# cabeçalho da coluna: "G02 Contador ... 40h 01+CR 01 - - 4.486,69".
# Exige milhar com ponto para não casar com nota de prova ("7,50") nem
# com percentual.
VALOR_SOLTO = re.compile(r"(?<![\d,.])([\d]{1,3}\.\d{3},\d{2})(?![\d])")

# Cabeçalho da coluna que interessa. "Taxa" fica de fora de propósito.
COLUNA_SALARIO = re.compile(
    r"sal[áa]rio|remunera|vencimento|subs[íi]dio|prov[ei]nto", re.I)

# Faixa: "de R$ X a R$ Y", "entre R$ X e R$ Y".
FAIXA = re.compile(
    r"(?:de|entre)\s*R\$\s*([\d.]+,\d{2})\s*(?:a|at[ée]|e)\s*R\$\s*([\d.]+,\d{2})",
    re.I)

# Abaixo disto é taxa de inscrição; acima, valor global de contrato.
MIN_SALARIO = 800.0
MAX_SALARIO = 100_000.0


def _num(bruto: str) -> float | None:
    try:
        return float(bruto.replace(".", "").replace(",", "."))
    except (ValueError, AttributeError):
        return None


def _plano(texto: str) -> str:
    """Minúsculas sem acento, PRESERVANDO o comprimento.

    Sem isso um índice achado no texto normalizado não vale para o
    texto original — o NFD decompõe o acento em dois pontos de código
    e o encode remove um, deslocando tudo que vem depois.
    """
    saida = []
    for ch in texto:
        d = unicodedata.normalize("NFD", ch)
        base = "".join(c for c in d if not unicodedata.combining(c)) or ch
        saida.append(base[0].lower())
    return "".join(saida)


def baixar_pdf_completo(url: str, tempo: int = 60) -> tuple[str, bytes]:
    """(texto, bytes) do PDF. ('', b'') se não der.

    Devolve também os bytes para que quem quiser ARQUIVAR o edital não
    precise baixar de novo — é o mesmo arquivo, e pedir duas vezes à
    banca seria o dobro de requisição sem motivo. Ver `arquivo_pdf.py`.
    """
    try:
        import pypdf
    except ImportError:
        return "", b""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        dados = urllib.request.urlopen(req, timeout=tempo).read()
    except Exception:
        return "", b""

    # Vários links "de PDF" devolvem HTML: página de erro, aviso de
    # cookie, ou o visualizador em vez do arquivo. O pypdf tenta ler
    # assim mesmo e cospe "invalid pdf header" no log sem devolver
    # nada útil. Todo PDF começa com %PDF (às vezes após um BOM).
    if b"%PDF" not in dados[:1024]:
        return "", b""

    try:
        leitor = pypdf.PdfReader(io.BytesIO(dados))
        return "\n".join(p.extract_text() or "" for p in leitor.pages), dados
    except Exception:
        # Ilegível como texto (digitalização), mas o arquivo é PDF de
        # verdade e ainda serve para o candidato baixar.
        return "", dados


def baixar_pdf(url: str, tempo: int = 60) -> str:
    """Texto do PDF. '' se não der (404, PDF de imagem, timeout)."""
    return baixar_pdf_completo(url, tempo)[0]


def do_texto(texto: str, cargo: str) -> float | None:
    """O vencimento do `cargo` neste texto. None se não achar.

    Procura o nome do cargo e pega o primeiro valor depois dele. Quando
    o cargo aparece mais de uma vez (tabela e conteúdo programático),
    fica com o MENOR: o maior costuma ser de outro cargo que veio na
    sequência.
    """
    if not texto or not cargo:
        return None

    corpo = re.sub(r"\s+", " ", texto)
    plano = _plano(corpo)
    if len(plano) != len(corpo):          # a normalização tem de preservar índice
        return None

    palavras = [p for p in _plano(cargo).split() if len(p) > 2]
    if not palavras:
        return None

    # Tolera ligação entre os termos: "TÉCNICO EM CONTABILIDADE" casa
    # com o cargo "Técnico De Contabilidade".
    padrao = r"[\s\w]{0,12}?".join(re.escape(p) for p in palavras)

    melhor = None
    for m in re.finditer(padrao, plano):
        janela = corpo[m.end():m.end() + 300]

        achado = VALOR.search(janela)
        if not achado:
            # Sem "R$" em lugar nenhum da janela, a tabela provavelmente
            # põe o cifrão só no cabeçalho da coluna. Aceitamos o número
            # solto — mas só aí, para não pescar nota nem percentual de
            # um texto que tinha valores marcados corretamente.
            if "R$" in janela:
                continue
            achado = VALOR_SOLTO.search(janela)
            if not achado:
                continue

        v = _num(achado.group(1))
        if v is None or not (MIN_SALARIO <= v <= MAX_SALARIO):
            continue
        if melhor is None or v < melhor:
            melhor = v
    return melhor


def piso_da_faixa(texto: str) -> float | None:
    """O menor valor de uma faixa declarada. None se não houver faixa."""
    if not texto:
        return None
    for m in FAIXA.finditer(texto):
        a, b = _num(m.group(1)), _num(m.group(2))
        if a is None or b is None:
            continue
        menor = min(a, b)
        if MIN_SALARIO <= menor <= MAX_SALARIO:
            return menor
    return None


def resolver(cargo: str, texto_pdf: str = "", texto_materia: str = "") -> tuple:
    """(valor, observação). Observação vazia = valor exato do cargo.

    A observação é o que o site mostra junto do número, para não
    afirmar precisão que não temos.
    """
    exato = do_texto(texto_pdf, cargo)
    if exato is not None:
        return exato, ""

    piso = piso_da_faixa(texto_pdf) or piso_da_faixa(texto_materia)
    if piso is not None:
        return piso, "a partir de"

    return None, ""
