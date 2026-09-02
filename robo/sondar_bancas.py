# -*- coding: utf-8 -*-
"""
Sondagem manual das 378 organizadoras do catálogo — pedido do Patrick
(01/09/2026): "será que não tem concurso contábil escondido numa banca
que o PCI não está anunciando hoje". Abre o site de CADA banca (a
ativa, a de reserva e o órgão público) e procura vaga contábil aberta
AGORA, mesmo que nenhuma fonte estruturada esteja apontando para ela.

    python robo/sondar_bancas.py                  # todas, sequencial
    python robo/sondar_bancas.py --lote 0:100      # só um pedaço
    python robo/sondar_bancas.py --situacao reserva  # só reserva

**NÃO roda no agendamento automático.** Fica pronta para rodar à mão,
ou para ligar depois — ver a nota no fim do arquivo e em
`.github/workflows/radar.yml`.

Por quê não entra na varredura semanal ainda: rodar as 378 leva perto
de 1h30 (medido em 01/09/2026, 4 lotes de ~75 em paralelo, ~25 min cada
com Playwright), contra os ~50 min da varredura normal — quase
triplica o tempo do job. E a primeira rodada completa (296 bancas em
reserva) não achou NENHUM concurso contábil genuinamente novo: os 10
candidatos brutos eram 8 falsos positivos e 2 que já estavam no radar
por outra fonte. Vale manter pronta e rodar periodicamente (o Patrick
sugeriu semanal ou quinzenal), não a cada varredura.

## As camadas de verificação — cada uma motivada por um falso positivo
## real, achado na auditoria manual de 01/09/2026

1. **`parece_concurso_atual` no CARD da listagem** — o card sozinho não
   prova nada. "Concurso Público 01/2018" (Acesse Concursos/SC) e a
   página `/dcf` de departamento de ensino (UFPI) casavam no regex de
   cargo mas não eram concurso aberto.

2. **PDFs do MESMO card, não os mais próximos no DOM** — quando a home
   lista vários concursos simultâneos (IBAM Concursos tinha 6 na mesma
   página), a ordem visual dos elementos não é a ordem de agrupamento;
   pegar os PDFs vizinhos trouxe o anexo de OUTRO concurso.

3. **Confirmar na PÁGINA DE DETALHE, não só no card** — esta é a
   camada que faltava na primeira versão e gerou 3 falsos positivos que
   só apareceram na revisão manual:
     - Curitibanos/SC: o card genérico não tinha ano nenhum; a página
       de detalhe dizia "Inscrições de 08/01/2018 a 06/02/2018".
     - UEL (PSS Contador): o card dizia "Edital PRORH nº 055/2026"; a
       página de detalhe mostrava "Homologação de Inscrições" em março
       e "Resultado Final" em maio — processo já encerrado.
   Por isso `sondar_pagina` agora SEMPRE abre o `href` do candidato e
   roda `parece_concurso_atual` de novo sobre o texto da página de
   detalhe, não confia no card.

4. **Deduplicar contra `data/editais.json`** — os dois achados reais da
   rodada de 01/09 (IBAM/Concórdia-SC e CEBRASPE/SEFAZ-AL) já estavam
   no radar via PCI. Sem checar isso, cada rodada "reencontraria" o
   mesmo concurso e pareceria achado novo.
"""
import argparse
import json
import re
import sys
import time
import unicodedata
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "robo"))
import config  # noqa: E402  (PADRAO_CONTABIL)

CATALOGO = BASE / "data" / "bancas-catalogo.json"
EDITAIS = BASE / "data" / "editais.json"
SAIDA_PADRAO = BASE / "robo" / "sondagem-ultima.json"


def norm(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize("NFD", (s or "").upper())
                   if unicodedata.category(c) != "Mn")


CAMINHOS_ABERTOS = [
    "", "/concursos", "/concursos-abertos", "/concurso",
    "/inscricoes-abertas", "/editais", "/edital",
    "/portal/concursos", "/concursos/abertos",
]

