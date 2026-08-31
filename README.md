# Radar Concursos Contabilidade · CFC Academy

Plataforma que reúne editais de concursos públicos da área contábil no Brasil.
Esta entrega é o **front-end** — a captura automática dos editais é a fase 2.

> **Demonstração.** Os editais são exemplos realistas, **não são dados reais**.
> O cadastro e o login são simulados no navegador (localStorage), sem backend.

---

## Como navegar

| Página | Arquivo | Acesso |
|---|---|---|
| Landing (vitrine) | `index.html` | Público |
| Criar conta | `cadastro.html` | Público |
| Entrar | `login.html` | Público |
| Plataforma | `app.html` | **Exige sessão** |

**Fluxo:** a landing mostra **3 editais completos** e o restante borrado, com o
paywall por cima. Ao criar conta, todos os editais são liberados em `app.html`.
Quem tenta abrir `app.html` sem sessão é mandado para o cadastro e volta para lá
depois de entrar.

Para testar de novo do zero, limpe o `localStorage` do site (DevTools →
Application → Local Storage) ou use uma janela anônima.

---

## Rodar localmente

Os módulos ES e o `fetch` do JSON não funcionam abrindo o arquivo direto
(`file://`). Suba um servidor estático na pasta:

```bash
npx serve .
# ou
python -m http.server 8080
```

E abra `http://localhost:8080`.

---

## Estrutura

```
index.html        landing pública, amostra + paywall
cadastro.html     criar conta
login.html        entrar
app.html          plataforma (protegida)

css/
  tokens.css      variáveis — ponto único de calibração da identidade
  base.css        reset, tipografia, primitivos (.btn .badge .chip .campo)
  app.css         componentes (topbar, hero, cards, filtros, paywall, auth)

js/
  sessao.js       sessão simulada em localStorage
  comum.js        formatação, ordenação e o card de edital (compartilhado)
  landing.js      landing pública
  auth.js         cadastro e login
  app.js          plataforma

data/
  editais.json          os editais capturados pelo robô (dados reais)
  organizadoras.json    bancas, com quantos editais cada uma tem AGORA
  bancas-catalogo.json  mapa permanente das 378 bancas do Brasil —
                        inclui as sem concurso contábil aberto, que são
                        reserva, não descarte
  editais-pdf/          cópia do PDF de cada edital + indice.json
```

Sem build, sem npm, sem framework — HTML/CSS/JS puro com módulos ES.

---

## Identidade visual

Documentada em [`IDENTIDADE-VISUAL.md`](IDENTIDADE-VISUAL.md). Resumo:

- Tema **dark**: preto esverdeado `#0a0f0a` com acento **verde-lima `#9FE31A`**
- Fontes **Archivo** (títulos) + **Sora** (corpo) + **JetBrains Mono** (horários)
- Conceito: **painel de monitoramento** — varredura, feed ao vivo, status

**Regra:** nenhuma cor literal fora de `css/tokens.css`.

---

## Atualização automática

> **A varredura é manual, por decisão do projeto.** Não há nada
> agendado: o site só muda quando alguém roda `varrer.bat` ou
> `python robo/atualizar.py`. Rode antes de divulgar o link — o
> status "aberto/encerrado" de cada edital é recalculado na varredura.

O robô varre 7 fontes (bancas organizadoras, PCI, agregadores) e reúne
os concursos da área contábil. Mapa completo das fontes, do que já foi
testado e do que não vale repetir: **[FONTES.md](FONTES.md)**.

Para religar o agendamento, veja a seção 10 do FONTES.md.

Nada vai ao ar sem sua aprovação: data de inscrição errada prejudica
candidato de verdade, e extração automática erra.

Detalhes, filtro e processo de revisão em [`robo/README.md`](robo/README.md).

```bash
python robo/atualizar.py --dry-run   # ver o que acharia, sem gravar
```

---

## Pendências para a fase 2

- Ampliar fontes (bancas, diários estaduais, API oficial da Imprensa Nacional)
- Autenticação real — `js/sessao.js` é substituído por completo
- Banco de dados e painel admin para cadastrar editais
- Alertas por e-mail/WhatsApp
- Logo oficial da CFC Academy (hoje há um ícone de radar como marcador)
- Links reais do curso e da comunidade
- Definir domínio final
