# Ligar o cadastro ao ActiveCampaign

**JÁ ESTÁ CONFIGURADO E LIGADO** (20/08/2026), com o formulário 85 da
conta `cfcacademy`. Este documento fica como referência para trocar de
formulário ou depurar.

Valores em uso (`js/crm.js`):

```js
endpoint:   'https://cfcacademy.activehosted.com/proc.php'
formulario: '6A875235C00B6'   // campo "u"
numero:     '85'              // campo "f"
```

---

## Passo 1 — criar o formulário no AC

1. No ActiveCampaign, vá em **Site › Forms**.
2. **Create a form** → escolha o tipo **Inline form**.
3. Dê um nome (ex.: "Radar Concursos Contabilidade").
4. Escolha a **lista** onde os contatos vão cair.
5. Deixe **só o campo de e-mail** no formulário. O site não envia mais
   nada — nem nome, nem telefone.

## Passo 2 — copiar os dois valores

Clique em **Integrate** → aba **Simple Embed**. Vai aparecer um bloco
de código. Procure nele:

```html
<form ... action="https://SUACONTA.activehosted.com/proc.php" ...>
  <input type="hidden" name="u" value="27" />
```

Você precisa de:

| O que | Onde está | Exemplo |
|---|---|---|
| Endereço | o `action` do form | `https://cfcacademy.activehosted.com/proc.php` |
| Código (`u`) | o `value` do input `name="u"` | `6A875235C00B6` |
| Número (`f`) | o `value` do input `name="f"` | `85` |

> **`u` e `f` são DIFERENTES e é fácil errar.** O `u` é um código
> alfanumérico; o `f` é o número (o mesmo do `embed.php?id=`). Mandar o
> número nos dois faz o contato ser rejeitado **em silêncio**.

### Se você só tem o embed em JavaScript

O código `<script src=".../f/embed.php?id=85">` não mostra os valores.
Para achá-los, abra esse endereço no navegador e procure por
`name=\"u\"` — o `value` ao lado é o código.

## Passo 3 — preencher em `js/crm.js`

```js
export const CRM = {
  ativo: true,                                              // ← ligar

  endpoint: 'https://cfcacademy.activehosted.com/proc.php', // ← passo 2
  formulario: '27',                                         // ← passo 2
};
```

Publique e pronto. O próximo e-mail informado no site cai na sua lista.

---

## Como conferir se funcionou

Cadastre-se no site com um e-mail seu e veja se o contato aparece em
**Contacts** no AC (costuma levar alguns segundos).

Se não aparecer, na ordem:

1. **O formulário está publicado?** Formulário em rascunho não recebe.
2. **O `u` está certo?** É o número do formulário, não o da lista.
3. **Bloqueador de anúncios.** Extensões como uBlock barram domínios
   de automação de marketing. Teste numa janela anônima sem extensões.

---

## Duas coisas que valem saber

**Não dá para confirmar o envio pelo site — e nem pela resposta.**
Testado em 20/08/2026: o `proc.php` devolve **HTTP 302 para tudo**,
inclusive com o `u` errado e sem e-mail nenhum. O código de resposta
não distingue sucesso de falha, e o CORS ainda impede o navegador de
lê-lo. **A única confirmação confiável é olhar Contacts no painel.**

**O acesso é liberado de qualquer jeito.** O envio ao AC é
deliberadamente sem `await`: se o AC estiver fora do ar ou bloqueado,
a pessoa vê os editais do mesmo jeito. Perder um contato na lista é
ruim; travar quem acabou de informar o e-mail é pior.

---

## O que isto **não** faz

Não há conta nem login — **por decisão de produto**, não por
limitação. O site guarda apenas uma marca de "já liberou" no navegador
(um carimbo de data, sem o e-mail), e o e-mail vive só no
ActiveCampaign.

A consequência aceita: quem trocar de aparelho ou limpar o navegador
informa o e-mail de novo. O AC reconhece contato repetido e não
duplica, então isso não suja a lista.

O ganho, que é o motivo da escolha: **o site não é depositário de dado
pessoal**. Não há base nossa para vazar, exportar ou ter de excluir a
pedido do titular — a obrigação fica com o AC, que já tem contrato e
política para isso.
