"""Gera a página de conferência dos editais pendentes (padrão 12/10).

Uso: python robo/gerar_conferencia.py 19-10
Molde de CSS/JS: conferencia-12-10.html. Saída: conferencia-<dd-mm>.html
"""
import hashlib
import html
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TAG = sys.argv[1] if len(sys.argv) > 1 else date.today().strftime("%d-%m")
TAG_BARRA = TAG.replace("-", "/")
HOJE = date.today().isoformat()


def norm(s):
    s = unicodedata.normalize("NFD", s or "").lower()
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\b(prefeitura|camara|municipal|municipio|de|da|do|dos|das|e)\b", " ", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def br(d):
    a, m, dia = d.split("-")
    return f"{dia}/{m}/{a}"


def dinheiro(v):
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


esc = html.escape
dados = json.loads((RAIZ / "data/editais.json").read_text(encoding="utf-8"))
L = dados if isinstance(dados, list) else dados["editais"]
rem = json.loads((RAIZ / "data/removidos.json").read_text(encoding="utf-8"))

publicados = [e for e in L if e.get("revisado")]
chaves_rem = {(norm(v.get("orgao", "")), norm(v.get("cargo", ""))) for v in rem.values()}

pend, fora = [], []
for e in L:
    if e.get("revisado") or e["id"] in rem:
        continue
    if e["status"] == "encerrado" or (e.get("inscricaoFim") or "9999") < HOJE:
        continue
    if not e.get("siteInscricao"):
        fora.append(e)
        continue
    pend.append(e)


def repetido_de(e):
    k = (norm(e["orgao"]), norm(e["cargo"]))
    if k in chaves_rem:
        return None, "removido"
    for p in publicados:
        if (norm(p["orgao"]), norm(p["cargo"])) == k:
            return p, "publicado"
    return None, None


def linha(e):
    pdf_ok = bool(e.get("pdfArquivo"))
    sal = e.get("salario") or 0
    prazo = br(e["inscricaoFim"])
    st = e["status"]
    cls_st = {"aberto": "aberto", "previsto": "previsto", "encerrando": "encerrando urg"}.get(st, "")
    rot_st = {"aberto": "aberto", "previsto": "previsto", "encerrando": "fecha em breve"}.get(st, st)
    notas = []
    dup, tipo = repetido_de(e)
    if tipo == "publicado":
        if dup.get("inscricaoFim") == e.get("inscricaoFim"):
            notas.append('<p class="nota dup">Parece repetido: já está no ar com o mesmo órgão, cargo e prazo '
                         f'({br(dup["inscricaoFim"])}). Marque <strong>não publicar</strong>.</p>')
        else:
            notas.append('<p class="nota prorr">Já está no ar com prazo até '
                         f'{br(dup["inscricaoFim"])}. Este traz prazo até {prazo}: confira se é prorrogação ou edital novo.</p>')
    elif tipo == "removido":
        notas.append('<p class="nota dup">Você já removeu este órgão/cargo antes. Marque <strong>não publicar</strong> se continuar valendo.</p>')
    if not e.get("uf"):
        notas.append('<p class="nota info">Sem UF no cadastro: a conferência de segurança barra a publicação até a UF ser informada.</p>')
    if pdf_ok and not sal:
        notas.append('<p class="nota info">PDF lido, mas o salário do cargo não foi achado nele. Confira no edital.</p>')
    if sal >= 15000 and e.get("nivel") != "federal":
        notas.append('<p class="nota info">Salário alto para o cargo: pode ser o teto do concurso, e não o deste cargo.</p>')

    if sal:
        cel_sal = f'<span class="valor">{dinheiro(sal)}</span>' + (
            '<span class="rot ok">lido no PDF</span>' if pdf_ok else '<span class="rot duv">da fonte, não conferido</span>')
    else:
        cel_sal = '<span class="vazio">não achado no PDF</span>' if pdf_ok else '<span class="vazio">sem valor</span>'

    nome = f'{e["orgao"][:40]} — {e["cargo"]}'
    links = []
    if pdf_ok and e.get("pdfEdital"):
        links.append(f'<a href="{esc(e["pdfEdital"])}" target="_blank" rel="noopener">Edital (PDF)</a>')
    links.append(f'<a href="{esc(e["siteInscricao"])}" target="_blank" rel="noopener">Página do concurso</a>')
    ck = "ck-" + hashlib.sha1(e["id"].encode()).hexdigest()[:10]
    onde = e.get("cidade") or re.sub(r"^(Prefeitura|Câmara|Município)( Municipal)?( de| do| da)? ", "", e["orgao"])[:28]
    return (
        f'<tr id="r-{e["id"]}" class="{"eh-dup" if tipo == "publicado" and dup.get("inscricaoFim") == e.get("inscricaoFim") else ""}">\n'
        f'<td class="ck"><input type="checkbox" id="{ck}" aria-label="Conferido"></td>\n'
        f'<td><strong>{esc(onde)}</strong><span class="uf">{esc(e.get("uf") or "—")}</span><span class="org">{esc(e["orgao"])}</span></td>\n'
        f'<td>{esc(e["cargo"])}<span class="sub">Vagas: {esc(str(e.get("vagas") or "—"))}</span></td>\n'
        f'<td class="num">{cel_sal}<label class="campo"><span>Salário certo</span>'
        f'<input type="text" inputmode="decimal" placeholder="ex.: 4.950,18" data-id="{e["id"]}" data-nome="{esc(nome)}" value=""></label>'
        f'<label class="rem"><input type="checkbox" data-remover="{e["id"]}"> não publicar</label></td>\n'
        f'<td class="num">{prazo}<span class="st {cls_st}">{rot_st}</span></td>\n'
        f'<td class="links">{" · ".join(links)}{"".join(notas)}</td>\n</tr>'
    )


