# -*- coding: utf-8 -*-
"""Camada de rede: busca páginas com educação e tolerância a falha."""

import gzip
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from functools import lru_cache

from config import CABECALHOS, PAUSA_ENTRE_REQUISICOES, TIMEOUT, USER_AGENT

_ultimo_acesso: dict[str, float] = {}


def _respeitar_pausa(host: str) -> None:
    """Espaça as chamadas por host. Sem isso, uma varredura de 30 dias
    viraria uma rajada de requisições contra o mesmo servidor."""
    agora = time.monotonic()
    anterior = _ultimo_acesso.get(host)
    if anterior is not None:
        espera = PAUSA_ENTRE_REQUISICOES - (agora - anterior)
        if espera > 0:
            time.sleep(espera)
    _ultimo_acesso[host] = time.monotonic()


@lru_cache(maxsize=64)
def _regras(host_scheme: str):
    """Busca e interpreta o robots.txt do host.

    Não dá para usar `RobotFileParser.read()` direto: ele engole o erro
    de rede e devolve um parser SEM REGRAS, que nega tudo. Um 404 (site
    sem robots.txt, o padrão da web é liberado) ficaria indistinguível
    de um `Disallow: /`. Buscamos o arquivo à mão para separar os casos.

    Retorna:
      None — sem restrição conhecida (404/410, ou arquivo vazio)
      RobotFileParser — regras a aplicar
    """
    url = f"{host_scheme}/robots.txt"
    try:
        req = urllib.request.Request(url, headers=CABECALHOS)
        with urllib.request.urlopen(req, timeout=15) as r:
            bruto = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                bruto = gzip.decompress(bruto)
            texto = bruto.decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        # 404/410: não existe robots.txt → liberado.
        # 401/403: o host restringe o próprio robots → tratamos como
        # proibido, que é o lado seguro.
        return None if e.code in (404, 410) else "PROIBIDO"
    except Exception:
        # Rede instável ou host que derruba a conexão (caso do in.gov.br).
        # Não sabemos a regra: assumimos proibido em vez de arriscar
        # varrer quem não quer ser varrido.
        return "PROIBIDO"

    if not texto.strip():
        return None

    rp = urllib.robotparser.RobotFileParser()
    rp.parse(texto.splitlines())
    return rp


def _disallows(regras) -> list[str]:
    """Caminhos proibidos para o agente `*`, lidos do parser."""
    caminhos = []
    entradas = list(getattr(regras, "entries", []))
    padrao = getattr(regras, "default_entry", None)
    if padrao:
        entradas.append(padrao)

    for entrada in entradas:
        for linha in getattr(entrada, "rulelines", []):
            if not linha.allowance and linha.path:
                caminhos.append(urllib.parse.unquote(linha.path))
    return caminhos


def pode_acessar(url: str) -> bool:
    """Consulta o robots.txt do host. Um raspador que ignora robots.txt
    é um raspador que vai ser bloqueado — e com razão.

    Não basta `can_fetch`: quando o arquivo traz `Allow: /` seguido de
    `Disallow: /pdf/`, o RobotFileParser considera o Allow mais
    específico e libera o caminho proibido. O PCI é exatamente esse caso
    — `can_fetch('/pdf/...')` devolvia True apesar do Disallow explícito.
    Conferimos os Disallow na mão para não depender dessa precedência.
    """
    p = urllib.parse.urlparse(url)
    regras = _regras(f"{p.scheme}://{p.netloc}")

    if regras is None:
        return True
    if regras == "PROIBIDO":
        return False

    caminho = p.path or "/"
    for proibido in _disallows(regras):
        if proibido == "/":
            return False
        # Regra com curinga do tipo "/*.pdf".
        if "*" in proibido:
            sufixo = proibido.split("*")[-1]
            if sufixo and caminho.endswith(sufixo):
                return False
            continue
        if caminho.startswith(proibido):
            return False

    try:
        return regras.can_fetch(USER_AGENT, url)
    except Exception:
        return False


def buscar(url: str, *, checar_robots: bool = True) -> str | None:
    """Devolve o corpo da resposta, ou None se a fonte falhar.

    Falha de uma fonte nunca derruba a varredura inteira: o robô roda sem
    supervisão e um portal fora do ar é situação esperada, não excepcional.
    """
    if checar_robots and not pode_acessar(url):
        print(f"    robots.txt proíbe: {url}")
        return None

    host = urllib.parse.urlparse(url).netloc
    _respeitar_pausa(host)

    try:
        # Acento na query quebra o urllib (UnicodeEncodeError). Escapamos
        # só o que não for ASCII, preservando a estrutura da URL.
        url_segura = urllib.parse.quote(url, safe=":/?&=#%+,;@[]!$'()*~")
        req = urllib.request.Request(url_segura, headers=CABECALHOS)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            bruto = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                bruto = gzip.decompress(bruto)

            # Nem todo site é UTF-8: a Fafipa serve iso-8859-1, e forçar
            # utf-8 transformava "Fundação" em "Funda??o". Respeitamos o
            # charset declarado e só caímos em utf-8 quando não há um.
            charset = r.headers.get_content_charset()
            if charset:
                try:
                    return bruto.decode(charset, "replace")
                except LookupError:
                    pass
            return bruto.decode("utf-8", "replace")

    except urllib.error.HTTPError as e:
        print(f"    HTTP {e.code}: {url}")
    except urllib.error.URLError as e:
        print(f"    rede: {e.reason} — {url}")
    except Exception as e:  # timeout, gzip corrompido, etc.
        print(f"    falhou ({type(e).__name__}): {url}")
    return None
