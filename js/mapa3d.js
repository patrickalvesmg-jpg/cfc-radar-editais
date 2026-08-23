/* ============================================================
   CFC ACADEMY · RADAR CONCURSOS CONTABILIDADE
   Mapa 3D — o país extrudado, cada estado com altura própria.
   ------------------------------------------------------------
   Terceira tentativa de 3D, e a primeira que trata o VOLUME como
   sendo o próprio território.

   As duas anteriores falharam pelo mesmo motivo: eram hastes
   sobrepostas a um desenho plano. Inclinar o mapa deformava o
   contorno do Brasil, e reconhecer o próprio estado é a primeira
   coisa que o candidato faz.

   Aqui cada estado é um BLOCO extrudado — a silhueta continua
   exata, porque é a mesma do SVG; o que muda é que ela ganha
   espessura, e a espessura é o número de editais.

   POR QUE NÃO USAMOS BIBLIOTECA 3D

   Three.js custa ~600 KB. Para extrudar 27 polígonos e girar a
   câmera, isso é desproporcional — e o site inteiro não passa de
   200 KB hoje. Projetamos à mão em canvas 2D: cada ponto do
   estado é rebatido por uma matriz isométrica, e as faces
   laterais saem de ligar o contorno de baixo ao de cima.

   O canvas não é acessível por si só, então o SVG original
   continua no DOM, invisível, servindo de camada de clique e de
   alvo para teclado e leitor de tela.
   ============================================================ */

const UFS_NOME = {
  AC:'Acre', AL:'Alagoas', AM:'Amazonas', AP:'Amapá', BA:'Bahia',
  CE:'Ceará', DF:'Distrito Federal', ES:'Espírito Santo', GO:'Goiás',
  MA:'Maranhão', MG:'Minas Gerais', MS:'Mato Grosso do Sul',
  MT:'Mato Grosso', PA:'Pará', PB:'Paraíba', PE:'Pernambuco',
  PI:'Piauí', PR:'Paraná', RJ:'Rio de Janeiro', RN:'Rio Grande do Norte',
  RO:'Rondônia', RR:'Roraima', RS:'Rio Grande do Sul',
  SC:'Santa Catarina', SE:'Sergipe', SP:'São Paulo', TO:'Tocantins',
};

/* ---------------- projeção ---------------- */

/** Inclinação da câmera. 0.52 dá profundidade sem achatar o país
 *  a ponto de o Nordeste virar uma faixa. */
const ACHATAMENTO = 0.52;

/** Altura máxima de um bloco, em unidades do mapa. */
const ALTURA_MAX = 34;
const ALTURA_MIN = 3.5;

/** Projeta um ponto do plano do mapa para a tela.
 *
 *  A rotação acontece em torno do centro do país; depois o eixo
 *  vertical é achatado (a inclinação da câmera) e a altura do
 *  bloco sobe na tela sem sofrer esse achatamento — é o que faz
 *  o bloco parecer erguido em vez de deitado. */
function projetar(x, y, z, cx, cy, cos, sin){
  const dx = x - cx;
  const dy = y - cy;
  return {
    x: cx + dx * cos - dy * sin,
    y: cy + (dx * sin + dy * cos) * ACHATAMENTO - z,
  };
}

function altura(n, maximo){
  if(!n) return ALTURA_MIN * 0.5;
  return ALTURA_MIN + (Math.sqrt(n) / Math.sqrt(maximo || 1)) * (ALTURA_MAX - ALTURA_MIN);
}

/* ---------------- cor ---------------- */

/** As cinco faixas do mapa plano, em RGB, para poder escurecer as
 *  faces laterais por cálculo em vez de manter uma segunda lista
 *  de cores que sairia de sincronia. */
const CORES = {
  0: [ 26,  38,  27],
  1: [ 47, 107,  34],
  2: [118, 164,  28],
  3: [159, 227,  26],
  4: [232, 214,  60],
};

function faixaDe(n){
  if(!n) return 0;
  if(n <= 2) return 1;
  if(n <= 5) return 2;
  if(n <= 10) return 3;
  return 4;
}

function rgb([r, g, b], fator = 1, alfa = 1){
  const f = v => Math.round(Math.min(255, v * fator));
  return `rgba(${f(r)},${f(g)},${f(b)},${alfa})`;
}

/* ---------------- geometria ---------------- */

