/* ============================================================
   CFC ACADEMY · RADAR DE EDITAIS
   Plataforma (área logada). Exige sessão — ver js/sessao.js.
   ============================================================ */

import {
  ESFERA, brl, dataBR, diasAte, numeroVagas, esc,
  cardEdital, prioridadePrazo, observar,
  renderStats, renderFeed, ligarMenuMobile, carregarEditais,
} from './comum.js';

import { exigirLogin, usuario, sair, primeiroNome } from './sessao.js';

/* Barreira de acesso. exigirLogin() já dispara o redirecionamento; aqui só
   evitamos montar a página enquanto o navegador troca de URL. O boot fica
   condicionado a esta constante em vez de um throw, que sujaria o console. */
const TEM_SESSAO = exigirLogin();

/* ---------------- favoritos (localStorage) ---------------- */

/** Favoritos são por conta: a chave inclui o e-mail do usuário. */
function chaveFavoritos(){
  const u = usuario();
  return 'cfc:favoritos:' + (u ? u.email : 'anon');
}

function carregarFavoritos(){
  try{ return new Set(JSON.parse(localStorage.getItem(chaveFavoritos()) || '[]')); }
  catch{ return new Set(); }
}

function salvarFavoritos(){
  try{ localStorage.setItem(chaveFavoritos(), JSON.stringify([...estado.favoritos])); }
  catch{ /* modo privado — favoritos ficam só nesta sessão */ }
}

const estado = {
  editais: [],
  status: 'todos',
  busca: '',
  ordem: 'prazo',
  filtros: { uf:'', banca:'', nivel:'', escolaridade:'', salarioMin:'' },
  favoritos: carregarFavoritos(),
};

/* ---------------- filtragem e ordenação ---------------- */

function filtrar(){
  const termo = estado.busca.trim().toLowerCase();
  const f = estado.filtros;

  return estado.editais.filter(e => {
    if(estado.status !== 'todos' && e.status !== estado.status) return false;
    if(f.uf && e.uf !== f.uf) return false;
    if(f.banca && e.banca !== f.banca) return false;
    if(f.nivel && e.nivel !== f.nivel) return false;
    if(f.escolaridade && e.escolaridade !== f.escolaridade) return false;
    if(f.salarioMin && e.salario < Number(f.salarioMin)) return false;

    if(termo){
      const alvo = [e.orgao, e.cargo, e.banca, e.cidade, e.uf].join(' ').toLowerCase();
      if(!alvo.includes(termo)) return false;
    }
    return true;
  });
}

function ordenar(lista){
  const copia = [...lista];
  switch(estado.ordem){
    case 'salario':
      return copia.sort((a,b) => b.salario - a.salario);
    case 'vagas':
      return copia.sort((a,b) => numeroVagas(b.vagas) - numeroVagas(a.vagas));
    case 'recente':
      return copia.sort((a,b) => new Date(b.capturadoEm) - new Date(a.capturadoEm));
    case 'prazo':
    default:
      // "Prazo acabando" = quem ainda dá para se inscrever primeiro, do mais
      // urgente ao mais folgado. Encerrados e previstos não têm prazo corrente,
      // então caem para o fim em vez de disputar o topo — um prazo vencido
      // (dias negativos) ordenaria antes de um que fecha amanhã.
      return copia.sort((a,b) => {
        const pa = prioridadePrazo(a), pb = prioridadePrazo(b);
        if(pa.grupo !== pb.grupo) return pa.grupo - pb.grupo;
        return pa.chave - pb.chave;
      });
  }
}

/* ---------------- renderização ---------------- */

function vazio(){
  return `
  <div class="vazio">
    <div class="ico">
      <svg viewBox="0 0 24 24" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>
      </svg>
    </div>
    <h3>Nenhum edital com esses filtros</h3>
    <p>O radar continua varrendo. Tente ampliar a busca ou limpar os filtros para ver tudo que está no ar agora.</p>
    <button class="btn btn-ghost btn-sm" id="limpar-tudo">Limpar filtros</button>
  </div>`;
}