RUIDO_LINK = re.compile(
    r"facebook|instagram|twitter|linkedin|youtube|whats|t\.me|mailto"
    r"|politica|privacidade|termos|cookie|lgpd", re.I)

# Ano corrente calculado em runtime — a versão de scratchpad tinha isto
# fixo em "2026", que ia ficar errado sozinho ano que vem. "Válido" é o
# ano atual e o anterior (edital de dezembro com prova em janeiro);
# "velho" é qualquer ano de 4 dígitos anterior a isso (2000-2099, cobre
# décadas sem precisar mexer de novo).
_ANO = date.today().year
_TODOS_OS_ANOS = re.compile(r"\b(20\d\d)\b")


def _achar_anos(texto: str) -> tuple[int, int]:
    """(quantos anos válidos, quantos anos velhos) no texto."""
    novos = velhos = 0
    for m in _TODOS_OS_ANOS.finditer(texto):
        if int(m.group(1)) >= _ANO - 1:
            novos += 1
        else:
            velhos += 1
    return novos, velhos


def parece_concurso_atual(texto: str) -> bool:
    """Card OU página de detalhe: sinal de prazo/edital + ano não
    dominado por anos antigos. Usada duas vezes por candidato — ver
    `sondar_pagina`, item 3 do cabeçalho."""
    if not texto:
        return False
    tem_sinal = bool(re.search(
        r"inscri[çc][õo]es|per[íi]odo\s+de\s+inscri|prazo\s+de\s+inscri"
        r"|edital\s+de\s+abertura|processo\s+seletivo|concurso\s+p[úu]blico",
        texto, re.I))
    if not tem_sinal:
        return False
    anos_novos, anos_velhos = _achar_anos(texto)
    if anos_novos == 0 and anos_velhos == 0:
        return True
    return anos_novos > 0 and anos_novos >= anos_velhos


# Sinais de que o processo, mesmo citando "inscrições" e ano atual, já
# passou da fase de inscrição — achado no caso UEL (01/09/2026): a
# página tinha "inscrições" no texto mas era sobre HOMOLOGAÇÃO de
# inscrições já encerradas, não abertura.
PADRAO_JA_ENCERRADO = re.compile(
    r"resultado\s+final|homologa[çc][ãa]o\s+(?:d[ae]s?\s+)?inscri"
    r"|convoca[çc][ãa]o\s+para\s+avalia[çc][ãa]o|lista\s+de\s+classifica"
    r"|processo\s+finalizado|selecao\s+finalizada|\bfinalizad[oa]\b"
    r"|homologado", re.I)


def parece_ainda_aberto(texto: str) -> bool:
    return not PADRAO_JA_ENCERRADO.search(texto or "")


def elementos_link_contabil(pagina):
    """ElementHandles de <a> cujo CARD (ancestral com texto) casa com
    o padrão contábil — devolve o handle, não só href/texto, para dar
    para subir no DOM depois."""
    try:
        handles = pagina.query_selector_all("a[href]")
    except Exception:
        return []
    achados = []
    for h in handles:
        try:
            # `.href` via JS (não `get_attribute`) — a PROPRIEDADE do
            # DOM vem resolvida para absoluta pelo navegador; o
            # ATRIBUTO cru fica relativo ("/v2/Selecao/..."), e por
            # causa disso a confirmação em página de detalhe (mais
            # abaixo) pulava o caso mais comum: achado no debug do
            # caso UEL (01/09/2026), cujo link nunca começa com
            # "http" e por isso nunca era reaberto para confirmar.
            href = h.evaluate("e => e.href") or ""
        except Exception:
            continue
        if not href or RUIDO_LINK.search(href):
            continue
        try:
            ctx = h.evaluate("""e => {
                let c = e, txt = '';
                for (let i = 0; i < 6 && c; i++) {
                    txt = (c.innerText || '').replace(/\\s+/g, ' ').trim();
                    if (txt.length > 20) break;
                    c = c.parentElement;
                }
                return txt.slice(0, 300);
            }""")
        except Exception:
            continue
        if config.PADRAO_CONTABIL.search(ctx):
            achados.append((h, href, ctx))
    return achados