/**
 * Lê os contornos do SVG.
 *
 * A maioria dos estados é `<polygon>`, e aí os pontos já vêm
 * prontos. MT e PA são `<path>` com curvas — para esses usamos
 * `getPointAtLength`, que é o próprio navegador convertendo a
 * curva em pontos. Sai mais barato e mais correto que escrever
 * um interpretador de bézier.
 */
function extrairContornos(svg){
  const formas = {};

  for(const uf of Object.keys(UFS_NOME)){
    const el = svg.getElementById(uf);
    if(!el) continue;

    if(el.tagName === 'polygon' && el.points){
      formas[uf] = Array.from(el.points).map(p => ({ x: p.x, y: p.y }));
      continue;
    }

    if(typeof el.getTotalLength === 'function'){
      const total = el.getTotalLength();
      if(!total) continue;
      // Um ponto a cada ~2 unidades: fino o bastante para a curva
      // não virar polígono visível, leve o bastante para redesenhar
      // a 60 quadros por segundo.
      const passos = Math.max(24, Math.min(220, Math.round(total / 2)));
      const pontos = [];
      for(let i = 0; i < passos; i++){
        const p = el.getPointAtLength((i / passos) * total);
        pontos.push({ x: p.x, y: p.y });
      }
      formas[uf] = pontos;
    }
  }
  return formas;
}

function centroide(pontos){
  const s = pontos.reduce((a, p) => ({ x: a.x + p.x, y: a.y + p.y }), { x:0, y:0 });
  return { x: s.x / pontos.length, y: s.y / pontos.length };
}

/* ---------------- render ---------------- */

