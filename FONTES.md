# Fontes do Radar — mapa completo

Documento de referência: **de onde vem cada edital**, o que já foi
testado e o que não vale a pena tentar de novo.

Última varredura completa: **19/08/2026** · 63 editais · 222 vagas

---

## 1. Como o radar descobre um concurso

```
7 fontes varrem em paralelo
        ↓
filtro de 3 camadas   (é concurso? é contábil? não é ruído?)
        ↓
enriquecimento        (link da página do concurso · PDF · coordenada)
        ↓
mesclagem             (preserva o que já foi revisado à mão)
        ↓
data/editais.json  →  site
```

Uma varredura completa leva **cerca de 15 minutos** — são ~400 páginas
com pausa de 1,5s entre requisições ao mesmo host.

---

## 2. Fontes ativas

| Fonte | Tipo | Editais hoje | Papel |
|---|---|---|---|
| **PCI Concursos** | agregador | **52** | Descoberta — é o que mais rende |
| **Fundação FAFIPA** | banca | 5 | Descoberta + PDF |
| **CEBRASPE** | banca | 3 | Descoberta + PDF |
| **ISET** | banca | 1 | Descoberta |
| **JCM Concursos** | banca | 1 | Descoberta |
| **Concursos no Brasil** | agregador | 1 | Link da página do concurso |
| Edital Concursos Brasil | agregador | 0 | Idem (volume baixo) |
| Consulplan | banca | 0 | Conselhos de Contabilidade (CRC/CFC) |
| Querido Diário | diários municipais | 0 | Rende quase nada — ver §5 |
| Radar do Estratégia | mapa | — | **Só coordenadas**, não cria edital |
| Base IBGE | municípios | — | 5.571 cidades com lat/long |

**Bancas na plataforma comum** (`robo/fontes/bancas.py`), varridas em
lote: FAFIPA · Objetiva · AvançaSP · Access · Exame · Fundep · Instituto
Aplicativa · AMAUC · Consulpam · Vicente Nelson · ISET · AB Concursos ·
JCM · Auctor · MS Concursos · COTEC/FADENOR · EducaPB.

Acrescentar banca ali é **uma linha** na tupla `BANCAS`.

---

## 3. Sondagem das 382 organizadoras do PCI

O PCI mantém catálogo em `/organizadoras/`. Extraí os domínios que
aparecem nas matérias e sondei **71**:

| Resultado | Qtde | O que significa |
|---|---|---|
| **Varreríveis** | **16** | Já ligadas |
| Barram por `robots.txt` | 22 | Fora de alcance por decisão do site |
| Sem rota previsível | 32 | Cada uma exigiria raspador próprio |
| Fora do ar | 1 | — |

Detalhe em `robo/_sonda.json`.

**Rendimento por banca** (concursos com cargo contábil / ativos):

| Banca | Rendimento | Observação |
|---|---|---|
| FAFIPA | **8 / 22** | Prefeituras do interior PR/SC/MG |
| Access | 4 / 15 | Todos vencidos na medição |
| AvançaSP | 3 / 10 | |
| IBGP | 1 / 17 | O único já vinha do PCI |

---

## 4. Portais testados e descartados

| Portal | Motivo |
|---|---|
| Tec Concursos, Concursos Brasil, Sou Concurseiro | `robots.txt` barra |
| Gran Cursos | rota inexistente |
| Direção Concursos, JC Concursos | não citam cargo contábil na listagem |
| **Portal CFC** | publica sobre **Exame de Suficiência**, não concurso público |
| **CRCs (SP/MG/RJ/PR/RS)** | abrem concurso próprio raramente; quando abrem, cai na Consulplan, que já monitoramos |
| FCC | `robots.txt` proíbe `/concursos/` |
| VUNESP, IBFC | respondem 403 a qualquer automação |
| DOU (in.gov.br) | `robots.txt` é `Disallow: /` |

**Não repetir estes testes** sem motivo novo.

---

## 5. Por que os diários municipais rendem pouco

Era a aposta natural para "vagas em prefeitura". Investigado e medido:

1. a API do Querido Diário **não suporta booleano** — `"a" AND b` vira
   busca solta: de 40 resultados, 27 falavam de concurso e 1 citava
   contador;
2. os `excerpts` trazem trecho **arbitrário** do diário, quase nunca a
   tabela de cargos;
3. baixando o **texto completo** de 20 editais de abertura recentes
   (~112 mil caracteres cada), **nenhum** tinha vaga contábil.

O volume vem das bancas e do PCI, não dos diários.

---

## 6. Diários estaduais: testados e descartados

Testados 10 diários oficiais estaduais (SP, PR, MG, RS, SC, BA, PE, GO,
CE, RJ):

| Resultado | Qtde |
|---|---|
| Barram por `robots.txt` | 3 (RS, BA, CE) |
| Permitem, mas **sem busca aproveitável** | 7 |

