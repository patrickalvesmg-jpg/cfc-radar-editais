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
def _robots(host_scheme: str) -> urllib.robotparser.RobotFileParser:
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(f"{host_scheme}/robots.txt")
    try:
        rp.read()
    except Exception:
        # robots.txt inacessível: seguimos, mas sem assumir permissão ampla.
        pass
    return rp


def pode_acessar(url: str) -> bool:
    """Consulta o robots.txt do host. Um raspador que ignora robots.txt
    é um raspador que vai ser bloqueado — e com razão."""
    p = urllib.parse.urlparse(url)
    try:
        return _robots(f"{p.scheme}://{p.netloc}").can_fetch(USER_AGENT, url)
    except Exception:
        return True


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
        req = urllib.request.Request(url, headers=CABECALHOS)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            bruto = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                bruto = gzip.decompress(bruto)
            return bruto.decode("utf-8", "replace")

    except urllib.error.HTTPError as e:
        print(f"    HTTP {e.code}: {url}")
    except urllib.error.URLError as e:
        print(f"    rede: {e.reason} — {url}")
    except Exception as e:  # timeout, gzip corrompido, etc.
        print(f"    falhou ({type(e).__name__}): {url}")
    return None
