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
import { ehNovo, mostrarAviso } from './novidades.js';
import { logado } from './sessao.js';

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

/** Quantos editais a lista mostra por vez.
 *
 *  Sem limite a página tinha 30 mil pixels de altura com 119
 *  editais — o mapa some lá em cima e ninguém rola até o fim.
 *  20 enche a coluna sem afogar, e o botão amplia sob demanda. */
const POR_PAGINA = 20;
let mostrando = POR_PAGINA;

let aoFiltrar = null;
const filtros = { busca:'', escolaridade:'', nivel:'', ordem:'prazo' };

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

  rotularEstados(svg, contagem);
}

/**
 * Escreve a contagem por cima de cada estado.
 *
 * A cor já dá a densidade, mas exige consultar a legenda; o número
 * responde de imediato. Estado sem edital não recebe rótulo — zero
 * escrito 27 vezes vira ruído e esconde o que importa.
 *
 * A posição sai do `getBBox()` do próprio estado, então acompanha
 * qualquer mudança no SVG sem tabela de coordenadas para manter.
 */
function rotularEstados(svg, contagem){
  svg.querySelector('#camada-rotulos')?.remove();

  const camada = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  camada.setAttribute('id', 'camada-rotulos');
  camada.setAttribute('class', 'camada-rotulos');
  camada.setAttribute('aria-hidden', 'true');   // o <path> já é anunciado

  Object.keys(UFS_NOME).forEach(uf => {
    const n = contagem[uf] || 0;
    if(!n) return;

    const alvo = svg.getElementById(uf);
    if(!alvo) return;

    let caixa;
    try{ caixa = alvo.getBBox(); }catch{ return; }
    if(!caixa.width) return;

    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.setAttribute('class', 'rotulo-uf');
    g.setAttribute('data-uf', uf);

    const cx = caixa.x + caixa.width / 2;
    const cy = caixa.y + caixa.height / 2;

    // Disco atrás do número: sobre estado claro o texto sumia, e
    // contorno sozinho engrossava demais em número de dois dígitos.
    const disco = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    disco.setAttribute('cx', cx);
    disco.setAttribute('cy', cy);
    disco.setAttribute('r', n > 9 ? 8.4 : 7);
    disco.setAttribute('class', 'rotulo-disco');

    const txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    txt.setAttribute('x', cx);
    txt.setAttribute('y', cy);
    txt.setAttribute('class', 'rotulo-n');
    txt.textContent = String(n);

    g.append(disco, txt);
    camada.appendChild(g);
  });

  svg.appendChild(camada);
}


/**
 * Um edital de exemplo, para quem não tem conta. O mais urgente do
 * Brasil inteiro (menor prazo restante), ignorando qualquer filtro —
 * é sempre o mesmo, some quando urgência muda sozinho e não precisa
 * de manutenção manual (decisão do Patrick, 01/09/2026).
 */
function exemploMaisUrgente(){
  return [...editais].sort((a, b) => {
    const da = diasAte(a.inscricaoFim), db = diasAte(b.inscricaoFim);
    if(da === null) return 1;
    if(db === null) return -1;
    return da - db;
  })[0];
}

