# Ligar o cadastro ao ActiveCampaign

O código já está pronto. Falta preencher **dois valores** em
`js/crm.js` — os dois na mesma tela do painel do AC.

Enquanto `ativo: false`, nada é enviado e o site funciona normalmente.

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
| ID do formulário | o `value` do input `u` | `27` |

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

**Não dá para confirmar o envio pelo site.** O AC não responde a
requisição vinda de outro domínio de forma legível (é o CORS). Por
isso o site manda e segue em frente. A consequência prática: se o
envio falhar, você não fica sabendo pelo site — daí o teste acima.

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
