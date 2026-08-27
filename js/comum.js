/* ============================================================
   CFC ACADEMY · RADAR DE EDITAIS
   Comum — formatação, regras de prazo e o card de edital.
   Compartilhado entre a landing (index) e a plataforma (app).
   ============================================================ */

import { ehNovo } from './novidades.js';

export const STATUS = {
  aberto:     { rot:'Inscrições abertas', classe:'badge-ok' },
  encerrando: { rot:'Encerrando',         classe:'badge-warn' },
  previsto:   { rot:'Previsto',           classe:'badge-info' },
  encerrado:  { rot:'Encerrado',          classe:'badge-neutro' },
};

export const ESFERA = { federal:'Federal', estadual:'Estadual', municipal:'Municipal' };

/* ---------------- formatação ---------------- */

export const brl = new Intl.NumberFormat('pt-BR', {
  style:'currency', currency:'BRL', maximumFractionDigits:0,
});

export function dataBR(iso){
  if(!iso) return '—';
  const [a,m,d] = iso.slice(0,10).split('-');
  return `${d}/${m}/${a}`;
}

export function hora(iso){
  if(!iso) return '--:--';
  return new Date(iso).toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'});
}

/** Dias até a data (negativo = já passou). */
export function diasAte(iso){
  if(!iso) return null;
  const hoje = new Date(); hoje.setHours(0,0,0,0);
  const alvo = new Date(iso.slice(0,10) + 'T00:00:00');
  return Math.round((alvo - hoje) / 86400000);
}

/** Vagas vêm como "12 + CR" ou "5" — extrai o número para ordenar/somar. */
export function numeroVagas(v){
  const n = parseInt(String(v).replace(/\D/g,''), 10);
  return Number.isFinite(n) ? n : 0;
}

export function esc(s){
  return String(s).replace(/[&<>"']/g, c => (
    {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]
  ));
}

/* ---------------- ordenação por prazo ---------------- */

/**
 * Classifica um edital para a ordenação por prazo, em três grupos:
 *   0 — inscrição em curso (ordena pelo que fecha antes)
 *   1 — previsto, sem data (ordena pelo capturado mais recente)
 *   2 — encerrado (ordena pelo que fechou mais recentemente)
 */
export function prioridadePrazo(e){
  const dias = diasAte(e.inscricaoFim);

  if(e.status === 'encerrado' || (dias !== null && dias < 0)){
    return { grupo:2, chave:-(new Date(e.inscricaoFim || 0).getTime()) };
  }
  if(dias === null){
    return { grupo:1, chave:-(new Date(e.capturadoEm || 0).getTime()) };
  }
  return { grupo:0, chave:dias };
}

export function ordenarPorPrazo(lista){
  return [...lista].sort((a,b) => {
    const pa = prioridadePrazo(a), pb = prioridadePrazo(b);
    if(pa.grupo !== pb.grupo) return pa.grupo - pb.grupo;
    return pa.chave - pb.chave;
  });
}

/* ---------------- card de edital ---------------- */

const ICONES = {
  local:'<circle cx="12" cy="10" r="3"/><path d="M12 21s7-6.2 7-11a7 7 0 1 0-14 0c0 4.8 7 11 7 11Z"/>',
  banca:'<path d="M4 6h16M4 12h16M4 18h10"/>',
  vagas:'<path d="M16 20v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 20v-2a4 4 0 0 0-3-3.9"/>',
  prova:'<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M8 3v4M16 3v4M3 11h18"/>',
  fonte:'<path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Z"/><path d="M2 12h20M12 2a15 15 0 0 1 0 20 15 15 0 0 1 0-20Z"/>',
};

function item(icone, html){
  return `<span class="item">
    <svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${ICONES[icone]}</svg>
    ${html}
  </span>`;
}

/**
 * Monta o card.
 * @param {object} e edital
 * @param {object} opcoes
 *   favorito {boolean} estado do coração
 *   interativo {boolean} false esconde ações (usado nos cards borrados)
 */
