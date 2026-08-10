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

/**
 * Sem editais bloqueados, o argumento de cadastro deixa de ser "veja o
 * resto" e passa a ser "seja avisado quando abrir" — que é verdadeiro
 * mesmo com o acervo pequeno, e é o valor real da conta.
 */
function ajustarSemBloqueio(total){
  const head = document.querySelector('#amostra .blk-head p');
  if(head){
    head.textContent = total === 1
      ? 'Este é o concurso da área contábil com inscrição aberta no radar neste momento.'
      : `Estes são os ${total} concursos da área contábil com inscrição aberta no radar neste momento.`;
  }

  const alvo = document.getElementById('trancado');
  if(!alvo) return;

  alvo.insertAdjacentHTML('afterend', `
    <div class="cta up" style="margin-top:var(--s-6)">
      <span class="eyebrow">Conta gratuita</span>
      <h2>Concurso de contador não abre todo dia.</h2>
      <p>
        O radar varre diários oficiais e bancas todos os dias. Crie sua conta
        para ser avisado assim que abrir um concurso do seu perfil — em vez de
        precisar voltar aqui para conferir.
      </p>
      <a href="cadastro.html" class="btn btn-lima">Criar conta grátis</a>
    </div>`);
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
    // Acervo menor que o limite grátis: não há o que bloquear. Some o
    // paywall e troca o discurso — prometer "veja o restante" quando não
    // há restante quebra a confiança logo na primeira visita.
    trancado.style.display = 'none';
    ajustarSemBloqueio(ordenados.length);
  }

  ajustarParaLogado();
  observar();
}

iniciar();