def texto_do_card(elemento_link):
    """Texto do card inteiro (nome do órgão + prazo), não só do botão
    ou da tabela de cargos — ver item 2/3 do cabeçalho do módulo."""
    try:
        via_classe = elemento_link.evaluate("""e => {
            let p = e;
            for (let i = 0; i < 12 && p; i++) {
                if (p.className && /(^|\\s)card(\\s|$)/.test(p.className)) {
                    return (p.innerText || '').slice(0, 2000);
                }
                p = p.parentElement;
            }
            return '';
        }""")
        if via_classe and len(via_classe) > 60:
            return via_classe
    except Exception:
        pass
    try:
        return elemento_link.evaluate("""e => {
            let p = e, melhor = '';
            for (let i = 0; i < 10 && p; i++) {
                const t = (p.innerText || '').trim();
                if (t.length > melhor.length && t.length < 4000) melhor = t;
                p = p.parentElement;
            }
            return melhor.slice(0, 2000);
        }""")
    except Exception:
        return ""


def _handle_do_card(elemento_link):
    """Sobe do link até o último ancestral que ainda contém
    "DOCUMENTOS" sem o texto ter mais que dobrado — ver item 2 do
    cabeçalho (caso IBAM Concursos)."""
    try:
        return elemento_link.evaluate_handle("""e => {
            let p = e, ultimo = null, ultimoTam = 0;
            for (let i = 0; i < 10 && p; i++) {
                const t = (p.innerText || '');
                if (t.includes('DOCUMENTOS') || t.includes('Documentos')) {
                    if (ultimo && t.length > ultimoTam * 2.5) break;
                    ultimo = p; ultimoTam = t.length;
                }
                p = p.parentElement;
            }
            return ultimo;
        }""")
    except Exception:
        return None


def pdfs_do_card(elemento_link):
    handle = _handle_do_card(elemento_link)
    card_el = handle.as_element() if handle else None
    if not card_el:
        return []
    try:
        pares = card_el.evaluate(
            "e => Array.from(e.querySelectorAll('a[href]'))"
            ".map(a => [a.href, (a.textContent||'').trim().slice(0,70)])")
    except Exception:
        return []
    saida = []
    for h, t in pares:
        if h and re.search(r"\.pdf|/download|/arquivo|s3\.amazonaws", h, re.I) \
           and not RUIDO_LINK.search(h):
            saida.append(h)
    return list(dict.fromkeys(saida))


def pdfs_da_pagina(pagina):
    js = "els => els.map(e => [e.href, (e.textContent||'').trim().slice(0,70)])"
    try:
        pares = pagina.eval_on_selector_all("a[href]", js)
    except Exception:
        return []
    saida = []
    for h, t in pares:
        if h and re.search(r"\.pdf|/download|/arquivo|s3\.amazonaws", h, re.I) \
           and not RUIDO_LINK.search(h):
            saida.append(h)
    return list(dict.fromkeys(saida))


