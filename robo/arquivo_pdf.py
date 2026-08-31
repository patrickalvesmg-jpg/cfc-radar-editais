# -*- coding: utf-8 -*-
"""
Guarda o PDF do edital junto com o radar.

Por que existe (pedido do Patrick, 31/08/2026): até aqui o site só
GUARDAVA O LINK do edital. O robô baixava o PDF para ler o salário e
descartava os bytes — `salario.baixar_pdf` lia o texto e devolvia a
string, o arquivo se perdia.

Link não é arquivo. Três coisas acontecem com um link de banca:

  1. o concurso encerra e a banca tira a página do ar;
  2. a banca republica o edital retificado NA MESMA URL, e o que a
     pessoa baixa deixa de ser o que a gente leu;
  3. o link some no meio da reforma do site da banca.

Nos três casos o candidato fica sem o documento e nós sem como provar
de onde saiu o salário que publicamos. Guardar o arquivo resolve os
três — e é o mesmo download que já fazíamos, agora sem jogar fora.

**O arquivo é cópia de apoio, não substitui a fonte.** A página do
edital continua mostrando o link oficial da banca em primeiro lugar;
o PDF guardado entra como alternativa ("cópia que lemos em
DD/MM/AAAA"), para o caso de o oficial ter saído do ar.

Nome do arquivo: `<id-do-edital>-<hash8>.pdf`. O hash é do conteúdo,
então republicação retificada vira arquivo novo em vez de sobrescrever
silenciosamente o antigo — e dá para ver que mudou.
"""

import hashlib
import json
import urllib.request
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "data" / "editais-pdf"
INDICE = RAIZ / "data" / "editais-pdf" / "indice.json"

# Teto por arquivo. Edital de concurso raramente passa de 5 MB; o que
# passa muito disso costuma ser digitalização de página inteira, que
# não tem texto pesquisável e não serve para ler salário. Guardar isso
# incharia o repositório sem benefício.
LIMITE_BYTES = 12 * 1024 * 1024


def _indice() -> dict:
    if INDICE.exists():
        try:
            return json.loads(INDICE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _gravar_indice(idx: dict) -> None:
    PASTA.mkdir(parents=True, exist_ok=True)
    INDICE.write_text(
        json.dumps(idx, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def guardar_bytes(edital_id: str, url: str, dados: bytes) -> dict | None:
    """Grava bytes já baixados. Devolve o registro, ou None se não servir.

    Recebe os bytes em vez de baixar de novo: quem chama (a verificação
    de salário) já tem o arquivo na mão. Baixar duas vezes seria pedir
    o dobro para a banca sem necessidade.
    """
    if not dados or b"%PDF" not in dados[:1024]:
        return None
    if len(dados) > LIMITE_BYTES:
        return None

    h = hashlib.sha256(dados).hexdigest()[:8]
    nome = f"{edital_id}-{h}.pdf"
    destino = PASTA / nome
    PASTA.mkdir(parents=True, exist_ok=True)
    if not destino.exists():
        destino.write_bytes(dados)

    registro = {
        "arquivo": f"data/editais-pdf/{nome}",
        "origem": url,
        "bytes": len(dados),
        "sha256_8": h,
        "baixadoEm": date.today().isoformat(),
    }
    idx = _indice()
    idx[edital_id] = registro
    _gravar_indice(idx)
    return registro


def baixar_e_guardar(edital_id: str, url: str, tempo: int = 60) -> dict | None:
    """Baixa a URL e guarda. Para quem ainda não tem os bytes."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        dados = urllib.request.urlopen(req, timeout=tempo).read()
    except Exception:
        return None
    return guardar_bytes(edital_id, url, dados)


def aplicar_aos_editais(editais: list[dict]) -> int:
    """Escreve o campo `pdfArquivo` em cada edital que tem cópia local."""
    idx = _indice()
    n = 0
    for e in editais:
        reg = idx.get(e.get("id", ""))
        if reg:
            e["pdfArquivo"] = reg["arquivo"]
            e["pdfArquivoEm"] = reg["baixadoEm"]
            n += 1
    return n
