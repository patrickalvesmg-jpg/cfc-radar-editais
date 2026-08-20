# Ligar o cadastro ao ActiveCampaign

**JÁ ESTÁ CONFIGURADO E LIGADO** (20/08/2026), com o formulário 85 da
conta `cfcacademy`. Este documento fica como referência para trocar de
formulário ou depurar.

Valores em uso (`js/crm.js`):

```js
endpoint: 'https://cfcacademy.activehosted.com/proc.php'
u:  '85'
f:  '85'
or: 'a0961656-11b8-4672-a291-19a683f688e7'
```

Além destes, o envio precisa de **`act=sub`** e **`v=2`**. Sem eles o AC
aceita a requisição e **ignora o cadastro em silêncio** — foi exatamente
o que aconteceu na primeira tentativa.

> **O `or` MUDA quando você edita o formulário no painel.** Ao mexer nos
> campos, pegue o embed de novo e reconfira este valor.

### Campos enviados

`firstname`, `email` e `phone`. Só o e-mail é obrigatório; os outros
vão apenas quando preenchidos — mandar vazio apagaria dado que a pessoa
já tivesse informado antes.

**O telefone precisa vir em formato internacional.** Testado: `83999991234`
é RECUSADO (`Forneça um número de telefone válido (formato +XXXXXXXXXXXXX)`);
`+5583999991234` é aceito. O `js/crm.js` converte sozinho — a pessoa digita
`(83) 99999-1234` e o site monta o `+55`. Número sem DDD é omitido, para não
derrubar o cadastro inteiro por causa do telefone.

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

| O que | Onde está |
|---|---|
| Endereço | o `action` do `<form>` |
| `u`, `f`, `or` | os `value` dos `<input type="hidden">` |

> **Pegue o embed do tipo "Simple Embed"**, que mostra o HTML do
> formulário. O embed em JavaScript (`<script src=".../embed.php?id=85">`)
> não expõe esses valores de forma confiável — tentar deduzi-los de
> dentro dele leva a erro.

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

**O envio É confirmável — mas só por JSONP.** Chamado com
`&jsonp=true` (como o próprio embed do AC faz), o `proc.php` responde
com JavaScript executável:

```js
_show_thank_you("85", "Obrigado por se cadastrar!", ...)   // sucesso
_show_error("85", "...")                                    // falha
```

O `js/crm.js` define essas duas funções antes de chamar, e assim sabe o
resultado. Um `fetch` comum não serviria: o CORS impede ler a resposta,
e o POST direto devolve **302 para tudo** — inclusive quando o cadastro
falha.

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