def sondar_pagina(pagina, url):
    """Abre a URL, acha candidato contábil pelo CARD, e só confirma
    depois de abrir a PÁGINA DE DETALHE e checar recência + "ainda não
    encerrado" ali — não no card, que pode estar desatualizado ou
    incompleto (item 3 do cabeçalho)."""
    try:
        pagina.goto(url, timeout=35000, wait_until="domcontentloaded")
        pagina.wait_for_timeout(1800)
    except Exception:
        return "erro", None

    candidatos = elementos_link_contabil(pagina)
    for elemento, href, ctx_curto in candidatos:
        card_txt = texto_do_card(elemento) or ctx_curto
        if not parece_concurso_atual(card_txt):
            continue

        pdfs = pdfs_do_card(elemento)

        # Confirmação na página de detalhe. Se o link não abrir uma
        # página nova válida (ex.: formulário de inscrição direto sem
        # texto substancial), fica só na checagem do card.
        detalhe_ok = True
        if href and href.startswith("http"):
            pg2 = pagina.context.new_page()
            try:
                pg2.goto(href, timeout=25000, wait_until="domcontentloaded")
                pg2.wait_for_timeout(1500)
                texto_detalhe = pg2.inner_text("body")
                if len(texto_detalhe) > 200:
                    detalhe_ok = (parece_concurso_atual(texto_detalhe)
                                 and parece_ainda_aberto(texto_detalhe))
                    if not pdfs:
                        pdfs = pdfs_da_pagina(pg2)
            except Exception:
                pass
            finally:
                pg2.close()

        if not detalhe_ok:
            continue

        return "achou", {
            "contexto": ctx_curto,
            "href": href,
            "pdfs": pdfs[:6],
            "trecho_card": card_txt[:500],
        }
    return "nada", None


def sondar(ctx_navegador, banca):
    dom = banca["dominio"]
    resultado = {"dominio": dom, "nome": banca["nome"],
                 "situacao": banca.get("situacao", "?"), "status": "nada"}

    for esquema in ("https://", "http://"):
        page = ctx_navegador.new_page()
        try:
            status, dado = sondar_pagina(page, f"{esquema}{dom}/")
            if status == "erro":
                page.close()
                continue

            if status == "achou":
                resultado.update(status="achou", **dado)
                page.close()
                return resultado

            for caminho in CAMINHOS_ABERTOS[1:5]:
                status2, dado2 = sondar_pagina(page, f"{esquema}{dom}{caminho}")
                if status2 == "achou":
                    resultado.update(status="achou", **dado2)
                    page.close()
                    return resultado

            resultado["status"] = "nada"
            page.close()
            return resultado
        except Exception as ex:
            resultado["status"] = "erro"
            resultado["erro"] = f"{type(ex).__name__}: {str(ex)[:60]}"
            try:
                page.close()
            except Exception:
                pass
            continue

    if resultado["status"] == "nada" and "erro" not in resultado:
        resultado["status"] = "fora_do_ar"
    return resultado