def tabela(itens):
    cab = ('<div class="tab"><table><thead><tr><th class="ck"><span class="sr">Conferido</span></th><th>Onde</th>'
           '<th>Cargo</th><th>Salário</th><th>Inscrição até</th><th>Conferir em</th></tr></thead><tbody>')
    return cab + "".join(linha(e) for e in itens) + "</tbody></table></div>"


ordem = lambda e: (e["inscricaoFim"], e["orgao"])
novos = [e for e in pend if e.get("capturadoEm", "") >= "2026-10-13"]
velhos = [e for e in pend if e not in novos]
com_pdf = lambda lst: [e for e in lst if e.get("pdfArquivo") and e.get("salario")]
sem_pdf = lambda lst: [e for e in lst if not (e.get("pdfArquivo") and e.get("salario"))]
dups = [e for e in pend if repetido_de(e)[1]]

modelo = (RAIZ / "conferencia-12-10.html").read_text(encoding="utf-8")
css = re.search(r"<style>.*?</style>", modelo, re.S).group(0)
js = re.search(r"<script>.*?</script>", modelo, re.S).group(0)
js = js.replace("conf-1210", "conf-" + TAG.replace("-", "")).replace("correcoes-radar-12-10", "correcoes-radar-" + TAG)

secoes = []
for titulo, sub, lst in (
    (f"Novos desta varredura ({len(novos)})",
     "Capturados em 19/10. Abra a página do concurso e confira cargo, salário e prazo.", sorted(novos, key=ordem)),
    (f"Já estavam no arquivo e ainda não foram conferidos ({len(velhos)})",
     "Capturados em varreduras anteriores e nunca marcados como conferidos. Mesma conferência.", sorted(velhos, key=ordem)),
):
    if lst:
        secoes.append(f"<h2>{esc(titulo)}</h2>\n<p class=\"secao-sub\">{esc(sub)}</p>\n{tabela(lst)}")

fora_html = ""
if fora:
    itens = "".join(f"<li>{esc(e['orgao'])} ({esc(e.get('uf') or '—')}) — {esc(e['cargo'])} — até {br(e['inscricaoFim'])}</li>" for e in fora)
    fora_html = f"<details><summary>{len(fora)} fora do site que não vão ao ar (sem link de inscrição)</summary><ul>{itens}</ul></details>"

pagina = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Conferência Radar {TAG_BARRA}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500;600&family=IBM+Plex+Sans:wght@400;600&display=swap">
{css}
</head><body><div class="wrap">
<h1>Editais para conferir</h1>
<p class="lead">Varredura de {TAG_BARRA}/2026. Entram só os que continuam válidos (inscrição não vencida e com link) e ainda não foram conferidos. Ordem: prazo mais curto primeiro.</p>
<div class="resumo">
 <div class="chip"><b>{len(pend)}</b><span>pendentes válidos</span></div>
 <div class="chip ok"><b>{len(com_pdf(pend))}</b><span>com salário lido no PDF</span></div>
 <div class="chip duv"><b>{len(sem_pdf(pend))}</b><span>para você conferir</span></div>
 <div class="chip dup"><b>{len(dups)}</b><span>possíveis repetidos</span></div>
</div>
<div class="como"><p><strong>Lido no PDF</strong> quer dizer que o robô baixou o edital da banca e leu o salário do cargo. Esses só precisam de uma olhada rápida.</p>
<p><strong>Da fonte, não conferido</strong> quer dizer que ninguém abriu o edital. O salário é o que a fonte divulgou e pode ser o teto do concurso ou de outro cargo (foi o caso de Urussanga, Colinas e Água Limpa em 12/10). Abra a página do concurso e confira cargo, salário e prazo.</p>
<p>A caixinha à esquerda marca o que você já conferiu. Se o salário estiver errado, digite o certo no campo <strong>Salário certo</strong>. Se o edital não deve ir ao ar, marque <strong>não publicar</strong>. No fim, clique em <strong>Salvar correções</strong>: o arquivo <code>correcoes-radar-{TAG}.json</code> vai para a sua pasta Downloads e eu leio de lá.</p></div>
{chr(10).join(secoes)}
<div class="barra"><button type="button" id="salvar">Salvar correções</button><span id="status">Nenhuma correção nova.</span></div>
{fora_html}
</div>
{js}
</body></html>
"""
assert "\x08" not in pagina
saida = RAIZ / f"conferencia-{TAG}.html"
saida.write_text(pagina, encoding="utf-8")
print(f"{saida.name}: {len(pend)} pendentes ({len(novos)} novos, {len(velhos)} antigos), "
      f"{len(com_pdf(pend))} com PDF, {len(dups)} possíveis repetidos, {len(fora)} fora")
