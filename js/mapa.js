/* ============================================================
   CFC ACADEMY · RADAR DE EDITAIS
   Mapa interativo do Brasil.
   ------------------------------------------------------------
   SVG estático com os 27 estados. Clicar num estado filtra a
   lista de editais daquele estado; clicar de novo limpa.

   Sem biblioteca de mapa: o SVG é leve, funciona offline e não
   depende de token de terceiro (o Mapbox do concorrente exige
   chave e cobra por carregamento).
   ============================================================ */

import { brl, dataBR, diasAte, esc, ESFERA } from './comum.js';

const UFS_NOME = {
  AC:'Acre', AL:'Alagoas', AM:'Amazonas', AP:'Amapá', BA:'Bahia',
  CE:'Ceará', DF:'Distrito Federal', ES:'Espírito Santo', GO:'Goiás',
  MA:'Maranhão', MG:'Minas Gerais', MS:'Mato Grosso do Sul',
  MT:'Mato Grosso', PA:'Pará', PB:'Paraíba', PE:'Pernambuco',
  PI:'Piauí', PR:'Paraná', RJ:'Rio de Janeiro', RN:'Rio Grande do Norte',
  RO:'Rondônia', RR:'Roraima', RS:'Rio Grande do Sul',
  SC:'Santa Catarina', SE:'Sergipe', SP:'São Paulo', TO:'Tocantins',
};

let editais = [];
let ufAtiva = '';
let aoFiltrar = null;

/* ---------------- densidade por estado ---------------- */

function contarPorUf(){
  const c = {};
  editais.forEach(e => {
    const uf = (e.uf || '').toUpperCase();
    if(uf) c[uf] = (c[uf] || 0) + 1;
  });
  return c;
}

/**
 * Faixa de intensidade (0 a 4) para colorir o estado. Usamos faixas
 * fixas e não escala contínua: com poucos editais por estado, um
 * gradiente contínuo faria 1 e 2 parecerem a mesma cor.
 */
function faixa(n){
  if(!n) return 0;
  if(n <= 2) return 1;
  if(n <= 5) return 2;
  if(n <= 10) return 3;
  return 4;
}

/* ---------------- render ---------------- */

function pintarMapa(){
  const contagem = contarPorUf();
  const svg = document.querySelector('#mapa-svg svg');
  if(!svg) return;

  Object.keys(UFS_NOME).forEach(uf => {
    const el = svg.getElementById(uf);
    if(!el) return;

    const n = contagem[uf] || 0;
    el.setAttribute('data-uf', uf);
    el.setAttribute('data-n', n);
    el.setAttribute('data-faixa', faixa(n));
    el.classList.toggle('ativo', ufAtiva === uf);
    el.classList.toggle('vazio', n === 0);

    // Acessibilidade: estado é um botão de verdade, alcançável por
    // teclado e anunciado com o número de editais.
    el.setAttribute('role', 'button');
    el.setAttribute('tabindex', n ? '0' : '-1');
    el.setAttribute('aria-label',
      `${UFS_NOME[uf]}: ${n} ${n === 1 ? 'edital' : 'editais'}`);
    el.setAttribute('aria-pressed', String(ufAtiva === uf));
  });
}

