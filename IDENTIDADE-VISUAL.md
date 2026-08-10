# Identidade Visual — CFC Academy

Documento de referência da estética da marca, verificada no código-fonte das
propriedades existentes e aplicada nesta plataforma.

## Fontes verificadas

A identidade não foi inventada: foi extraída dos arquivos reais da CFC Academy.
As quatro propriedades abaixo usam **exatamente os mesmos tokens**, o que
confirma que o sistema já estava consolidado antes desta plataforma.

| Propriedade | Caminho |
|---|---|
| CFC Questões (landing) | `landing-pages/cfc-questoes/index.html` |
| CFC Express (landing) | `landing-pages/cfc-express/index.html` |
| Quiz CFC | `landing-pages/quiz-cfc/index.html` |
| Mapa de Concursos (v1) | `mapa-concursos/css/variables.css` |

---

## 1. Cor

O sistema é **dark-first**. Não existe versão clara da marca.

### Superfícies
| Token | Hex | Uso |
|---|---|---|
| `--preto` | `#0a0f0a` | Fundo raiz. Preto esverdeado, nunca preto puro. |
| `--preto-2` | `#0f1710` | Faixas e barras (elevação 1) |
| `--carvao` | `#141c14` | Cards e painéis (elevação 2) |
| `--carvao-2` | `#18211a` | Hover / aninhado |
| `--carvao-3` | `#1e2a1f` | Inputs e chips |

### Acento
| Token | Hex | Uso |
|---|---|---|
| `--lima` | `#9FE31A` | **A cor da marca.** Botões, destaques, números. |
| `--lima-esc` | `#76A41C` | Gradientes e estados pressionados |
| `--lima-claro` | `#B6EF4A` | Hover sobre fundo escuro |

### Tinta
`--branco #F3F7F0` (texto principal) · `--cinza #9aa79a` (secundário) ·
`--cinza-esc #5f6b5f` (terciário, labels)

### Regra crítica de contraste
**Texto sobre lima é sempre escuro (`--preto`), nunca branco.** O lima é
altamente luminoso; texto branco sobre ele fica ilegível. Essa regra vale em
todos os botões primários da marca e foi mantida aqui.

### Regra de disciplina do acento
O lima é reservado a **"aberto / ativo / positivo"**. Estados concorrentes usam
cores próprias para não diluir o acento da marca:

- `--warn #E3B341` — encerrando, previsto, a confirmar
- `--crit #EF6A6A` — encerrado
- `--info #5BC8E3` — datas de prova, andamento

Se tudo fosse lima, nada seria destaque.

---

## 2. Tipografia

| Papel | Fonte | Pesos | Aplicação |
|---|---|---|---|
| Display | **Archivo** | 600–900 | Títulos, botões, números, badges |
| Corpo | **Sora** | 400–800 | Texto corrido, labels, parágrafos |
| Mono | **JetBrains Mono** | 400–500 | Horários de captura, numeração (novo nesta plataforma) |

Características do sistema:
- Títulos com `letter-spacing: -.02em` e `line-height: 1.06` — compactos e densos.
- Botões em **CAIXA ALTA**, peso 800, Archivo.
- `eyebrow` (rótulo acima do título): caixa alta, `letter-spacing: .18em`,
  precedido de um ponto lima pulsante — **assinatura mais reconhecível da marca**.
- Numerais tabulares (`.num`) obrigatórios em salários e datas, para alinhamento
  em coluna.

---

## 3. Assinaturas visuais da marca

Elementos recorrentes que tornam a CFC reconhecível:

1. **Grid mesh de fundo** — malha de 52×52px em lima translúcido, com máscara
   radial. Aparece em heros e blocos de destaque.
2. **Glow do lima** — `box-shadow` colorido em botões e elementos ativos.
   Dá a sensação de "fósforo aceso".
3. **Ponto pulsante** (`@keyframes blink`) — indica atividade ao vivo.
4. **Gradiente de card** — `linear-gradient(165deg, --carvao, --preto-2)`,
   nunca cor chapada.
5. **Radial lima no canto superior** dos heros.

---

## 4. O que esta plataforma acrescentou

A identidade da CFC já existia; o conceito **"painel de monitoramento"** é a
extensão criada aqui para diferenciar a plataforma das landing pages de venda.

- **Linha de varredura** (`.scanner::after`) — atravessa o painel de capturas.
- **Feed ao vivo** — capturas recentes com horário em fonte mono.
- **Trilho de status** na borda esquerda dos cards, para leitura periférica.
- **Contagem crescente** dos números do topo.
- **Barra de pulso** na topbar com horário da última varredura.

Tudo isso comunica: *a máquina está ligada e trabalhando por você.*

---

## 5. Arquitetura do CSS

Três camadas, carregadas nesta ordem:

| Arquivo | Papel |
|---|---|
| `css/tokens.css` | **Ponto único de calibração.** Só variáveis. |
| `css/base.css` | Reset, tipografia, primitivos (`.btn`, `.badge`, `.chip`, `.campo`) |
| `css/app.css` | Componentes da plataforma (topbar, hero, cards, filtros) |

**Nunca escreva cor literal fora de `tokens.css`.** Trocar a identidade inteira
deve custar a edição de um arquivo só.

---

## 6. Acessibilidade

Decisões já implementadas, que devem ser mantidas:

- `:focus-visible` com contorno lima de 2px em todos os interativos.
- `prefers-reduced-motion` desliga varredura, pulso e contagem crescente.
- Abas de status com `role="tab"` e `aria-selected`.
- Favoritos com `aria-pressed` e `aria-label` que muda conforme o estado.
- Skip link para o painel.
- Regiões dinâmicas com `aria-live="polite"`.
- Estilos de impressão: um edital salvo em PDF continua legível.

---

## 7. Pendências

- Logo oficial: o ícone de radar é um marcador. Substituir pelo logo real da CFC.
- Os editais em `data/editais.json` são **exemplos realistas**, não dados reais.
- Backend do robô de captura (esta entrega é só o front-end).
- Link real do curso no CTA e do WhatsApp da comunidade.