def _chaves_dos_editais_existentes() -> set[str]:
    """(cidade normalizada, cargo normalizado) de todo edital já no
    radar — para não reportar como "achado" um concurso que a gente já
    tem por outra fonte. Foi o caso de IBAM/Concórdia e CEBRASPE/SEFAZ-
    AL em 01/09/2026: já estavam no radar via PCI."""
    try:
        eds = json.loads(EDITAIS.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()
    chaves = set()
    for e in eds:
        c = norm(e.get("orgao", "")) + "|" + norm(e.get("cargo", ""))
        chaves.add(c)
        if e.get("cidade"):
            chaves.add(norm(e["cidade"]) + "|" + norm(e.get("cargo", "")))
    return chaves


# Palavras que aparecem em quase toda chave (termo do domínio, não
# nome próprio) e por isso NÃO contam como acerto de dedup — sem esta
# lista, "Prefeitura de Cidade Nunca Vista abre concurso para
# Contador" batia como "já no radar" só por causa de "CONCURSO" e
# "CONTADOR", palavras presentes em quase todo registro do acervo.
_PALAVRA_GENERICA = {
    "PREFEITURA", "MUNICIPIO", "MUNICIPAL", "CAMARA", "CONCURSO",
    "CONCURSOS", "PUBLICO", "PUBLICA", "CONTADOR", "CONTADORA",
    "CONTABIL", "CONTABEIS", "CONTABILIDADE", "AUDITOR", "AUDITORIA",
    "FISCAL", "TRIBUTOS", "CONTROLE", "INTERNO", "EDITAL", "ABERTURA",
    "INSCRICOES", "VAGAS", "TECNICO", "ANALISTA", "ASSISTENTE",
    "SECRETARIA", "GOVERNO", "ESTADO", "INSTITUTO", "FUNDACAO",
}


def _ja_no_radar(chaves_existentes: set[str], texto_card: str) -> bool:
    """Exige UMA palavra específica (não genérica) do card — nome de
    cidade ou órgão — batendo numa chave existente que TAMBÉM tenha
    marca contábil. "Concórdia" sozinha já é bastante discriminante;
    exigir duas (testado) perdia o próprio caso real que motivou esta
    função — "Câmara Municipal de Concórdia/SC" só tem uma palavra
    específica no card curto, o resto é vocabulário comum de edital.

    Uma palavra genérica sozinha ("Contador", "Concurso") NUNCA basta
    — está fora de `_PALAVRA_GENERICA` antes de chegar aqui — mas
    ainda checamos se a CHAVE batida tem marca contábil, para não
    casar "Concórdia" com um registro de outro cargo qualquer daquela
    cidade que não seja o mesmo achado."""
    palavras = [p for p in re.split(r"[^A-Za-zÀ-ÿ]+", norm(texto_card))
               if len(p) >= 5 and p not in _PALAVRA_GENERICA]
    if not palavras:
        return False
    for chave in chaves_existentes:
        if not config.PADRAO_CONTABIL.search(chave):
            continue
        if any(p in chave for p in palavras[:12]):
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--situacao", choices=["reserva", "em_uso", "orgao_publico", "todas"],
                    default="todas", help="filtra o catálogo por situação")
    ap.add_argument("--lote", type=str, default=None,
                    help="fatia 'inicio:fim' sobre a lista filtrada, ex. 0:100")
    ap.add_argument("--saida", type=str, default=None,
                    help="onde gravar o JSON (padrão: robo/sondagem-ultima.json)")
    args = ap.parse_args()

    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    alvos = catalogo if args.situacao == "todas" else \
        [b for b in catalogo if b["situacao"] == args.situacao]

    if args.lote:
        ini, fim = (int(x) if x else None for x in args.lote.split(":"))
        alvos = alvos[ini:fim]

    saida_path = Path(args.saida) if args.saida else SAIDA_PADRAO
    print(f"sondando {len(alvos)} bancas (saída: {saida_path})\n", flush=True)

    chaves_existentes = _chaves_dos_editais_existentes()

    from playwright.sync_api import sync_playwright
    resultados = []
    t0 = time.time()
    with sync_playwright() as pw:
        nav = pw.chromium.launch(args=["--ignore-certificate-errors"])
        ctx = nav.new_context(ignore_https_errors=True, accept_downloads=True)
        for i, banca in enumerate(alvos, 1):
            r = sondar(ctx, banca)
            if r["status"] == "achou" and _ja_no_radar(chaves_existentes, r.get("trecho_card", "")):
                r["status"] = "ja_no_radar"
            resultados.append(r)
            marca = {"achou": "!!!", "ja_no_radar": " ok ", "nada": "  .",
                     "fora_do_ar": "  x", "erro": "  ?"}[r["status"]]
            print(f"[{i:3}/{len(alvos)}] {marca} {banca['dominio']:34} {r['status']}", flush=True)
            if r["status"] == "achou":
                print(f"          -> {r.get('contexto', '')[:90]}", flush=True)
            if i % 15 == 0:
                decorrido = time.time() - t0
                print(f"      ({decorrido/60:.1f} min, ~{decorrido/i*len(alvos)/60:.1f} min total est.)",
                      flush=True)
                saida_path.write_text(json.dumps(resultados, ensure_ascii=False, indent=1), encoding="utf-8")
        nav.close()

    saida_path.write_text(json.dumps(resultados, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n{'=' * 60}")
    import collections
    c = collections.Counter(r["status"] for r in resultados)
    print("resumo:", dict(c))
    achou = [r for r in resultados if r["status"] == "achou"]
    print(f"\nACHADOS NOVOS ({len(achou)}) — revisar à mão antes de cadastrar:")
    for r in achou:
        print(f"  {r['dominio']:34} {r.get('contexto', '')[:80]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