export function cardEdital(e, { favorito = false, interativo = true } = {}){
  const st = STATUS[e.status] || STATUS.encerrado;
  const dias = diasAte(e.inscricaoFim);

  // O bloco de prazo muda de sentido conforme o status.
  let prazoHtml;
  if(e.status === 'previsto'){
    prazoHtml = `<div class="prazo"><b>Aguardando</b>edital não publicado</div>`;
  }else if(e.status === 'encerrado'){
    prazoHtml = `<div class="prazo"><b>Encerrado</b>em ${dataBR(e.inscricaoFim)}</div>`;
  }else if(dias !== null && dias >= 0){
    const urgente = dias <= 7 ? ' urgente' : '';
    const txt = dias === 0 ? 'Último dia' : `${dias} ${dias === 1 ? 'dia' : 'dias'}`;
    prazoHtml = `<div class="prazo${urgente}"><b>${txt}</b>até ${dataBR(e.inscricaoFim)}</div>`;
  }else{
    prazoHtml = `<div class="prazo"><b>—</b>prazo a confirmar</div>`;
  }

  // O rótulo diz de onde veio o número.
  //
  // Era "Até" para todo mundo, e isso estava errado das duas formas: o
  // valor vinha do maior salário do edital (o do médico, do procurador),
  // e o "Até" ainda prometia que o contador podia chegar lá.
  //
  // Agora: sem observação, é o vencimento DO CARGO, lido do anexo do
  // edital — o rótulo é "Salário". Com `salarioObs` ("a partir de"), o
  // edital só publicou faixa e mostramos o piso.
  const rotuloSalario = e.salarioObs ? 'A partir de' : 'Salário';
  const salarioHtml = e.salario
    ? `<div class="salario"><small>${esc(rotuloSalario)}</small>${brl.format(e.salario)}</div>`
    : `<div class="salario"><small>Salário</small><span class="pendente">a confirmar</span></div>`;

  /* Editais recém-capturados podem vir sem cidade ou sem UF: o robô só
     preenche o que consegue afirmar. Montamos o local com o que existe. */
  const local = e.cidade && e.uf ? `<b>${esc(e.cidade)}</b>/${esc(e.uf)}`
              : e.cidade         ? `<b>${esc(e.cidade)}</b>`
              : e.uf             ? `<b>${esc(e.uf)}</b>`
              : '';

  const acoes = interativo ? `
      <div class="edital-acoes">
        <button class="icone-btn" aria-pressed="${favorito}"
                aria-label="${favorito ? 'Remover dos favoritos' : 'Salvar nos favoritos'}"
                data-fav="${esc(e.id)}">
          <svg viewBox="0 0 24 24" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="m12 21-1.5-1.3C5.4 15.1 2 12.1 2 8.5 2 5.4 4.4 3 7.5 3c1.7 0 3.4.8 4.5 2.1C13.1 3.8 14.8 3 16.5 3 19.6 3 22 5.4 22 8.5c0 3.6-3.4 6.6-8.5 11.2L12 21Z"/>
          </svg>
        </button>
        <a class="btn btn-lima btn-sm" href="${esc(e.editalUrl)}">Ver edital</a>
      </div>` : '';

  const titulo = interativo
    ? `<a href="${esc(e.editalUrl)}">${esc(e.cargo)}</a>`
    : esc(e.cargo);

  return `
  <article class="edital up" data-status="${esc(e.status)}">
    <div class="edital-main">
      <div class="edital-topo">
        ${ehNovo(e) ? '<span class="badge badge-novo">Novo</span>' : ''}
        <span class="badge ${st.classe}">${st.rot}</span>
        <span class="badge badge-neutro">${ESFERA[e.nivel] || esc(e.nivel)}</span>
        ${e.confianca === 'baixa' ? '<span class="badge badge-warn">A confirmar</span>' : ''}
      </div>

      <h3>${titulo}</h3>
      <p class="orgao">${esc(e.orgao)}</p>

      <div class="edital-meta">
        ${local ? item('local', local) : ''}
        ${e.banca ? item('banca', `Banca <b>${esc(e.banca)}</b>`) : ''}
        ${e.vagas ? item('vagas', `<b>${esc(e.vagas)}</b> vagas`) : ''}
        ${e.dataProva ? item('prova', `Prova <b>${dataBR(e.dataProva)}</b>`) : ''}
        ${item('fonte', `${esc(e.fonte)} · ${hora(e.capturadoEm)}`)}
      </div>
    </div>

    <div class="edital-lado">
      ${salarioHtml}
      ${prazoHtml}
      ${acoes}
    </div>
  </article>`;
}

/* ---------------- reveal on scroll ---------------- */

let observador;
export function observar(){
  observador?.disconnect();
  observador = new IntersectionObserver((entradas) => {
    entradas.forEach(e => {
      if(e.isIntersecting){ e.target.classList.add('in'); observador.unobserve(e.target); }
    });
  }, { threshold:0.08, rootMargin:'0px 0px -40px 0px' });

  document.querySelectorAll('.up:not(.in)').forEach(el => observador.observe(el));
}

/* ---------------- números do topo ---------------- */

