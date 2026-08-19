# Robô de captura — Radar Concursos Contabilidade

Varredura automática de editais de concurso da área contábil.
Roda no GitHub Actions, **sem depender de nenhum computador ligado**.

```
GitHub Actions (cron diário 06:00 BRT)
   └─ python robo/atualizar.py
        ├─ consulta as fontes
        ├─ filtra o que é concurso contábil
        ├─ extrai campos e mescla com o publicado
        └─ grava data/editais.json
   └─ abre Pull Request  ← você revisa e aprova
   └─ merge → GitHub Pages republica sozinho
```

---

## Rodar na mão

```bash
python robo/atualizar.py --dry-run      # mostra o que acharia, sem gravar
python robo/atualizar.py                # grava data/editais.json
python robo/atualizar.py --limite 50    # amplia a busca por consulta
```

Sem dependências: só a biblioteca padrão do Python 3.12+.

---

## Fontes

| Fonte | O que cobre | Situação |
|---|---|---|
| **CEBRASPE** (`apis.cebraspe.org.br`) | Concursos da banca, com cargo/vagas/salário/prazo estruturados | Ativa |
| **PCI Concursos** | Prefeituras — maior volume | Ativa — é o que mais rende |
| **Portais WordPress** | Concursos no Brasil + Edital Concursos Brasil, via `/wp-json/` | Ativa — volume baixo |
| **Consulplan** | Banca dos **Conselhos de Contabilidade** (CRC-CE, CRC-RJ, CFC/EQT) e de prefeituras | Ativa |
| **Querido Diário** (`api.queridodiario.ok.org.br`) | Diários oficiais **municipais** de todo o Brasil | Ativa — rendimento baixo, ver abaixo |

### Por que os diários municipais rendem pouco (investigado, não suposto)

Era a aposta natural para "vagas em prefeituras". Não funciona bem, e o
motivo **não é o filtro**:

1. A API **não suporta booleano**. `"a" AND b` vira busca livre: de 40
   resultados, 27 falavam de concurso e só 1 citava contador.
2. Os `excerpts` trazem um trecho **arbitrário** do diário — cláusula de
   fotocópia, referência a lei — quase nunca a tabela de cargos.
3. Baixando o **texto completo** de 20 editais de abertura recentes
   (média de 112 mil caracteres), **nenhum** tinha vaga contábil. Os 4
   que citavam "contabilidade" eram listas de classificação de certame
   já encerrado.

Conclusão: concurso municipal para contador é raro, e quando sai vem num
PDF cuja tabela de cargos a API não indexa de forma pesquisável.
**O volume do site vem das bancas**, que publicam cargo, vaga e salário
já estruturados.

### Bancas que ficaram de fora

| Banca | Motivo |
|---|---|
| **FCC** | `robots.txt` proíbe `/concursos/` — justamente a área necessária |
| **VUNESP** | Responde **403** a qualquer automação, inclusive no `robots.txt` |
| **IBFC** | Idem |

Incluí-las exigiria contornar bloqueio explícito. Se forem importantes,
o caminho é pedir acesso/parceria à banca — não burlar.

### Por que o Diário Oficial da União não está aqui

O `robots.txt` de `in.gov.br` é **`Disallow: /`** — proíbe raspagem
automatizada do site inteiro, para qualquer agente. O robô respeita isso
(`http_util.pode_acessar`), então a fonte foi removida.

Para incluir o DOU de forma legítima há dois caminhos, ambos fora do que
o robô faz sozinho hoje:

1. Solicitar acesso à API oficial da Imprensa Nacional; ou
2. Cadastrar o edital à mão quando for concurso federal relevante.

O Querido Diário, ao contrário, publica `Allow: /` com
`Content-Signal: use=reference` — que é exatamente nosso uso: citamos o
trecho e linkamos de volta para a fonte.

---

## O filtro

Três camadas, validadas contra dados reais (2.834 publicações do DOU e
centenas de diários municipais):

1. **É concurso?** — "concurso público", "processo seletivo", "edital de abertura"
2. **É contábil?** — contador, ciências contábeis, auditor fiscal, analista contábil…
3. **Não é ruído?** — descarta duas famílias:
   - *compras públicas*: licitação, extrato de contrato, pregão
   - *atos de concurso já existente*: **convocação, nomeação, homologação,
     resultado, lista de aprovados**