function renderTabela(){
  const alvo = document.getElementById('mapa-lista');
  if(!alvo) return;

  // Pedido do Patrick (01/09/2026): a primeira versão desse bloqueio
  // mostrava várias linhas raspadas ("Concurso aberto — Minas Gerais"
  // repetido oito vezes) e ficou estranho — muito espaço para pouca
  // informação de verdade. A segunda versão é mais direta: sem conta,
  // mapa/chips/busca/filtros continuam VISÍVEIS (dão volume, mostram
  // que a base é grande), mas usá-los não filtra nada — mostra o
  // convite de cadastro. A lista sempre tem UM edital de exemplo
  // completo (o mais urgente do Brasil todo), para provar que o dado é
  // real sem entregar o acervo peça por peça.
  if(!logado()){
    renderExemploUnico(alvo);
    return;
  }

  const lista = aplicarFiltros();

  const titulo = document.getElementById('mapa-titulo');
  if(titulo){
    titulo.textContent = ufAtiva
      ? `${UFS_NOME[ufAtiva]} — ${lista.length} ${lista.length === 1 ? 'edital' : 'editais'}`
      : `Brasil — ${lista.length} editais`;
  }

  const limpar = document.getElementById('mapa-limpar');
  if(limpar) limpar.hidden = !ufAtiva;

  // O contador acompanha o filtro: se a pessoa escolheu um estado,
  // ele conta as novidades DAQUELE estado. Dizer "12 novos" e mostrar
  // uma lista de 2 seria contradição na mesma tela.
  mostrarAviso(lista, document.getElementById('novidades-aviso'));

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

  const visiveis = ordenada.slice(0, mostrando);

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
          ${visiveis.map(linha).join('')}
        </tbody>
      </table>
    </div>

    ${ordenada.length > mostrando ? `
      <button type="button" class="btn btn-ghost btn-block ver-mais" id="ver-mais">
        Ver mais ${Math.min(POR_PAGINA, ordenada.length - mostrando)}
        de ${ordenada.length - mostrando} restantes
      </button>` : ''}`;

  document.getElementById('ver-mais')?.addEventListener('click', () => {
    mostrando += POR_PAGINA;
    renderTabela();
  });
}

/** Aplica UF + busca + escolaridade. A ordenação é feita depois. */
function aplicarFiltros(){
  const termo = filtros.busca.trim().toLowerCase();

  return editais.filter(e => {
    if(ufAtiva && (e.uf || '').toUpperCase() !== ufAtiva) return false;
    if(filtros.escolaridade && e.escolaridade !== filtros.escolaridade) return false;
    if(filtros.nivel && e.nivel !== filtros.nivel) return false;
    if(termo){
      const alvo = [e.orgao, e.cargo, e.cidade, e.banca, e.uf]
        .filter(Boolean).join(' ').toLowerCase();
      if(!alvo.includes(termo)) return false;
    }
    return true;
  });
}

/**
 * Tela sem cadastro: UM edital completo de exemplo + convite. Segunda
 * versão do bloqueio (01/09/2026) — a primeira mostrava várias linhas
 * raspadas ("Concurso aberto — Minas Gerais" repetido) e ficou
 * estranha, muito espaço vazio para pouca informação de verdade.
 *
 * O exemplo é sempre o edital de menor prazo do PAÍS TODO, ignorando
 * qualquer estado/filtro escolhido — interagir com mapa, chips, busca
 * ou os selects não muda o que aparece aqui; eles só abrem o convite
 * de cadastro (ver `pedirCadastro`). Isso é intencional: filtrar por
 * estado É o produto pago, então mostrar resultado filtrado de graça
 * devolveria de graça o que o cadastro deveria trocar.
 */
function renderExemploUnico(alvo){
  const titulo = document.getElementById('mapa-titulo');
  if(titulo) titulo.textContent = 'Um exemplo do que você encontra aqui';

  const limpar = document.getElementById('mapa-limpar');
  if(limpar) limpar.hidden = true;

  const exemplo = exemploMaisUrgente();
  if(!exemplo){
    alvo.innerHTML = `<p class="mapa-vazio">Nenhum edital aberto no momento.</p>`;
    return;
  }

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
        <tbody>${linha(exemplo)}</tbody>
      </table>
    </div>

    <div class="paywall paywall-cheio">
      <div class="cadeado" aria-hidden="true">
        <svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round">
          <rect x="4" y="10" width="16" height="11" rx="2"/>
          <path d="M8 10V7a4 4 0 0 1 8 0v3"/>
        </svg>
      </div>
      <h3>${editais.length} editais no radar agora</h3>
      <p>
        Este é só um exemplo. Crie sua conta grátis para filtrar por
        estado e ver todos os concursos, com salário, prazo e link de
        inscrição.
      </p>
      <a href="cadastro.html" class="btn btn-lima">Ver todos os editais</a>
      <p class="micro">É grátis. Não pedimos senha nem cartão.</p>
    </div>`;
}

/**
 * Sem conta, qualquer interação com mapa/chips/filtros/busca não
 * filtra nada — mostra o convite. Rola até ele em vez de recarregar a
 * lista, para não dar a impressão de que "não achou nada": a pessoa
 * clicou, algo aconteceu, e o que aconteceu é o convite.
 */
// Pedido do Patrick (01/09/2026): a primeira tentativa de filtrar sem
// conta merece uma chamada forte, não só rolar até o card que já
// estava na tela. Só a PRIMEIRA — variável em memória, não
// localStorage: "por visita" quer dizer que um F5 ou aba nova mostra
// de novo, o que é o comportamento certo para um aviso, diferente de
// uma preferência que devesse persistir.
let modalJaMostrado = false;

function fecharModalCadastro(){
  document.getElementById('modal-cadastro-fundo')?.remove();
  document.removeEventListener('keydown', fecharComEsc);
}

function fecharComEsc(ev){
  if(ev.key === 'Escape') fecharModalCadastro();
}

