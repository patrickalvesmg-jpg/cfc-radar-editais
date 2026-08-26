/* ============================================================
   CFC ACADEMY · RADAR DE EDITAIS
   Plataforma (área logada). Exige sessão — ver js/sessao.js.
   ============================================================ */

import {
  ESFERA, brl, dataBR, diasAte, numeroVagas, esc,
  cardEdital, prioridadePrazo, observar,
  renderStats, renderFeed, ligarMenuMobile, ligarBarraRolagem, carregarEditais,
} from './comum.js';

import { exigirLogin, usuario, sair } from './sessao.js';
import { montarMapa } from './mapa.js';
import { marcarVisita } from './novidades.js';
import { ligarAnuncios } from './anuncio.js';

/* Barreira de acesso. exigirLogin() já dispara o redirecionamento; aqui só
   evitamos montar a página enquanto o navegador troca de URL. O boot fica
   condicionado a esta constante em vez de um throw, que sujaria o console. */
const TEM_SESSAO = exigirLogin();

/* ---------------- favoritos (localStorage) ---------------- */

/** Favoritos ficam neste navegador, numa chave única.
 *
 *  Antes a chave incluía o e-mail da pessoa — o que obrigava a
 *  guardá-lo aqui. Como agora o site não retém dado pessoal
 *  nenhum (ver js/sessao.js), a chave é fixa: os favoritos são do
 *  NAVEGADOR, não de uma conta. Some se a pessoa limpar o
 *  navegador, e é esse o trade-off aceito. */
function chaveFavoritos(){
  return 'cfc:favoritos';
}

function carregarFavoritos(){
  try{ return new Set(JSON.parse(localStorage.getItem(chaveFavoritos()) || '[]')); }
  catch{ return new Set(); }
}

function salvarFavoritos(){
  try{ localStorage.setItem(chaveFavoritos(), JSON.stringify([...estado.favoritos])); }
  catch{ /* modo privado — favoritos ficam só nesta sessão */ }
}

/** Quantos cards a lista mostra por vez. Sem limite, os 127
 *  editais davam 34 mil pixels de altura — ninguém rola até o fim,
 *  e os filtros lá em cima somem da vista. */
const POR_PAGINA = 24;

const estado = {
  mostrando: POR_PAGINA,
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

  const visiveis = lista.slice(0, estado.mostrando);
  el.innerHTML = lista.length
    ? visiveis.map(e => cardEdital(e, { favorito: estado.favoritos.has(e.id) })).join('')
      + (lista.length > estado.mostrando ? `
        <button type="button" class="btn btn-ghost btn-block ver-mais" id="ver-mais-app">
          Ver mais ${Math.min(POR_PAGINA, lista.length - estado.mostrando)}
          de ${lista.length - estado.mostrando} restantes
        </button>` : '')
    : vazio();

  document.getElementById('ver-mais-app')?.addEventListener('click', () => {
    estado.mostrando += POR_PAGINA;
    render();
  });

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

  // Não há nome nem e-mail para exibir: o site não guarda dado da
  // pessoa (ver js/sessao.js). O menu passa a informar o ESTADO do
  // acesso, que é o que existe de fato. Inventar um "Olá, Fulano"
  // exigiria reter o nome — justamente o que decidimos não fazer.
  const desde = u.desde ? new Date(u.desde) : null;

  document.getElementById('saudacao').textContent = 'contador';
  document.getElementById('conta-nome').textContent = 'Acesso';
  document.getElementById('avatar').textContent = '✓';
  document.getElementById('menu-nome').textContent = 'Acesso liberado';
  document.getElementById('menu-email').textContent = desde
    ? `desde ${desde.toLocaleDateString('pt-BR')}`
    : 'neste navegador';

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
    t = setTimeout(() => { estado.mostrando = POR_PAGINA; estado.busca = ev.target.value; render(); }, 180);
  });

  document.getElementById('ordem').addEventListener('change', ev => {
    estado.mostrando = POR_PAGINA; estado.ordem = ev.target.value; render();
  });

  // abas de status
  document.querySelectorAll('.aba').forEach(aba => {
    aba.addEventListener('click', () => {
      document.querySelectorAll('.aba').forEach(a => a.setAttribute('aria-selected','false'));
      aba.setAttribute('aria-selected','true');
      estado.mostrando = POR_PAGINA; estado.status = aba.dataset.status;
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
      estado.mostrando = POR_PAGINA; estado.busca = '';
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
  ligarBarraRolagem();
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
  render();

  // O mapa FILTRA a lista (pedido do Patrick, ago/2026): clicar num
  // estado é a forma mais direta de achar concurso perto de casa, e
  // ter mapa e lista independentes fazia a pessoa filtrar duas vezes.
  montarMapa(estado.editais, {
    onFiltrar: uf => {
      estado.filtros.uf = uf || '';
      estado.mostrando = POR_PAGINA;
      render();
      // Leva a pessoa até a lista: o mapa fica acima dela, e sem isto
      // o clique parece não ter feito nada em tela pequena.
      document.getElementById('painel')?.scrollIntoView({ behavior:'smooth' });
    },
  });

  // Por último: registrar antes daqui apagaria a referência que o
  // selo "Novo" usa para comparar, e nada seria marcado.
  marcarVisita();
  ligarAnuncios();
}

if(TEM_SESSAO) iniciar();
