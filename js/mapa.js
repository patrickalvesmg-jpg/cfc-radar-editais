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
import { criarMapa3D } from './mapa3d.js';

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
let mapa3d = null;

let aoFiltrar = null;
const filtros = { busca:'', escolaridade:'', ordem:'prazo' };

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

  // O 3D lê a MESMA contagem que acabou de pintar os estados, então
  // as duas camadas nunca divergem.
  mapa3d?.atualizar(contagem, ufAtiva);
}


function renderTabela(){
  const alvo = document.getElementById('mapa-lista');
  if(!alvo) return;

  const lista = aplicarFiltros();

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

  const ordenada = [...lista].sort((a, b) => {
    if(filtros.ordem === 'salario') return (b.salario || 0) - (a.salario || 0);
    // Padrão: prazo mais curto primeiro — é o que decide a ação.
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
            <th scope="col">Organizadora</th>
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

/** Aplica UF + busca + escolaridade. A ordenação é feita depois. */
function aplicarFiltros(){
  const termo = filtros.busca.trim().toLowerCase();

  return editais.filter(e => {
    if(ufAtiva && (e.uf || '').toUpperCase() !== ufAtiva) return false;
    if(filtros.escolaridade && e.escolaridade !== filtros.escolaridade) return false;
    if(termo){
      const alvo = [e.orgao, e.cargo, e.cidade, e.banca, e.uf]
        .filter(Boolean).join(' ').toLowerCase();
      if(!alvo.includes(termo)) return false;
    }
    return true;
  });
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
      <td data-rot="Local">${esc(local) || '—'}<span class="esfera">${ESFERA[e.nivel] || ''}</span></td>
      <td data-rot="Organizadora"><span class="banca-cel">${esc(e.banca || '—')}</span></td>
      <td class="num" data-rot="Vagas">${esc(e.vagas) || '—'}</td>
      <td class="num salario" data-rot="Salário até">${e.salario ? brl.format(e.salario) : '—'}</td>
      <td data-rot="Inscrições até" class="${urgente ? 'urgente' : ''}">
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
  pintarChips();
  renderTabela();
  aoFiltrar?.(ufAtiva);

  if(ufAtiva){
    document.getElementById('mapa-lista')
      ?.scrollIntoView({ behavior:'smooth', block:'nearest' });
  }
}

/** Chips de estado: atalho para quem sabe onde quer procurar, e
 *  alternativa acessível ao mapa (o SVG exige mira precisa no celular). */
function montarChips(){
  const alvo = document.getElementById('chips-ufs');
  if(!alvo) return;

  const contagem = contarPorUf();
  const ufs = Object.keys(contagem)
    .filter(uf => contagem[uf] > 0)
    .sort((a, b) => contagem[b] - contagem[a] || a.localeCompare(b));

  alvo.innerHTML = ufs.map(uf => `
    <button class="chip-uf" data-uf="${uf}" aria-pressed="false">
      ${uf}<span class="cont">${contagem[uf]}</span>
    </button>`).join('');

  const todos = document.getElementById('cont-todos');
  if(todos) todos.textContent = editais.length;
}

function pintarChips(){
  document.querySelectorAll('.chip-uf').forEach(c => {
    const ativo = (c.dataset.uf || '') === ufAtiva;
    c.classList.toggle('ativo', ativo);
    c.setAttribute('aria-pressed', String(ativo));
  });
}

function ligarFiltros(){
  const busca = document.getElementById('f-busca');
  if(busca){
    let t;
    busca.addEventListener('input', ev => {
      clearTimeout(t);
      t = setTimeout(() => { filtros.busca = ev.target.value; renderTabela(); }, 180);
    });
  }

  document.getElementById('f-escolaridade')?.addEventListener('change', ev => {
    filtros.escolaridade = ev.target.value; renderTabela();
  });
  document.getElementById('f-ordem')?.addEventListener('change', ev => {
    filtros.ordem = ev.target.value; renderTabela();
  });

  document.querySelector('.filtros-rapidos')?.addEventListener('click', ev => {
    const chip = ev.target.closest('.chip-uf');
    if(!chip) return;
    const uf = chip.dataset.uf || '';
    // Chip "Todos" limpa; chip do estado ativo alterna para limpar.
    ufAtiva = (!uf || uf === ufAtiva) ? '' : uf;
    pintarMapa(); pintarChips(); renderTabela();
    aoFiltrar?.(ufAtiva);
  });
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

  montarChips();
  ligarFiltros();

  const caixa = document.getElementById('mapa-svg');
  if(!caixa){ renderTabela(); return; }

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

  // O canvas 3D entra ANTES de pintar, para receber a contagem já
  // na primeira passada. Se falhar (canvas indisponível, SVG fora
  // do padrão), o mapa plano continua funcionando sozinho — é por
  // isso que ele permanece no DOM.
  try{
    mapa3d = criarMapa3D(caixa, { onSelecionar: selecionar });
    if(mapa3d) caixa.classList.add('tem-3d');
  }catch(err){
    console.warn('[radar] 3D indisponível, usando o mapa plano:', err);
  }

  pintarMapa();
  renderTabela();
  ligarEventos();
}
