/* ============================================================
   CFC ACADEMY · RADAR CONCURSOS CONTABILIDADE
   Pinos volumétricos sobre o mapa.
   ------------------------------------------------------------
   Cada estado com edital ganha uma coluna cuja ALTURA é o número
   de editais. É a leitura principal do acervo: de relance se vê
   onde há oportunidade.

   POR QUE SVG E NÃO WEBGL

   Seriam ~600 KB de biblioteca e um canvas que leitor de tela
   não enxerga, para desenhar 27 colunas. Em SVG cada pino é
   elemento real — clicável, alcançável por teclado, anunciado
   com estado e contagem.

   COMO O VOLUME É CONSTRUÍDO

   Não é perspectiva de câmera: é um prisma desenhado à mão. Cada
   coluna tem três faces — frente clara, lateral escura, topo em
   losango — e o olho lê isso como sólido. É a mesma técnica de
   ilustração isométrica, e tem uma vantagem sobre inclinar o
   mapa inteiro: o contorno do Brasil continua reconhecível, e o
   candidato precisa achar o estado dele.

   O ERRO DA PRIMEIRA VERSÃO ficou registrado aqui para não se
   repetir: as colunas sobem ACIMA do topo do viewBox, e o
   `overflow:hidden` do contêiner as decepava — os estados do
   Norte perdiam o pino inteiro. O viewBox é reescrito para
   abrir espaço em cima.
   ============================================================ */

const NS = 'http://www.w3.org/2000/svg';

/** Largura da coluna, em unidades do viewBox. */
const LARGURA = 7;

/** Deslocamento da face lateral — o que cria a sensação de
 *  profundidade. Proporcional à largura, para a coluna parecer
 *  o mesmo sólido em qualquer tamanho de tela. */
const PROFUNDIDADE = LARGURA * 0.42;

const ALTURA_MAX = 62;
const ALTURA_MIN = 12;

/** Espaço extra no topo do viewBox, para as colunas mais altas e
 *  suas siglas caberem sem serem cortadas. */
const FOLGA_TOPO = ALTURA_MAX + 26;

/**
 * Altura da coluna a partir da contagem.
 *
 * Raiz quadrada, não proporção direta: MG tem 33 editais e o AC
 * tem 1. Em escala linear a coluna mineira sairia da tela e as
 * outras virariam tocos idênticos. A raiz comprime o topo e
 * preserva a diferença embaixo, onde está quase todo estado.
 */
function altura(n, maximo){
  if(!n) return 0;
  return ALTURA_MIN + (Math.sqrt(n) / Math.sqrt(maximo || 1)) * (ALTURA_MAX - ALTURA_MIN);
}

