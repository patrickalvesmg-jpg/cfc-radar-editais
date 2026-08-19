# Como conseguir acesso ao DOU (Imprensa Nacional)

O `robots.txt` de `in.gov.br` é **`Disallow: /`** — proíbe raspagem
automatizada de todo o site. Mas o conteúdo do Diário Oficial é público
por lei, e há caminhos oficiais para obtê-lo.

---

## O argumento que sustenta o pedido

O **Decreto nº 8.777/2016** instituiu a Política de Dados Abertos do
Executivo Federal. Em cumprimento a ele, a Imprensa Nacional criou seu
**Plano de Dados Abertos (PDA)**, e o próprio site declara:

> *"...priorizando a abertura dos dados do **Diário Oficial da União**,
> fonte primária da informação oficial, cujas páginas, digitalmente
> certificadas, já se encontram disponibilizadas ao público para
> pesquisa livre e gratuita."*

Ou seja: **a abertura desses dados é política pública declarada**, não
um favor. O pedido não é por exceção — é por acesso ao que já deveria
estar disponível em formato aberto.

---

## Caminho 1 — Fala.BR (o mais indicado)

Plataforma oficial de acesso à informação (Lei 12.527/2011).
**https://falabr.cgu.gov.br**

- Registre como **Pedido de Acesso à Informação**
- Órgão destinatário: **Imprensa Nacional**
- Prazo legal de resposta: **20 dias**, prorrogável por mais 10
- Gera número de protocolo e resposta formal — se negarem, cabe recurso

É o caminho com força legal. Os outros são complementares.

## Caminho 2 — contato direto

| Canal | Contato |
|---|---|
| Coordenação-Geral de TI (CGTI) | `corti@in.gov.br` |
| Diretoria-Geral | `dirge@in.gov.br` |
| Telefone | (61) 3441-9404 · (61) 3441-9866 |

A **CGTI** é quem opera os sistemas — é o interlocutor certo para
falar de API, formato de dados e volume de acesso.

## Caminho 3 — Serviço de Informação ao Cidadão (SIC)

`gov.br/imprensanacional/pt-br/acesso-a-informacao` → seção SIC.
Mesma base legal do Fala.BR, com atendimento próprio do órgão.

---

## O que pedir (seja específico)

Pedido genérico costuma render resposta genérica. Peça:

1. **Acesso programático** (API, webservice ou dump diário) às matérias
   do DOU, seções 1, 2 e 3;
2. **Formato estruturado** — JSON ou XML, não PDF;
3. **Filtro por assunto ou palavra-chave**, ou ao menos a íntegra do
   dia para filtrarmos localmente;
4. **Condições de uso**: limite de requisições, necessidade de
   credencial, exigência de citar a fonte.

Explique o uso: *plataforma que reúne concursos públicos da área
contábil, sem fim comercial direto sobre o dado, com link de volta à
fonte oficial*. Isso costuma facilitar — é exatamente o uso que a
política de dados abertos quer estimular.

---

## Modelo de texto para o pedido

> Solicito informação sobre a existência de acesso programático (API,
> webservice ou arquivo estruturado) às matérias publicadas no Diário
> Oficial da União, nas seções 1, 2 e 3.
>
> A solicitação tem por base o Decreto nº 8.777/2016 e o Plano de Dados
> Abertos da Imprensa Nacional, que prioriza expressamente a abertura
> dos dados do DOU.
>
> A finalidade é reunir, em plataforma de consulta pública e gratuita,
> os editais de concurso público voltados à área contábil, com
> indicação e link para a fonte oficial em cada registro.
>
> Caso exista o serviço, solicito as condições de uso: forma de
> credenciamento, limites de requisição e formato disponível. Caso não
> exista, solicito orientação sobre a via adequada para obtenção
> regular desses dados em formato aberto.

---

## Enquanto não há resposta

O radar **não raspa o in.gov.br** — o `http_util.pode_acessar()`
respeita o `Disallow: /` e bloqueia qualquer tentativa.

Concurso federal continua chegando por outras vias: **CEBRASPE** (API
própria), **PCI** e os agregadores. O que se perde são órgãos federais
menores, que publicam só no DOU.
