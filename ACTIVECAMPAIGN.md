# Ligar o cadastro ao ActiveCampaign

O código já está pronto. Falta preencher **quatro valores** em
`js/crm.js` — tudo copiado de uma tela só do painel do AC.

Enquanto `ativo: false`, nada é enviado e o site funciona normalmente.

---

## Passo 1 — criar o formulário no AC

1. No ActiveCampaign, vá em **Site › Forms**.
2. **Create a form** → escolha o tipo **Inline form**.
3. Dê um nome (ex.: "Radar Concursos Contabilidade").
4. Escolha a **lista** onde os contatos vão cair.

## Passo 2 — criar os dois campos personalizados

O AC já tem nome e e-mail. Estado e interesse precisam ser criados,
e são eles que deixam você segmentar depois ("todo mundo da PB",
"quem quer ser auditor").

Ainda no editor do formulário, arraste um campo novo para cada:

| Campo | Tipo sugerido | Opções |
|---|---|---|
| **Estado** | Dropdown | as 27 UFs (ou texto livre) |
| **Cargo de interesse** | Dropdown | `contador`, `auditor`, `analista`, `qualquer` |

> Use exatamente esses quatro valores no cargo de interesse — são os
> que o formulário do site envia.

## Passo 3 — copiar os valores

Clique em **Integrate** → aba **Simple Embed**. Vai aparecer um bloco
de código. Procure nele:

```html
<form ... action="https://SUACONTA.activehosted.com/proc.php" ...>
  <input type="hidden" name="u" value="27" />
  ...
  <input type="text" name="field[3,0]" />   ← Estado
  <input type="text" name="field[4,0]" />   ← Cargo de interesse
```

Você precisa de:

| O que | Onde está | Exemplo |
|---|---|---|
| Endereço | o `action` do form | `https://cfcacademy.activehosted.com/proc.php` |
| ID do formulário | o `value` do input `u` | `27` |
| Campo Estado | o `name` do campo | `field[3,0]` |
| Campo Interesse | o `name` do campo | `field[4,0]` |

## Passo 4 — preencher em `js/crm.js`

```js
export const CRM = {
  ativo: true,                                              // ← ligar

  endpoint: 'https://cfcacademy.activehosted.com/proc.php', // ← passo 3
  formulario: '27',                                         // ← passo 3

  campos: {
    estado: 'field[3,0]',                                   // ← passo 3
    interesse: 'field[4,0]',                                // ← passo 3
  },
};
```

Publique e pronto. O próximo cadastro no site cai na sua lista.

---

## Como conferir se funcionou

Cadastre-se no site com um e-mail seu e veja se o contato aparece em
**Contacts** no AC (costuma levar alguns segundos).

Se não aparecer, na ordem:

1. **O formulário está publicado?** Formulário em rascunho não recebe.
2. **O `u` está certo?** É o número do formulário, não o da lista.
3. **Bloqueador de anúncios.** Extensões como uBlock barram domínios
   de automação de marketing. Teste numa janela anônima sem extensões.
4. **Os `field[x,y]` batem?** Se o nome do campo estiver errado, o
   contato entra mesmo assim, só que sem estado e interesse.

---

## Duas coisas que valem saber

**Não dá para confirmar o envio pelo site.** O AC não responde a
requisição vinda de outro domínio de forma legível (é o CORS). Por
isso o site manda e segue em frente. A consequência prática: se o
envio falhar, você não fica sabendo pelo site — daí o teste acima.

**O cadastro local acontece de qualquer jeito.** O envio ao AC é
deliberadamente sem `await`: se o AC estiver fora do ar ou bloqueado,
a pessoa entra na plataforma do mesmo jeito. Perder um contato na
lista é ruim; travar o acesso de quem se cadastrou é pior.

---

## O que isto **não** faz

Este caminho capta contato e alimenta suas automações de e-mail. Ele
**não faz login de verdade** — o ActiveCampaign é ferramenta de
marketing, não sistema de contas: não guarda senha nem sessão.

Hoje a "conta" continua vivendo no navegador da pessoa
(`js/sessao.js`, localStorage). Se ela trocar de aparelho ou limpar o
navegador, a conta some — mas **o contato permanece no AC**, que é o
ativo que interessa.

Para login real (a pessoa volta dias depois e entra com senha), o
caminho é um backend de autenticação — Supabase é o mais direto. Os
contatos já captados aqui não se perdem nessa migração.
