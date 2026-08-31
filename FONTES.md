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

### AcheConcursos — sondado em 31/08/2026, NÃO vira fonte

O Patrick pediu para avaliar
`acheconcursos.com.br/busca-concursos/cargo-contador`. Diferente do
QConcursos, este **permite** a leitura: o `robots.txt` traz `Allow: /`
e a página de busca não está em nenhum `Disallow` (só `/premium/`,
`/apostilas/`, `/forum/` e downloads). O `http_util.pode_acessar`
confirma. Ou seja: dava para usar — e ainda assim não compensa.

**O que ele tem:** uma tabela com concurso, abertura, prazo, vagas e
"Salários **Até**", e uma página por concurso que linka o site oficial
da banca (FADE-UFPE, CEBRASPE, CESGRANRIO, Instituto Mais).

**O que rende, medido:** 70 concursos distintos somando seis buscas por
cargo contábil (contador, técnico em contabilidade, auditor fiscal,
fiscal de tributos, analista contábil, controlador interno). Desses,
**apenas 3 são concurso contábil que não temos**: TRANSPETRO
(CESGRANRIO), Concurso Unificado PI e FUNDACI Ilhabela. Um quarto
candidato, o CRECI-SP, não cita nenhum cargo contábil — seria falso
positivo.

**Bancas novas: nenhuma.** Visitei as 66 páginas de concurso e extraí
todo domínio externo: 49 domínios, 21 fora do catálogo. Depois de tirar
CDN, S3 e o fornecedor do site (`desenvolveweb.com.br`, que aparecia 66
vezes), sobraram 14 candidatas — e todas já eram conhecidas:

- 7 já estavam em `organizadoras.json`, vindas dos nossos editais;
- 5 eram subdomínios de `selecao.net.br` de bancas que já temos;
- `fundep.selecao.net.br` é a FUNDEP, catalogada como
  `gestaodeconcursos.com.br`;
- `fundacaounespar.org.br` é a **própria Fundação FAFIPA** num segundo
  domínio — o site responde "Fundação FAFIPA | CNPJ 05.566.804/0001-76".
  Isso virou uma linha no `organizadoras.CANONICO`: sem ela o radar
  exibiria "Fundacaounespar" como se fosse outra banca.

**Conclusão: fica de fora.** É agregador (mesma natureza do PCI, que já
lemos por API), está na blocklist de link por ser concorrente, e o
ganho seria 3 editais contra o custo de mais uma fonte para manter. O
próprio `FONTES.md` já registrava que ele não tem `/wp-json`.

**O que vale aproveitar dele:** os 3 concursos acima, cadastrados à
mão, e a confirmação de que a cobertura de bancas está boa — uma fonte
independente não achou nenhuma organizadora que o catálogo não tivesse.

E um alerta sobre a coluna dele: **"Salários Até" é o teto do
concurso**, o mesmo número que causou o erro de Floresta/PE (ver
`robo/auditar_salario.py`). Se um dia essa fonte for ligada, o valor
dela entra como não verificado, nunca como salário do cargo.

### QConcursos — testado em 31/08/2026, fora (não repetir)

O Patrick pediu para incluir o *Mapa de Concursos Públicos* do
QConcursos (`qconcursos.com/questoes-de-concursos/mapa-concursos-publicos`).
**Não dá, e não deveríamos mesmo que desse.** Medido, não suposto:

| Requisição | Resposta |
|---|---|
| `robots.txt` com nosso User-Agent | **403** |
| `robots.txt` com User-Agent de Chrome real | **403** |
| a própria página do mapa, com Chrome real | **403** |

O 403 vem do Cloudflare e alcança **até o `robots.txt`** — o site nega
a leitura do próprio arquivo que declara o que é permitido. É a mesma
assinatura de VUNESP, FCC e IBFC: bloqueio deliberado e ativo, não
descuido de configuração.

Contornar exigiria proxy residencial e resolução do desafio do
Cloudflare. Além de romper um "não" explícito, seria uma corrida:
funciona umas semanas, eles apertam, e o robô que roda sozinho toda
segunda passa a **falhar em silêncio** — o defeito mais caro que este
projeto já teve (ver o `\b` virando backspace).

**E não perdemos nada.** O QConcursos é agregador, a mesma natureza do
PCI que já lemos por API — e por isso já está na blocklist de
`js/edital.js`, `robo/conferir.py` e `robo/fontes/pci.py`: nenhum link
do radar pode mandar visitante para plataforma concorrente. O que ele
lista sai das **bancas**, que é onde o radar já busca, com cargo por
extenso e salário estruturado — dado melhor do que o agregador daria.

Onde está o ganho real de cobertura: nas bancas de
`data/bancas-catalogo.json` ainda não sondadas (296 em reserva), que
são acessíveis e oficiais.

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

