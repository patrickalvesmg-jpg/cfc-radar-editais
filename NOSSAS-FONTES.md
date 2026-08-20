# Nossas fontes

De onde vêm os editais do Radar Concursos Contabilidade. Este documento
é o registro oficial: **as fontes listadas aqui são as que usamos**.

Números medidos em **20/08/2026**, sobre os 209 editais no ar.

> Para o histórico de tudo que já foi testado e **descartado** — com o
> motivo de cada um —, veja `FONTES.md`. Consulte-o antes de sondar
> portal novo, para não repetir teste já feito.

---

## Quanto cada fonte rende hoje

| Fonte | Editais | O que cobre |
|---|---|---|
| **PCI Concursos** (API) | 183 | Prefeituras de todo o Brasil |
| **IBGP Concursos** (API) | 11 | Prefeituras de MG |
| **CEBRASPE** (API) | 5 | Concursos federais e estaduais grandes |
| **Fundação FAFIPA** | 4 | Prefeituras do interior de PR, SC, MG |
| **Portais WordPress** | 3 | Agregadores, via `/wp-json/` |
| **ISET** | 2 | Prefeituras da BA |
| **JCM Concursos** | 1 | Prefeituras de MG |

**O PCI responde por 88% do acervo.** As demais rendem pouco em volume,
mas trazem o que ele não indexa — e é por isso que continuam ligadas.

Duas fontes ativas com zero editais hoje, o que é normal:

- **Consulplan** — banca dos Conselhos de Contabilidade (CRC-CE, CRC-RJ,
  CFC/Exame de Qualificação). Rende quando esses concursos abrem, e são
  os de maior relevância para o público da CFC Academy.
- **IBADE** — cobre RO, ES, AC e MT, onde o radar é mais fraco. Na
  medição a aba de inscrições abertas estava vazia; fica ligada
  esperando a próxima abertura.

---

## As fontes, uma a uma

### 1. PCI Concursos — o motor do acervo

```
https://www.pciconcursos.com.br/api/v1/concursos
```

API pública, **493 concursos numa única requisição**, com cargo em lista
real, datas em ISO e cidade estruturada. Substituiu a raspagem de 27
páginas que existia antes.

**Cuidado que custou caro:** o filtro contábil precisa rodar só sobre o
conteúdo do concurso. A barra lateral do PCI cita "Contador" em quase
toda página, e ao filtrar o HTML inteiro **4 de 4 vagas de psicólogo
eram aprovadas**. O corte da barra lateral está em `robo/fontes/pci.py`.

**Regra do produto:** o PCI é fonte, **nunca destino**. Nenhum link do
site aponta para lá — a URL vira o campo `procedencia`, que só o revisor
enxerga.

### 2. IBGP Concursos — API da própria banca

```
/rest/concurso/proximasInscricoes    lista os concursos
/rest/concurso/cargos/{id}           os cargos de cada um
```

Dá o cargo **por extenso**, o que permite separar coisas que o texto
corrido esconde: Contagem/MG abriu cinco cargos chamados "Auditor de
Controle Interno" — Ciências Contábeis, Direito, Engenharia Civil, TI e
Contador. Só dois são vaga contábil.

Duas armadilhas: a UF está em `concurso.nome`, não em `empresa.nome`; e
a rota `inscricoesAbertas` responde **500** no servidor deles.

### 3. CEBRASPE — API oficial

```
https://apis.cebraspe.org.br
```

Entrega cargo, vagas, salário e período de inscrição já estruturados —
por isso esses editais nascem com `confianca: alta`. É a **única fonte
com PDF do edital acessível**, vindo de `arquivosEdital[]`.

### 4. Fundação FAFIPA

```
https://www.fundacaofafipa.org.br/
```

Atende prefeituras do interior do PR, SC e MG, onde quase sempre há vaga
de contador. Rendimento medido: **8 de 22 concursos** têm cargo contábil,
e 6 deles não vinham do PCI — descoberta, não repetição.

Serve **iso-8859-1**: forçar utf-8 transformava "Fundação" em "Funda??o".

### 5. Bancas em plataforma comum — 24 bancas