Nenhum expõe API ou campo de busca que aceite termo — é o mesmo padrão
que já inviabilizou o Querido Diário (§5). Varrer edição por edição
seria baixar milhares de páginas para achar meia dúzia de vagas.

**Conclusão:** concurso de TCE e SEFAZ chega até nós pelo PCI e pelas
bancas grandes (CEBRASPE, FGV, FUNDATEC), que publicam com cargo
estruturado. Não vale raspar diário estadual.

---

## 7. Sobre contornar bloqueio de robots.txt

**Não fazemos, e a razão é prática além de ética.**

O `robots.txt` é a declaração formal do site sobre acesso automatizado.
Contorná-lo exige forjar identidade de navegador e ignorar um "não"
explícito — e o desfecho típico é **bloqueio de IP**, que nos custaria
até o acesso que hoje funciona.

VUNESP, FCC e IBFC já respondem **403 a qualquer sinal de automação**.
Insistir apenas antecipa o bloqueio definitivo.

**O caminho para essas três é comercial, não técnico:** são empresas com
canal de contato, e um site que divulga os concursos delas é do
interesse delas. Um pedido de acesso pode render mais que qualquer
raspador.

---

## 8. Rodada extra de sondagem (19/08/2026)

Testadas mais 30 fontes, em quatro frentes:

| Frente | Testadas | Aproveitadas |
|---|---|---|
| Tribunais (TCE-SP, TCE-MG, TCU, CNJ) | 4 | 0 — TCEs barram; TCU/CNJ não publicam concurso contábil |
| Bancas restantes (FGV, Cetro, FUNRIO, IADES, IBFC…) | 10 | 0 — as que permitem não expõem rota nem cargo |
| Portais regionais (Ache, Nova, Vagas Públicas…) | 8 | 0 — a maioria barra por robots |
| Plataformas de diário municipal (AMM-MG, AMUPE, FAMURS, AMP…) | 7 | 0 — ver abaixo |

**Diários municipais agregados** eram a aposta mais promissora: quatro
plataformas cobrem centenas de prefeituras e têm busca avançada com
campo de texto. Testei via GET, via POST e via navegador — **a busca não
devolve resultado por palavra-chave** em nenhum dos três. Sem isso,
restaria baixar edição por edição, o que já se mostrou inviável (§5).

**A Cetro tem API WordPress**, mas os posts são blog de contabilidade
("Escritório de Contabilidade em SP"), não concursos.

**Conclusão:** a cobertura por raspagem está saturada. O que existe de
alcançável já está ligado.

---

## 9. Onde ainda vale ampliar

1. **Bancas sem rota previsível (32)** — cada uma exige inspeção
   própria; comece pelas que mais aparecem nos nossos editais.
2. **API da Imprensa Nacional** — o DOU proíbe raspagem, mas a abertura
   desses dados é política pública declarada (Decreto 8.777/2016 e o
   Plano de Dados Abertos da própria IN). Caminho e modelo de pedido
   em **[ACESSO-DOU.md](ACESSO-DOU.md)**.
3. **Parceria com banca** — VUNESP, FCC e IBFC bloqueiam automação;
   acesso combinado resolveria o que a raspagem não alcança.

---

## 10. Agendamento

> **Por decisão do Patrick (19/08/2026), a varredura é MANUAL.**
> Não há nada agendado: o site só muda quando a varredura é disparada.

Para rodar:

```bash
python robo/atualizar.py --dry-run   # mostra o que acharia, sem gravar
python robo/atualizar.py             # grava data/editais.json
```
Depois, `git add data/ && git commit && git push` — o site republica só.

Ou dar duplo clique em **`varrer.bat`**, que faz os dois passos.

Uma varredura completa leva **cerca de 20 minutos** (20 bancas + 3
agregadores, com pausa de 1,5s entre requisições ao mesmo host).

### Se um dia quiser automatizar

**Na nuvem** — o workflow existe e está corrigido, só desativado:
```
gh workflow enable radar.yml --repo patrickalvesmg-jpg/cfc-radar-editais
```
Roda às 06:00 sem depender de máquina ligada e abre Pull Request para
revisão. As 8 últimas execuções antes de desativar foram bem-sucedidas.

**Na máquina** — agendar o `varrer.bat`:
```
schtasks /create /tn "Radar Concursos Contabilidade" /tr "CAMINHOarrer.bat" /sc daily /st 07:00
```
Só roda com o computador ligado, e publica direto (sem revisão prévia).

### Por que a frequência importa

O `status` de cada edital (aberto / encerrando / encerrado) é calculado
na varredura. Sem rodar por semanas, o site passa a mostrar como
"aberto" concurso cuja inscrição já fechou — o erro que mais prejudica
quem usa o radar. Se ficar muito tempo sem varrer, rode antes de
divulgar o link.