function el(tag, attrs){
  const node = document.createElementNS(NS, tag);
  for(const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  return node;
}

function centro(alvo){
  try{
    const b = alvo.getBBox();
    return { x: b.x + b.width / 2, y: b.y + b.height / 2 };
  }catch{
    return null;   // getBBox lança se o elemento ainda não renderizou
  }
}

/** Mesma escala de faixas do mapa plano, para as duas leituras
 *  (cor do estado e cor da coluna) nunca discordarem. */
function faixaDe(n){
  if(!n) return 0;
  if(n <= 2) return 1;
  if(n <= 5) return 2;
  if(n <= 10) return 3;
  return 4;
}

/** Abre espaço no topo do viewBox. Sem isto as colunas altas são
 *  cortadas — foi o defeito da primeira versão. */
function ampliarViewBox(svg){
  if(svg.dataset.vbAmpliado) return;

  const vb = (svg.getAttribute('viewBox') || '').split(/[\s,]+/).map(Number);
  if(vb.length !== 4 || vb.some(Number.isNaN)) return;

  svg.dataset.vbOriginal = svg.getAttribute('viewBox');
  svg.setAttribute('viewBox',
    `${vb[0]} ${vb[1] - FOLGA_TOPO} ${vb[2]} ${vb[3] + FOLGA_TOPO}`);
  svg.dataset.vbAmpliado = '1';
}

function restaurarViewBox(svg){
  if(!svg.dataset.vbAmpliado) return;
  svg.setAttribute('viewBox', svg.dataset.vbOriginal);
  delete svg.dataset.vbAmpliado;
}

/** Definições reutilizáveis: gradientes das faces e o brilho. */
function garantirDefs(svg){
  if(svg.querySelector('#defs-pinos')) return;

  const defs = el('defs', { id: 'defs-pinos' });

  // Um gradiente por faixa, para a coluna ter volume próprio em
  // vez de cor chapada. O topo é sempre mais claro que a base:
  // é o que o olho espera de algo iluminado de cima.
  const FAIXAS = {
    1: ['#2f6b22', '#1c3f14'],
    2: ['#76A41C', '#3f5c10'],
    3: ['#9FE31A', '#5c8410'],
    4: ['#E8D63C', '#8a7a12'],
  };

  for(const [faixa, [claro, escuro]] of Object.entries(FAIXAS)){
    const g = el('linearGradient', {
      id: `grad-pino-${faixa}`, x1: '0', y1: '0', x2: '0', y2: '1',
    });
    g.append(
      el('stop', { offset: '0',   'stop-color': claro }),
      el('stop', { offset: '1',   'stop-color': escuro }),
    );
    defs.appendChild(g);
  }

  // Sombra suave sob a coluna, para ela assentar no mapa.
  const blur = el('filter', {
    id: 'brilho-pino', x: '-70%', y: '-70%', width: '240%', height: '240%',
  });
  blur.append(el('feGaussianBlur', { stdDeviation: '2.4', result: 'b' }));
  const merge = el('feMerge', {});
  merge.append(el('feMergeNode', { in: 'b' }), el('feMergeNode', { in: 'SourceGraphic' }));
  blur.appendChild(merge);
  defs.appendChild(blur);

  svg.insertBefore(defs, svg.firstChild);
}

/**
 * Desenha as colunas dentro do SVG do mapa.
 *
 * @param {SVGElement} svg     o <svg> do mapa
 * @param {Object} contagem    { UF: nº de editais }
 * @param {string} ufAtiva     estado selecionado, ou ''
 * @param {Function} aoClicar  recebe a UF clicada
 */
export function desenharPinos(svg, contagem, ufAtiva, aoClicar){
  if(!svg) return;

  svg.querySelector('#camada-pinos')?.remove();

  const valores = Object.values(contagem).filter(Boolean);
  if(!valores.length){ restaurarViewBox(svg); return; }

  ampliarViewBox(svg);
  garantirDefs(svg);

  const maximo = Math.max(...valores);
  const camada = el('g', { id: 'camada-pinos', class: 'camada-pinos' });

  // De trás para a frente: sem isto a coluna do Amazonas passa
  // por cima da de São Paulo, que está à frente na composição.
  const colunas = Object.entries(contagem)
    .filter(([, n]) => n > 0)
    .map(([uf, n]) => ({ uf, n, alvo: svg.getElementById(uf) }))
    .filter(c => c.alvo)
    .map(c => ({ ...c, pos: centro(c.alvo) }))
    .filter(c => c.pos)
    .sort((a, b) => a.pos.y - b.pos.y);

  const temSelecao = Boolean(ufAtiva);

  colunas.forEach(({ uf, n, pos }) => {
    const h = altura(n, maximo);
    const faixa = faixaDe(n);
    const meia = LARGURA / 2;
    const topoY = pos.y - h;

    const g = el('g', {
      class: 'pino',
      'data-uf': uf,
      'data-faixa': String(faixa),
      role: 'button',
      tabindex: '0',
      'aria-label': `${uf}: ${n} ${n === 1 ? 'edital' : 'editais'}`,
    });
    if(uf === ufAtiva) g.setAttribute('data-ativo', 'true');
    else if(temSelecao) g.setAttribute('data-apagado', 'true');

    // Sombra elíptica: ancora a coluna ao estado. Sem ela o
    // sólido flutua sobre o mapa em vez de nascer dele.
    g.appendChild(el('ellipse', {
      cx: pos.x + PROFUNDIDADE / 2, cy: pos.y + 1.5,
      rx: LARGURA * 0.95, ry: LARGURA * 0.34,
      class: 'pino-sombra',
    }));

    // Face frontal.
    g.appendChild(el('rect', {
      x: pos.x - meia, y: topoY, width: LARGURA, height: h,
      rx: 1.2, class: 'pino-frente',
      fill: `url(#grad-pino-${faixa})`,
    }));

    // Face lateral, deslocada — é ela que cria a profundidade.
    g.appendChild(el('path', {
      d: `M${pos.x + meia},${topoY} l${PROFUNDIDADE},${-PROFUNDIDADE * 0.6}`
       + ` l0,${h} l${-PROFUNDIDADE},${PROFUNDIDADE * 0.6} Z`,
      class: 'pino-lado',
    }));

    // Topo em losango, fechando o sólido.
    g.appendChild(el('path', {
      d: `M${pos.x - meia},${topoY}`
       + ` l${PROFUNDIDADE},${-PROFUNDIDADE * 0.6}`
       + ` l${LARGURA},0`
       + ` l${-PROFUNDIDADE},${PROFUNDIDADE * 0.6} Z`,
      class: 'pino-tampa',
    }));

    // Contagem sobre a coluna — o dado que o pino representa,
    // dito em número. A altura dá a comparação; o número dá a
    // precisão.
    g.appendChild(el('text', {
      x: pos.x + PROFUNDIDADE / 2, y: topoY - 8.5,
      class: 'pino-n',
    })).textContent = String(n);

    g.appendChild(el('text', {
      x: pos.x + PROFUNDIDADE / 2, y: topoY - 2.5,
      class: 'pino-sigla',
    })).textContent = uf;

    g.addEventListener('click', ev => { ev.stopPropagation(); aoClicar(uf); });
    g.addEventListener('keydown', ev => {
      if(ev.key === 'Enter' || ev.key === ' '){
        ev.preventDefault();
        aoClicar(uf);
      }
    });

    camada.appendChild(g);
  });

  svg.appendChild(camada);
}

/** Liga ou desliga a vista com volume. */
export function aplicarVista(container, tridimensional){
  if(!container) return;
  container.classList.toggle('mapa-3d', tridimensional);

  const svg = container.querySelector('svg');
  if(svg && !tridimensional) restaurarViewBox(svg);
}