function render(){
  const lista = ordenar(filtrar());
  const el = document.getElementById('lista');

  el.innerHTML = lista.length
    ? lista.map(e => cardEdital(e, { favorito: estado.favoritos.has(e.id) })).join('')
    : vazio();

  const resumo = document.getElementById('resumo');
  resumo.textContent = lista.length
    ? `${lista.length} ${lista.length === 1 ? 'edital encontrado' : 'editais encontrados'}`
    : '';

  renderChips();
  atualizarContagens();
  observar();
}

function renderChips(){
  const rotulos = {
    uf:'Estado', banca:'Banca', nivel:'Esfera',
    escolaridade:'Escolaridade', salarioMin:'Salário mín.',
  };
  const chips = Object.entries(estado.filtros)
    .filter(([,v]) => v)
    .map(([k,v]) => {
      const txt = k === 'salarioMin' ? `acima de ${brl.format(Number(v))}`
                : k === 'nivel' ? (ESFERA[v] || v)
                : v;
      return `<span class="chip">${rotulos[k]}: ${esc(txt)}
        <button data-limpar="${k}" aria-label="Remover filtro ${rotulos[k]}">✕</button></span>`;
    });

  document.getElementById('chips').innerHTML = chips.join('');
}

function atualizarContagens(){
  // A contagem de cada aba ignora o filtro de status, mas respeita os demais.
  const statusReal = estado.status;
  document.querySelectorAll('.aba').forEach(aba => {
    estado.status = aba.dataset.status;
    aba.querySelector('.cont').textContent = filtrar().length;
  });
  estado.status = statusReal;
}

/* ---------------- agenda de provas ---------------- */

function renderAgenda(){
  const comProva = estado.editais
    .filter(e => e.dataProva && diasAte(e.dataProva) >= 0)
    .sort((a,b) => new Date(a.dataProva) - new Date(b.dataProva))
    .slice(0,5);

  const el = document.getElementById('agenda-lista');
  if(!comProva.length){
    el.innerHTML = `<p style="color:var(--cinza)">Nenhuma prova agendada no radar no momento.</p>`;
    return;
  }

  el.innerHTML = comProva.map(e => {
    const d = diasAte(e.dataProva);
    return `
    <article class="edital up" data-status="${esc(e.status)}">
      <div class="edital-main">
        <div class="edital-topo">
          <span class="badge badge-info">${dataBR(e.dataProva)}</span>
        </div>
        <h3>${esc(e.cargo)}</h3>
        <p class="orgao">${esc(e.orgao)}</p>
        <div class="edital-meta">
          <span class="item"><b>${esc(e.cidade)}</b>/${esc(e.uf)}</span>
          <span class="item">Banca <b>${esc(e.banca)}</b></span>
        </div>
      </div>
      <div class="edital-lado">
        <div class="prazo"><b>${d} ${d === 1 ? 'dia' : 'dias'}</b>para a prova</div>
      </div>
    </article>`;
  }).join('');
}

/* ---------------- popular selects de filtro ---------------- */

function popularFiltros(){
  const preencher = (id, valores) => {
    const sel = document.getElementById(id);
    valores.sort((a,b) => a.localeCompare(b,'pt-BR'))
      .forEach(v => sel.insertAdjacentHTML('beforeend', `<option value="${esc(v)}">${esc(v)}</option>`));
  };
  preencher('f-uf',    [...new Set(estado.editais.map(e => e.uf))]);
  preencher('f-banca', [...new Set(estado.editais.map(e => e.banca))]);
}

/* ---------------- menu de conta ---------------- */

function montarConta(){
  const u = usuario();
  if(!u) return;

  const nome = primeiroNome();
  document.getElementById('saudacao').textContent = nome;
  document.getElementById('conta-nome').textContent = nome;
  document.getElementById('avatar').textContent = nome.charAt(0).toUpperCase();
  document.getElementById('menu-nome').textContent = u.nome || nome;
  document.getElementById('menu-email').textContent = u.email;

  const btn = document.getElementById('conta-btn');
  const menu = document.getElementById('conta-menu');

  btn.addEventListener('click', ev => {
    ev.stopPropagation();
    const aberto = menu.classList.toggle('aberto');
    btn.setAttribute('aria-expanded', String(aberto));
  });

  // Fecha ao clicar fora ou apertar Esc.
  document.addEventListener('click', () => {
    menu.classList.remove('aberto');
    btn.setAttribute('aria-expanded','false');
  });
  document.addEventListener('keydown', ev => {
    if(ev.key === 'Escape'){
      menu.classList.remove('aberto');
      btn.setAttribute('aria-expanded','false');
    }
  });
  menu.addEventListener('click', ev => ev.stopPropagation());

  document.getElementById('sair').addEventListener('click', () => {
    sair();
    location.href = 'index.html';
  });
}