`robo/fontes/bancas.py`. Várias bancas usam a mesma plataforma, com rota
`/informacoes/{id}/`. Acrescentar banca ali é **uma linha**, não um
arquivo novo.

FAFIPA · Objetiva · AvançaSP · Instituto Access · Exame Consultores ·
Fundep/Gestão de Concursos · Instituto Aplicativa · AMAUC · Consulpam ·
Instituto Vicente Nelson · ISET · AB Concursos · JCM · Auctor · MS
Concursos · COTEC/FADENOR · EducaPB · Selecon · IDCAP · Instituto Mais ·
GL Consultoria · Instituto Legalle · Instituto IBEPP · IMESO

### 6. Consulplan — a banca dos conselhos

```
https://www.institutoconsulplan.org.br
```

Organiza os concursos dos **Conselhos Regionais de Contabilidade** e o
Exame de Qualificação Técnica do CFC. Volume baixo, relevância altíssima
para o público da CFC Academy.

O `robots.txt` dele passou a proibir `/api/` — a listagem em HTML é o
único caminho.

### 7. IBADE

```
https://portal.ibade.selecao.site/edital
```

Cobre RO, ES, AC e MT. **Só as abas "abertos" e "futuros" entram**: em
"andamento" o certame está em curso mas a inscrição já fechou — o
concurso de Itarana estava lá com "resultado final" no texto.

O catálogo vivo fica no subdomínio da plataforma; `ibade.org.br` é só
vitrine institucional, com certames passados.

### 8. Portais WordPress

Concursos no Brasil e Edital Concursos Brasil, via `/wp-json/wp/v2/posts`.

**O gargalo aqui nunca foi coleta.** Medido: um firehose de 500 posts
levou de 8 a 15 candidatos contábeis, e ambos terminaram nos mesmos 2
editais. O problema era o filtro de cargo reconhecer 4 famílias enquanto
o filtro contábil aceita 14 — 9 de 12 cargos morriam ali.

**Regra: `PADRAO_CONTABIL` (config.py) e `CARGO` (portais_wp.py) são
filtros em série. Ampliar um sem o outro não muda nada.**

### 9. Querido Diário — diários municipais

```
https://api.queridodiario.ok.org.br
```

Rendimento baixo, e o motivo foi investigado, não suposto: a API não
suporta booleano, os trechos que ela devolve são arbitrários, e ao
baixar o texto completo de 20 editais recentes **nenhum** tinha vaga
contábil. Fica ligada porque o custo é baixo.

---

## Como acrescentar fonte nova

1. **Consulte o `FONTES.md` primeiro** — dezenas de portais já foram
   testados e descartados, com motivo.
2. **Confira o `robots.txt`** com `http_util.pode_acessar()`. Se proíbe,
   registre como descartado. Não contornamos: além da questão ética, o
   desfecho típico é bloqueio de IP, e perderíamos até o acesso que hoje
   funciona.
3. **Meça o rendimento** antes de implementar: quantos concursos a fonte
   lista, quantos têm cargo contábil, e quantos **não vinham do PCI**.
   Fonte que só repete o PCI não acrescenta.
4. **Sonde os dois domínios** — o institucional e o portal de inscrição.
   O IBADE passou despercebido porque a sondagem antiga bateu só no
   institucional.
5. Acrescente em `FONTES` no `atualizar.py`. O resto do robô não muda.

---

## Bancas que bloqueiam automação

| Banca | Situação |
|---|---|
| **VUNESP** | 403 em qualquer requisição automatizada |
| **FCC** | `robots.txt` proíbe `/concursos/` |
| **IBFC** | 403 |
| **Quadrix** | `robots.txt` barra robôs de IA por nome |
| **FUNDATEC** | AWS WAF com desafio de JavaScript |
| **Instituto AOCP** | **Não bloqueia** — o site é que não entrega dados sem navegador |

**O caminho para elas é comercial, não técnico.** Divulgar os concursos
delas é do interesse delas, então vale pedir acesso ou parceria. O AOCP
é o melhor candidato: não nos barra, só depende de tecnologia que o robô
não usa.