A camada 3 é a mais importante e a menos óbvia. Um "EDITAL DE CONVOCAÇÃO
— ANALISTA CONTÁBIL" contém as palavras *concurso público* **e**
*contador*, mas a inscrição fechou meses atrás. Publicar isso como
oportunidade aberta enganaria o candidato — foi um falso positivo real
capturado durante o desenvolvimento.

O filtro é **conservador de propósito**: prefere perder um edital (que o
revisor acrescenta à mão) a publicar lixo com aparência de concurso.

### Expectativa realista de volume

Concurso para contador **não abre todo dia**. É normal a varredura rodar
e não achar nada — nesse caso ela não abre PR nenhum. Rodadas com zero
resultado não significam robô quebrado.

Se quiser conferir se ainda funciona, rode com `--dry-run`: o log mostra
quantos documentos cada consulta trouxe. Se as consultas trazem
documentos mas o filtro zera **sempre por semanas**, aí vale investigar.

---

## Links: o radar nunca aponta para concorrente

Regra do produto: **nenhum link do site vai para outra plataforma de
concurso**. Mandar visitante ao PCI é entregar a audiência ao concorrente.

- O card abre `edital.html?id=...` — página interna com todos os dados.
- O único link externo é **onde a inscrição acontece** (banca ou órgão),
  extraído do texto da fonte. Em concurso municipal isso é sempre a banca
  organizadora: verificado, 10 de 10 não apontam para `.gov.br`.
- Sem endereço confirmável, a página orienta a procurar o edital oficial.
- A URL do agregador vira `procedencia` — auditoria do revisor, nunca exibida.

A blocklist vive em três lugares e precisa ser respeitada por qualquer
fonte nova: `js/edital.js` (BLOQUEADOS), `robo/fontes/pci.py` e
`robo/fontes/portais_wp.py` (DOMINIO_PROIBIDO).

## Links de inscrição são reconciliados

Edital já revisado normalmente não é tocado pelo robô. A **única
exceção** é o `siteInscricao`: se estiver vazio e uma fonte nova trouxer
o endereço, ele é preenchido. É acréscimo, não substituição — um edital
sem link é inútil para quem quer se inscrever.

## Revisão (o passo humano)

O robô **nunca publica sozinho**. Ele abre um PR, e cada item novo entra
com `"revisado": false`.

Ao revisar um edital no `data/editais.json`:

1. Confira nos campos — o `_trecho` traz o texto de origem, então dá para
   validar sem abrir o diário oficial;
2. Corrija o que estiver errado (cargo, salário, datas);
3. Marque **`"revisado": true`**.

A partir daí o robô **não sobrescreve mais** os campos curados
(`cargo`, `cidade`, `salario`, `vagas`, `dataProva`, `banca`, `uf`…).
Ele continua só atualizando o `status` conforme o prazo corre.

Essa regra existe para que a correção manual não seja desfeita na
execução seguinte.

### Fonte estruturada vence extração por regex

Quando a fonte entrega o campo pronto (o CEBRASPE dá cargo, vagas,
salário e período de inscrição), esse valor é usado direto. A regex do
`extrair.py` só entra quando a fonte não informa — é o caso dos diários
municipais, que são texto corrido.

Por isso os editais do CEBRASPE nascem com `confianca: alta`.

### Campo `confianca`

| Valor | O que significa |
|---|---|
| `alta` | Tem cargo, período de inscrição e salário |
| `media` | Falta um desses |
| `baixa` | Só sabemos que há algo contábil publicado — **revise primeiro** |

---

## Arquivos

```
robo/
  config.py        termos do filtro, bancas, UFs — calibração fica aqui
  http_util.py     rede: robots.txt, pausa entre requisições, tolerância a falha
  extrair.py       texto bruto → campos estruturados
  atualizar.py     orquestra e mescla preservando a curadoria
  fontes/
    cebraspe.py
    querido_diario.py
```

Para **acrescentar uma fonte**: crie `fontes/nova.py` com uma função
`coletar()` que devolva dicionários com `fonte`, `titulo`, `orgao_bruto`,
`texto`, `url`; e registre em `FONTES` no `atualizar.py`. O resto do
pipeline não muda.

---

## Boas práticas embutidas

- **robots.txt é consultado** antes de cada requisição
- **1,5s de pausa** entre chamadas ao mesmo host
- **User-Agent identificado**, com link do projeto para contato
- **Falha de fonte não derruba a varredura** — roda sem supervisão
- **Nada é publicado sem revisão humana**