/* ---------------- eventos ---------------- */

function ligarEventos(){
  // busca com debounce — evita re-render a cada tecla
  let t;
  document.getElementById('busca').addEventListener('input', ev => {
    clearTimeout(t);
    t = setTimeout(() => { estado.busca = ev.target.value; render(); }, 180);
  });

  document.getElementById('ordem').addEventListener('change', ev => {
    estado.ordem = ev.target.value; render();
  });

  // abas de status
  document.querySelectorAll('.aba').forEach(aba => {
    aba.addEventListener('click', () => {
      document.querySelectorAll('.aba').forEach(a => a.setAttribute('aria-selected','false'));
      aba.setAttribute('aria-selected','true');
      estado.status = aba.dataset.status;
      render();
    });
  });

  // selects de filtro
  document.querySelectorAll('[data-filtro]').forEach(sel => {
    sel.addEventListener('change', () => {
      estado.filtros[sel.dataset.filtro] = sel.value;
      render();
    });
  });

  // painel de filtros
  const btnF = document.getElementById('btn-filtros');
  btnF.addEventListener('click', () => {
    const aberto = document.getElementById('filtros').classList.toggle('oculto');
    btnF.setAttribute('aria-expanded', String(!aberto));
  });

  // delegação: chips, favoritos e limpar-tudo
  document.body.addEventListener('click', ev => {
    const limpar = ev.target.closest('[data-limpar]');
    if(limpar){
      const chave = limpar.dataset.limpar;
      estado.filtros[chave] = '';
      const sel = document.querySelector(`[data-filtro="${chave}"]`);
      if(sel) sel.value = '';
      render();
      return;
    }

    if(ev.target.closest('#limpar-tudo')){
      Object.keys(estado.filtros).forEach(k => estado.filtros[k] = '');
      estado.busca = '';
      document.getElementById('busca').value = '';
      document.querySelectorAll('[data-filtro]').forEach(s => s.value = '');
      render();
      return;
    }

    const fav = ev.target.closest('[data-fav]');
    if(fav){
      const id = fav.dataset.fav;
      estado.favoritos.has(id) ? estado.favoritos.delete(id) : estado.favoritos.add(id);
      salvarFavoritos();
      const ativo = estado.favoritos.has(id);
      fav.setAttribute('aria-pressed', String(ativo));
      fav.setAttribute('aria-label', ativo ? 'Remover dos favoritos' : 'Salvar nos favoritos');
    }
  });

  ligarMenuMobile();
}

/* ---------------- altura da barra sticky ---------------- */

/**
 * A barra de busca é sticky e muda de altura (filtros abrem/fecham, abas
 * quebram linha). Publicamos a altura real em --busca-h para o conteúdo
 * abaixo reservar o espaço certo em vez de usar um valor chutado.
 */
function medirBarra(){
  const barra = document.querySelector('.busca-wrap');
  if(!barra) return;
  const h = Math.round(barra.getBoundingClientRect().height);
  document.documentElement.style.setProperty('--busca-h', `${h}px`);
}

function observarBarra(){
  medirBarra();
  const barra = document.querySelector('.busca-wrap');
  if(barra && 'ResizeObserver' in window){
    new ResizeObserver(medirBarra).observe(barra);
  }
  addEventListener('resize', medirBarra);
}

/* ---------------- boot ---------------- */

async function iniciar(){
  montarConta();

  try{
    estado.editais = await carregarEditais();
  }catch(err){
    console.error('Falha ao carregar editais:', err);
    document.getElementById('lista').innerHTML = `
      <div class="vazio">
        <h3>Não foi possível carregar os editais</h3>
        <p>Verifique a conexão e recarregue a página. Se você abriu o arquivo direto do disco,
           rode um servidor local — o navegador bloqueia fetch em file://</p>
      </div>`;
    return;
  }

  popularFiltros();
  ligarEventos();
  observarBarra();
  renderStats(estado.editais);
  renderFeed(estado.editais);
  renderAgenda();
  render();
}

if(TEM_SESSAO) iniciar();