export function criarMapa3D(container, { onSelecionar } = {}){
  const svg = container.querySelector('svg');
  if(!svg) return null;

  const vb = (svg.getAttribute('viewBox') || '').split(/[\s,]+/).map(Number);
  if(vb.length !== 4) return null;

  const formas = extrairContornos(svg);
  const centros = {};
  for(const [uf, pts] of Object.entries(formas)) centros[uf] = centroide(pts);

  const cx = vb[0] + vb[2] / 2;
  const cy = vb[1] + vb[3] / 2;

  const canvas = document.createElement('canvas');
  canvas.className = 'mapa3d-canvas';
  canvas.setAttribute('aria-hidden', 'true');   // o SVG é a camada acessível
  container.prepend(canvas);

  const ctx = canvas.getContext('2d');

  let contagem = {};
  let ufAtiva = '';
  let giro = -0.32;          // radianos; leve, só para não ficar frontal
  let giroAlvo = -0.32;
  let animando = false;

  function dimensionar(){
    const r = container.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(r.width * dpr);
    canvas.height = Math.round(r.height * dpr);
    canvas.style.width = `${r.width}px`;
    canvas.style.height = `${r.height}px`;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return r;
  }

  function desenhar(){
    const r = dimensionar();
    ctx.clearRect(0, 0, r.width, r.height);

    // O mapa cabe na caixa mantendo proporção; o topo ganha folga
    // para os blocos altos não encostarem na borda.
    const folga = ALTURA_MAX + 12;
    const escala = Math.min(r.width / vb[2], r.height / (vb[3] + folga));
    const offX = (r.width - vb[2] * escala) / 2;
    const offY = (r.height - (vb[3] + folga) * escala) / 2 + folga * escala;

    const cos = Math.cos(giro);
    const sin = Math.sin(giro);
    const maximo = Math.max(1, ...Object.values(contagem));
    const temSelecao = Boolean(ufAtiva);

    const tela = (x, y, z) => {
      const p = projetar(x, y, z, cx, cy, cos, sin);
      return { x: offX + (p.x - vb[0]) * escala, y: offY + (p.y - vb[1]) * escala };
    };

    // Pinta de trás para a frente: sem isto os estados do sul
    // ficam por baixo dos do norte, que estão atrás na cena.
    const ordem = Object.entries(formas)
      .map(([uf, pts]) => {
        const c = centros[uf];
        const d = (c.x - cx) * sin + (c.y - cy) * cos;   // profundidade
        return { uf, pts, prof: d };
      })
      .sort((a, b) => a.prof - b.prof);

    for(const { uf, pts } of ordem){
      const n = contagem[uf] || 0;
      const h = altura(n, maximo) * (n ? 1 : 1);
      const cor = CORES[faixaDe(n)];
      const ativo = uf === ufAtiva;
      const alfa = temSelecao && !ativo ? 0.42 : 1;

      const base = pts.map(p => tela(p.x, p.y, 0));
      const topo = pts.map(p => tela(p.x, p.y, h * escala));

      // Faces laterais: uma por aresta, só as que olham para a
      // câmera. Desenhar as de trás seria trabalho jogado fora e
      // ainda escureceria o bloco por sobreposição.
      for(let i = 0; i < pts.length; i++){
        const j = (i + 1) % pts.length;
        const b1 = base[i], b2 = base[j], t1 = topo[i], t2 = topo[j];

        // Produto vetorial: aresta virada para nós tem sinal > 0.
        if((b2.x - b1.x) * (t1.y - b1.y) - (b2.y - b1.y) * (t1.x - b1.x) <= 0) continue;

        ctx.beginPath();
        ctx.moveTo(b1.x, b1.y);
        ctx.lineTo(b2.x, b2.y);
        ctx.lineTo(t2.x, t2.y);
        ctx.lineTo(t1.x, t1.y);
        ctx.closePath();
        ctx.fillStyle = rgb(cor, 0.42, alfa);
        ctx.fill();
      }

      // Tampa: a face que recebe luz, e onde a cor se lê.
      ctx.beginPath();
      topo.forEach((p, i) => i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y));
      ctx.closePath();
      ctx.fillStyle = rgb(cor, ativo ? 1.25 : 1, alfa);
      ctx.fill();
      ctx.lineWidth = ativo ? 1.6 : 0.6;
      ctx.strokeStyle = ativo ? 'rgba(255,255,255,.9)' : rgb(cor, 0.55, alfa);
      ctx.stroke();
    }

    // Rótulos por último, para nenhum bloco cobrir texto.
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    for(const { uf } of ordem){
      const n = contagem[uf] || 0;
      if(!n) continue;

      const c = centros[uf];
      const h = altura(n, maximo);
      const p = tela(c.x, c.y, h * escala);
      const ativo = uf === ufAtiva;
      const alfa = temSelecao && !ativo ? 0.35 : 1;

      ctx.font = `700 ${Math.max(10, 11 * escala / 1.1)}px ui-monospace, monospace`;
      ctx.lineWidth = 3;
      ctx.strokeStyle = `rgba(10,15,10,${alfa})`;
      ctx.strokeText(String(n), p.x, p.y - 7);
      ctx.fillStyle = ativo ? `rgba(255,255,255,${alfa})` : `rgba(230,245,220,${alfa})`;
      ctx.fillText(String(n), p.x, p.y - 7);

      ctx.font = `600 ${Math.max(7, 7.5 * escala / 1.1)}px ui-monospace, monospace`;
      ctx.strokeText(uf, p.x, p.y + 3);
      ctx.fillStyle = `rgba(150,175,140,${alfa})`;
      ctx.fillText(uf, p.x, p.y + 3);
    }
  }

  function animar(){
    if(animando) return;
    animando = true;
    const passo = () => {
      const delta = giroAlvo - giro;
      if(Math.abs(delta) < 0.001){
        giro = giroAlvo;
        animando = false;
        desenhar();
        return;
      }
      giro += delta * 0.12;
      desenhar();
      requestAnimationFrame(passo);
    };
    requestAnimationFrame(passo);
  }

  /* ---- arrastar para girar ---- */
  let arrastando = false, xInicial = 0, giroInicial = 0;

  canvas.addEventListener('pointerdown', ev => {
    arrastando = true;
    xInicial = ev.clientX;
    giroInicial = giro;
    canvas.setPointerCapture(ev.pointerId);
    canvas.style.cursor = 'grabbing';
  });

  canvas.addEventListener('pointermove', ev => {
    if(!arrastando) return;
    // Limite de ±50°: passando disso o país fica de perfil e
    // deixa de ser reconhecível, que é o erro das versões antigas.
    giro = Math.max(-0.9, Math.min(0.9, giroInicial + (ev.clientX - xInicial) * 0.005));
    giroAlvo = giro;
    desenhar();
  });

  const soltar = ev => {
    if(!arrastando) return;
    arrastando = false;
    canvas.style.cursor = 'grab';
    try{ canvas.releasePointerCapture(ev.pointerId); }catch{}
  };
  canvas.addEventListener('pointerup', soltar);
  canvas.addEventListener('pointercancel', soltar);

  window.addEventListener('resize', () => desenhar());

  return {
    atualizar(novaContagem, nova){
      contagem = novaContagem || {};
      ufAtiva = nova || '';
      desenhar();
    },
    girarPara(rad){ giroAlvo = rad; animar(); },
    destruir(){ canvas.remove(); },
  };
}