/** Contagem crescente — reforça a sensação de painel ao vivo. */
export function animarNumero(el, alvo){
  if(!el) return;
  if(matchMedia('(prefers-reduced-motion: reduce)').matches){
    el.textContent = alvo.toLocaleString('pt-BR');
    return;
  }
  const dur = 900, ini = performance.now();
  function passo(agora){
    const p = Math.min((agora - ini) / dur, 1);
    const eased = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(alvo * eased).toLocaleString('pt-BR');
    if(p < 1) requestAnimationFrame(passo);
  }
  requestAnimationFrame(passo);
}

export function renderStats(editais){
  const abertos = editais.filter(e => e.status === 'aberto' || e.status === 'encerrando');
  const vagas = editais.reduce((s,e) => s + numeroVagas(e.vagas), 0);
  const maior = Math.max(...editais.map(e => e.salario || 0));

  animarNumero(document.getElementById('s-abertos'), abertos.length);
  animarNumero(document.getElementById('s-vagas'), vagas);
  const el = document.getElementById('s-salario');
  if(el) el.textContent = brl.format(maior);
}

/* ---------------- feed de capturas ---------------- */

export function renderFeed(editais){
  const alvo = document.getElementById('feed');
  if(!alvo) return;

  const recentes = [...editais]
    .sort((a,b) => new Date(b.capturadoEm) - new Date(a.capturadoEm))
    .slice(0,5);

  alvo.innerHTML = recentes.map((e,i) => `
    <div class="feed-item" style="animation-delay:${i * 90}ms">
      <span class="dot" aria-hidden="true"></span>
      <span class="org">${esc(e.orgao)}<span>${esc(e.cargo)}</span></span>
      <span class="hora">${hora(e.capturadoEm)}</span>
    </div>`).join('');

  const pulso = document.getElementById('pulso-hora');
  if(pulso) pulso.textContent = hora(recentes[0]?.capturadoEm);
}

/* ---------------- menu mobile ---------------- */

export function ligarMenuMobile(){
  const btn = document.getElementById('menu-btn');
  const nav = document.getElementById('nav');
  if(!btn || !nav) return;

  btn.addEventListener('click', () => {
    const aberto = nav.classList.toggle('aberto');
    btn.setAttribute('aria-expanded', String(aberto));
  });
  nav.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => {
      nav.classList.remove('aberto');
      btn.setAttribute('aria-expanded','false');
    });
  });
}

/* ---------------- carga de dados ---------------- */

export async function carregarEditais(){
  const res = await fetch('data/editais.json');
  if(!res.ok) throw new Error(`HTTP ${res.status}`);
  const todos = await res.json();

  // Encerrado não aparece no site (decisão do Patrick, 27/08/2026).
  //
  // Antes ficavam numa aba "Encerrados". A ideia era mostrar que aquela
  // prefeitura abre concurso contábil, mas na prática ocupavam metade do
  // radar com o que ninguém pode mais fazer — e quem clicava chegava
  // numa inscrição fechada.
  //
  // O filtro fica AQUI, no único ponto por onde landing e plataforma
  // carregam os dados: em qualquer outro lugar, uma tela nova nasceria
  // mostrando encerrado de novo.
  //
  // Continuam no arquivo: o robô precisa deles para não recapturar o
  // mesmo edital como novidade a cada varredura.
  const hoje = new Date().toISOString().slice(0, 10);
  return todos.filter(e => {
    if(e.status === 'encerrado') return false;

    // Prazo vencido conta como encerrado mesmo que o status não tenha
    // sido recalculado ainda — foi o que deixou 4 editais vencidos
    // aparecendo como "encerrando".
    const fim = (e.inscricaoFim || '').slice(0, 10);
    if(fim && fim < hoje) return false;

    // Sem NENHUM link, o card é um beco sem saída: a pessoa lê o cargo,
    // vê o salário e não tem para onde ir. Some da tela, mas continua
    // no arquivo — quando a banca publicar o endereço, a varredura
    // preenche e ele volta sozinho.
    const temOnde = (e.siteInscricao || '').trim() || (e.pdfEdital || '').trim();
    return Boolean(temOnde);
  });
}


/**
 * Sombra na barra fixa quando a página rola.
 *
 * Sem isso, a barra clara sobre conteúdo claro perde o limite — o
 * texto que passa por baixo parece pertencer a ela. A sombra só
 * aparece depois que há conteúdo atrás, então no topo a barra
 * continua limpa.
 */
export function ligarBarraRolagem(){
  const barra = document.querySelector('.topbar');
  if(!barra) return;

  const avaliar = () => barra.classList.toggle('rolou', window.scrollY > 8);
  avaliar();
  addEventListener('scroll', avaliar, { passive:true });
}