## IBGP Concursos — fonte própria desde 20/08/2026

`robo/fontes/ibgp.py`. **Rende 13 cargos contábeis em 8 dos 20 concursos.**

Isto **corrige a avaliação anterior** registrada aqui, de que o IBGP
rendia "1 de 17 e esse 1 já vinha do PCI". Aquela medição usava a rota
errada: olhava só os concursos com inscrição aberta, e o volume está em
`proximasInscricoes` — os que ainda vão abrir.

| Rota | O que dá |
|---|---|
| `/rest/concurso/proximasInscricoes` | lista os concursos (sem os cargos) |
| `/rest/concurso/cargos/{id}` | os cargos, na chave `cargos` |
| `/rest/concurso/inscricoesAbertas` | **HTTP 500** no servidor deles |

Duas armadilhas medidas:

- A listagem traz só `totalCargos: 3`, nunca os nomes. Uma requisição por
  concurso é inevitável para saber se há vaga contábil.
- **A UF está em `concurso.nome`, não em `empresa.nome`.** "MUNICÍPIO DE
  SÃO JOÃO DEL-REI" não tem estado; "…DEL-REI/MG" tem. Sem olhar os dois
  campos, 5 concursos ficam sem UF e somem do mapa.

### Cargo com especialidade: a formação declarada manda

Contagem/MG abriu CINCO cargos "Auditor de Controle Interno" — Ciências
Contábeis, Direito, Engenharia Civil, Tecnologia da Informação e
Contador. Todos casam em `PADRAO_CONTABIL` por causa de "controle
interno", mas só dois são vaga contábil.

Por isso o `_NAO_CONTABIL` em `ibgp.py`. Vale também para "Agente Fiscal
de **Saneamento**", que é fiscalização sanitária, não tributária. Isso só
é possível porque a API dá o cargo por extenso — de texto corrido não há
como distinguir.

## Portais WordPress: o gargalo era o funil, não a coleta

Investigado a fundo em 20/08/2026. **Aumentar volume sozinho rende
zero:** medido, um firehose de 500 posts levou de 8 para 15 candidatos
com conteúdo contábil, e ambos terminaram nos **mesmos 2 editais**. Tudo
morria depois da coleta.

**A causa:** o `CARGO` de `portais_wp.py` reconhecia 4 famílias de cargo,
enquanto o `PADRAO_CONTABIL` aceita 14. O post passava no filtro contábil
e era descartado por "não nomear cargo" — sendo que o cargo estava lá.
Verificado: **9 de 12 cargos contábeis eram perdidos assim** (Fiscal de
Tributos, Agente de Arrecadação, Auxiliar Contábil, Auditor Fiscal,
Controlador Interno, Tesoureiro, Analista Tributário…). Corrigido.

**Regra que fica: ao mexer no `PADRAO_CONTABIL`, mexer no `CARGO` junto.**
São dois filtros em série; ampliar um sem o outro não muda nada.

### Testado e descartado nos portais (não repetir)

| O que | Por quê |
|---|---|
| Busca com termo de duas palavras | A busca do WordPress é **OR**, não AND. `search=auditor fiscal` devolve 661 resultados que não têm nem "auditor" nem "fiscal". Só termo de UMA palavra filtra. |
| Taxonomia `cargo` | Existe no `concursosnobrasil.com`, mas tem 4 termos (Fonoaudiólogo, Médico, Professor, Psicólogo) e nenhum contábil. |
| Categoria temática | As categorias são geográficas (sp, mg) e editoriais (notícia, loterias). `tags` está vazio. |
| Campo `meta` | Só `{"footnotes": ""}`. Nada de salário, vagas ou PDF. |
| `concursosnobrasil.com.br` | Espelho do `.com` — os links redirecionam. Zero valor novo. |
| `blog.grancursosonline.com.br` | Responde, mas mistura matéria-resumo ("11 editais publicados") com edital único, e o órgão sai corrompido. Exigiria parser próprio. |
| `concurseiro24horas` | 7 posts, último de 2024. Morto. |
| concursosaz, opcaoconcursos, concursosemfoco | `robots.txt` proíbe. |
| pciconcursos, jcconcursos, novaconcursos, acheconcursos | Sem `/wp-json`. |

### O que ainda dá para ganhar ali

`class_list` traz UF e município já normalizados
(`['category-am', 'cidade-manaus']`) e era ignorado — mais confiável que
ler "(AM)" do título, porque muitos títulos escrevem "Prefeitura de
Manaus AM", sem parênteses. Já ligado em `_uf_cidade()`.

Paginação (`per_page=100`, teto real; 150 dá HTTP 400) e leitura de data
com hora ("as 16h do dia 13 de agosto") continuam pendentes — valem
quando o acervo precisar de mais volume.

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