function renderTabela(){
  const alvo = document.getElementById('mapa-lista');
  if(!alvo) return;

  const lista = ufAtiva
    ? editais.filter(e => (e.uf || '').toUpperCase() === ufAtiva)
    : editais;

  const titulo = document.getElementById('mapa-titulo');
  if(titulo){
    titulo.textContent = ufAtiva
      ? `${UFS_NOME[ufAtiva]} — ${lista.length} ${lista.length === 1 ? 'edital' : 'editais'}`
      : `Brasil — ${lista.length} editais`;
  }

  const limpar = document.getElementById('mapa-limpar');
  if(limpar) limpar.hidden = !ufAtiva;

  if(!lista.length){
    alvo.innerHTML = `
      <p class="mapa-vazio">
        Nenhum edital aberto em ${esc(UFS_NOME[ufAtiva] || 'todo o país')} neste momento.
        O radar continua varrendo — clique em outro estado ou volte depois.
      </p>`;
    return;
  }

  // Prazo mais curto primeiro: é a informação que decide a ação.
  const ordenada = [...lista].sort((a, b) => {
    const da = diasAte(a.inscricaoFim), db = diasAte(b.inscricaoFim);
    if(da === null) return 1;
    if(db === null) return -1;
    return da - db;
  });

  alvo.innerHTML = `
    <div class="tabela-wrap">
      <table class="tabela-editais">
        <thead>
          <tr>
            <th scope="col">Órgão / Cargo</th>
            <th scope="col">Local</th>
            <th scope="col" class="num">Vagas</th>
            <th scope="col" class="num">Salário até</th>
            <th scope="col">Inscrições até</th>
            <th scope="col"><span class="sr-only">Ação</span></th>
          </tr>
        </thead>
        <tbody>
          ${ordenada.map(linha).join('')}
        </tbody>
      </table>
    </div>`;
}

function linha(e){
  const dias = diasAte(e.inscricaoFim);
  const urgente = dias !== null && dias >= 0 && dias <= 7;
  const local = [e.cidade, e.uf].filter(Boolean).join('/');

  return `
    <tr>
      <td>
        <a class="cargo" href="${esc(e.editalUrl)}">${esc(e.cargo)}</a>
        <span class="orgao">${esc(e.orgao)}</span>
      </td>
      <td>${esc(local) || '—'}<span class="esfera">${ESFERA[e.nivel] || ''}</span></td>
      <td class="num">${esc(e.vagas) || '—'}</td>
      <td class="num salario">${e.salario ? brl.format(e.salario) : '—'}</td>
      <td class="${urgente ? 'urgente' : ''}">
        ${e.inscricaoFim ? dataBR(e.inscricaoFim) : 'a confirmar'}
        ${dias !== null && dias >= 0
          ? `<span class="restam">${dias === 0 ? 'último dia' : dias + (dias === 1 ? ' dia' : ' dias')}</span>`
          : ''}
      </td>
      <td><a class="btn btn-ghost btn-sm" href="${esc(e.editalUrl)}">Ver</a></td>
    </tr>`;
}

/* ---------------- interação ---------------- */

function selecionar(uf){
  ufAtiva = (ufAtiva === uf) ? '' : uf;
  pintarMapa();
  renderTabela();
  aoFiltrar?.(ufAtiva);

  if(ufAtiva){
    document.getElementById('mapa-lista')
      ?.scrollIntoView({ behavior:'smooth', block:'nearest' });
  }
}

function ligarEventos(){
  const svg = document.querySelector('#mapa-svg svg');
  if(!svg) return;

  svg.addEventListener('click', ev => {
    const alvo = ev.target.closest('[data-uf]');
    if(alvo && alvo.dataset.n !== '0') selecionar(alvo.dataset.uf);
  });

  svg.addEventListener('keydown', ev => {
    if(ev.key !== 'Enter' && ev.key !== ' ') return;
    const alvo = ev.target.closest('[data-uf]');
    if(alvo && alvo.dataset.n !== '0'){
      ev.preventDefault();
      selecionar(alvo.dataset.uf);
    }
  });

  document.getElementById('mapa-limpar')
    ?.addEventListener('click', () => selecionar(ufAtiva));
}

/* ---------------- boot ---------------- */

export async function montarMapa(lista, { onFiltrar } = {}){
  editais = lista || [];
  aoFiltrar = onFiltrar;

  const caixa = document.getElementById('mapa-svg');
  if(!caixa) return;

  try{
    const res = await fetch('assets/brasil.svg');
    if(!res.ok) throw new Error(String(res.status));
    caixa.innerHTML = await res.text();
  }catch{
    // Sem o SVG a tabela ainda funciona; escondemos só o mapa.
    caixa.closest('.mapa-bloco')?.classList.add('sem-mapa');
    renderTabela();
    return;
  }

  pintarMapa();
  renderTabela();
  ligarEventos();
}
