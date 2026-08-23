/* ============================================================
   CFC ACADEMY · RADAR CONCURSOS CONTABILIDADE
   Pinos volumétricos sobre o mapa.
   ------------------------------------------------------------
   Cada estado ganha um pino cuja ALTURA é o número de editais e
   cuja COR é a intensidade — o mesmo dado que antes só existia
   no preenchimento do estado, agora legível de relance.

   POR QUE SVG E NÃO WEBGL

   O visual de referência usa WebGL. Aqui não compensa: seriam
   ~600 KB de biblioteca e um canvas que o leitor de tela não
   enxerga, para desenhar 27 hastes. Em SVG o pino é um elemento
   real — clicável, alcançável por teclado, anunciado com o nome
   do estado — e entra no mesmo documento que já desenha o mapa.

   A profundidade vem de projeção isométrica leve: o mapa inclina
   para trás e o pino sobe na vertical. Não é 3D de verdade, e
   não precisa ser — o que comunica volume é a altura relativa
   entre os pinos, não a perspectiva.
   ============================================================ */

/** Inclinação do mapa, em graus. Suficiente para dar profundidade
 *  sem deformar o contorno do país a ponto de dificultar o
 *  reconhecimento — o candidato precisa achar o estado dele. */
const INCLINACAO = 52;

/** Altura máxima do pino, em unidades do viewBox do SVG. */
const ALTURA_MAX = 78;
const ALTURA_MIN = 14;

/**
 * Altura do pino a partir da contagem.
 *
 * Raiz quadrada, não proporção direta: São Paulo tem muitas vezes
 * o volume do Acre, e em escala linear o pino paulista sairia da
 * tela enquanto os demais virariam tocos indistinguíveis. A raiz
 * comprime o topo e preserva a diferença embaixo, que é onde
 * estão quase todos os estados.
 */
function altura(n, maximo){
  if(!n) return 0;
  const proporcao = Math.sqrt(n) / Math.sqrt(maximo || 1);
  return ALTURA_MIN + proporcao * (ALTURA_MAX - ALTURA_MIN);
}

/** Centro geométrico do estado, no sistema de coordenadas do SVG. */
function centro(el){
  try{
    const b = el.getBBox();
    return { x: b.x + b.width / 2, y: b.y + b.height / 2 };
  }catch{
    // getBBox lança se o elemento ainda não foi renderizado.
    return null;
  }
}

/**
 * Desenha os pinos dentro do SVG do mapa.
 *
 * @param {SVGElement} svg      o <svg> do mapa
 * @param {Object} contagem     { UF: nº de editais }
 * @param {string} ufAtiva      estado selecionado, ou ''
 * @param {Function} aoClicar   recebe a UF clicada
 */
export function desenharPinos(svg, contagem, ufAtiva, aoClicar){
  if(!svg) return;

  svg.querySelector('#camada-pinos')?.remove();

  const valores = Object.values(contagem).filter(Boolean);
  if(!valores.length) return;
  const maximo = Math.max(...valores);

  const camada = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  camada.setAttribute('id', 'camada-pinos');
  camada.setAttribute('class', 'camada-pinos');

  // Estados ao fundo primeiro: sem isto o pino do Amazonas passa
  // por cima do de São Paulo, que está à frente dele na projeção.
  const ordenados = Object.entries(contagem)
    .filter(([, n]) => n > 0)
    .map(([uf, n]) => ({ uf, n, el: svg.getElementById(uf) }))
    .filter(item => item.el)
    .map(item => ({ ...item, pos: centro(item.el) }))
    .filter(item => item.pos)
    .sort((a, b) => a.pos.y - b.pos.y);

  ordenados.forEach(({ uf, n, pos }) => {
    const h = altura(n, maximo);
    const grupo = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    grupo.setAttribute('class', 'pino');
    grupo.setAttribute('data-uf', uf);
    grupo.setAttribute('data-faixa', String(faixaDe(n)));
    if(uf === ufAtiva) grupo.setAttribute('data-ativo', 'true');

    // O halo no chão ancora o pino ao estado: sem ele a haste
    // parece flutuar sobre o mapa em vez de nascer dele.
    const halo = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
    halo.setAttribute('cx', pos.x);
    halo.setAttribute('cy', pos.y);
    halo.setAttribute('rx', 7);
    halo.setAttribute('ry', 3);
    halo.setAttribute('class', 'pino-halo');

    const haste = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    haste.setAttribute('x1', pos.x);
    haste.setAttribute('y1', pos.y);
    haste.setAttribute('x2', pos.x);
    haste.setAttribute('y2', pos.y - h);
    haste.setAttribute('class', 'pino-haste');

    const topo = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    topo.setAttribute('cx', pos.x);
    topo.setAttribute('cy', pos.y - h);
    topo.setAttribute('r', 3.4);
    topo.setAttribute('class', 'pino-topo');

    const sigla = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    sigla.setAttribute('x', pos.x);
    sigla.setAttribute('y', pos.y - h - 7);
    sigla.setAttribute('class', 'pino-sigla');
    sigla.textContent = uf;

    grupo.append(halo, haste, topo, sigla);

    // O pino é um botão de verdade: teclado alcança, leitor de tela
    // anuncia. O SVG do fundo continua clicável para quem prefere
    // acertar o estado em si.
    grupo.setAttribute('role', 'button');
    grupo.setAttribute('tabindex', '0');
    grupo.setAttribute('aria-label', `${uf}: ${n} ${n === 1 ? 'edital' : 'editais'}`);
    grupo.addEventListener('click', ev => { ev.stopPropagation(); aoClicar(uf); });
    grupo.addEventListener('keydown', ev => {
      if(ev.key === 'Enter' || ev.key === ' '){
        ev.preventDefault();
        aoClicar(uf);
      }
    });

    camada.appendChild(grupo);
  });

  svg.appendChild(camada);
}

/** Mesma escala de faixas do mapa plano, para as duas leituras
 *  (cor do estado e cor do pino) nunca discordarem. */
function faixaDe(n){
  if(!n) return 0;
  if(n <= 2) return 1;
  if(n <= 5) return 2;
  if(n <= 10) return 3;
  return 4;
}

/** Liga ou desliga a vista 3D no contêiner do mapa. */
export function aplicarVista(container, tridimensional){
  if(!container) return;
  container.classList.toggle('mapa-3d', tridimensional);
  container.style.setProperty('--inclinacao', `${tridimensional ? INCLINACAO : 0}deg`);
}