function mostrarModalCadastro(){
  if(document.getElementById('modal-cadastro-fundo')) return; // já aberto

  const fundo = document.createElement('div');
  fundo.id = 'modal-cadastro-fundo';
  fundo.className = 'modal-cadastro-fundo';
  fundo.setAttribute('role', 'dialog');
  fundo.setAttribute('aria-modal', 'true');
  fundo.setAttribute('aria-labelledby', 'modal-cadastro-titulo');
  fundo.innerHTML = `
    <div class="modal-cadastro">
      <button type="button" class="modal-cadastro-fechar" aria-label="Fechar">
        <svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18 6 6 18M6 6l12 12"/>
        </svg>
      </button>
      <div class="cadeado" aria-hidden="true">
        <svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round">
          <rect x="4" y="10" width="16" height="11" rx="2"/>
          <path d="M8 10V7a4 4 0 0 1 8 0v3"/>
        </svg>
      </div>
      <h3 id="modal-cadastro-titulo">Para filtrar, crie sua conta grátis</h3>
      <p>
        Filtrar por estado, cargo ou salário é exclusivo de quem tem
        conta. Leva menos de um minuto e já libera todos os
        ${esc(String(editais.length))} editais do radar.
      </p>
      <a href="cadastro.html" class="btn btn-lima">Criar conta grátis</a>
      <p class="micro">É grátis. Não pedimos senha nem cartão.</p>
    </div>`;

  document.body.appendChild(fundo);
  document.addEventListener('keydown', fecharComEsc);

  fundo.addEventListener('click', ev => {
    if(ev.target === fundo) fecharModalCadastro();
  });
  fundo.querySelector('.modal-cadastro-fechar')
    .addEventListener('click', fecharModalCadastro);
}

function pedirCadastro(){
  if(!modalJaMostrado){
    modalJaMostrado = true;
    mostrarModalCadastro();
  }

  document.getElementById('mapa-lista')
    ?.scrollIntoView({ behavior:'smooth', block:'nearest' });
}

function linha(e){
  const dias = diasAte(e.inscricaoFim);
  const urgente = dias !== null && dias >= 0 && dias <= 7;
  const local = [e.cidade, e.uf].filter(Boolean).join('/');

  return `
    <tr${ehNovo(e) ? ' data-novo="true"' : ''}>
      <td>
        <a class="cargo" href="${esc(e.editalUrl)}">${esc(e.cargo)}</a>
        ${ehNovo(e) ? '<span class="selo-novo">Novo</span>' : ''}
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
  // Sem conta, tocar num estado não filtra — abre o convite. Sai daqui
  // ANTES de mexer em `ufAtiva`: se deixasse mudar o estado ativo e só
  // trocasse o que a lista mostra, o mapa pintaria o estado escolhido
  // como se tivesse funcionado, e um refresh da página confirmaria o
  // filtro (porque `renderTabela` decide pelo login, não por isto).
  if(!logado()){ pedirCadastro(); return; }

  mostrando = POR_PAGINA;   // filtro novo, lista do começo
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
  // Sem conta, busca e os três selects não filtram — abrem o convite.
  // A checagem fica no TOPO de cada handler, antes de tocar em
  // `filtros`: se deixasse o valor mudar e só a renderização soubesse
  // ignorá-lo, o campo ficaria com um valor que não bate com o que a
  // tela mostra (ex.: select em "Federal" com o exemplo único visível,
  // que pode nem ser federal) — pequeno, mas é exatamente o tipo de
  // inconsistência que confunde no reload ou ao finalmente logar.
  const busca = document.getElementById('f-busca');
  if(busca){
    let t;
    busca.addEventListener('input', ev => {
      if(!logado()){ ev.target.value = ''; pedirCadastro(); return; }
      clearTimeout(t);
      t = setTimeout(() => { filtros.busca = ev.target.value; mostrando = POR_PAGINA; renderTabela(); }, 180);
    });
  }

  function ligarSelect(id, campo){
    const el = document.getElementById(id);
    el?.addEventListener('change', ev => {
      if(!logado()){ ev.target.value = ''; pedirCadastro(); return; }
      filtros[campo] = ev.target.value; mostrando = POR_PAGINA; renderTabela();
    });
  }
  ligarSelect('f-escolaridade', 'escolaridade');
  ligarSelect('f-nivel', 'nivel');
  ligarSelect('f-ordem', 'ordem');

  document.querySelector('.filtros-rapidos')?.addEventListener('click', ev => {
    const chip = ev.target.closest('.chip-uf');
    if(!chip) return;
    if(!logado()){ pedirCadastro(); return; }
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


  pintarMapa();
  renderTabela();
  ligarEventos();
}
