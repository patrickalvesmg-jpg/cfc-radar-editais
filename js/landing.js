/* ============================================================
   CFC ACADEMY · RADAR DE EDITAIS
   Landing pública — amostra grátis + paywall.
   ============================================================ */

import {
  cardEdital, ordenarPorPrazo, observar,
  renderStats, renderFeed, ligarMenuMobile, carregarEditais,
} from './comum.js';

import { logado, LIMITE_GRATIS } from './sessao.js';

/**
 * Quem já tem sessão não deveria estar vendo o paywall.
 * Trocamos os CTAs por um atalho para a plataforma.
 */
function ajustarParaLogado(){
  if(!logado()) return;

  const topo = document.getElementById('cta-topo');
  if(topo){ topo.textContent = 'Abrir plataforma'; topo.href = 'app.html'; }

  document.querySelectorAll('a[href="cadastro.html"]').forEach(a => {
    a.href = 'app.html';
    if(/criar conta/i.test(a.textContent)) a.textContent = 'Abrir plataforma';
  });

  const entrar = document.querySelector('.nav a[href="login.html"]');
  if(entrar){ entrar.textContent = 'Meus editais'; entrar.href = 'app.html'; }
}

async function iniciar(){
  ligarMenuMobile();

  let editais;
  try{
    editais = await carregarEditais();
  }catch(err){
    console.error('Falha ao carregar editais:', err);
    document.getElementById('lista-gratis').innerHTML = `
      <div class="vazio">
        <h3>Não foi possível carregar os editais</h3>
        <p>Recarregue a página. Se você abriu o arquivo direto do disco,
           rode um servidor local — o navegador bloqueia fetch em file://</p>
      </div>`;
    return;
  }

  renderStats(editais);
  renderFeed(editais);

  // Os mais urgentes primeiro: é a melhor vitrine da plataforma.
  const ordenados = ordenarPorPrazo(editais);
  const gratis = ordenados.slice(0, LIMITE_GRATIS);
  const bloqueados = ordenados.slice(LIMITE_GRATIS);

  document.getElementById('lista-gratis').innerHTML =
    gratis.map(e => cardEdital(e)).join('');

  // Os bloqueados entram sem ações e sem link — o blur é visual,
  // então o conteúdo real não pode ficar clicável por baixo dele.
  const alvoBloqueado = document.getElementById('lista-bloqueada');
  const trancado = document.getElementById('trancado');

  if(bloqueados.length){
    // Mostra no máximo 4 cards borrados: o suficiente para dar volume
    // sem esticar a página à toa.
    alvoBloqueado.innerHTML = bloqueados.slice(0,4)
      .map(e => cardEdital(e, { interativo:false })).join('');
    document.getElementById('n-bloqueados').textContent = bloqueados.length;
  }else{
    trancado.style.display = 'none';
  }

  ajustarParaLogado();
  observar();
}

iniciar();
