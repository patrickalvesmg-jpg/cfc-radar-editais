/* ============================================================
   CFC ACADEMY · RADAR DE EDITAIS
   Landing pública — amostra grátis + paywall.
   ============================================================ */

import {
  cardEdital, ordenarPorPrazo, observar,
  renderStats, renderFeed, ligarMenuMobile, ligarBarraRolagem, carregarEditais,
} from './comum.js';

import { logado, LIMITE_GRATIS } from './sessao.js';
import { montarMapa } from './mapa.js';
import { marcarVisita } from './novidades.js';
import { ligarAnuncios } from './anuncio.js';

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
  ligarBarraRolagem();

  let editais;
  try{
    editais = await carregarEditais();
  }catch(err){
    console.error('Falha ao carregar editais:', err);
    // O aviso vai para onde houver lugar: a seção de amostra pode não
    // existir (landing enxuta), e aí a mensagem entra na lista do mapa.
    const aviso = `
      <div class="vazio">
        <h3>Não foi possível carregar os editais</h3>
        <p>Recarregue a página. Se você abriu o arquivo direto do disco,
           rode um servidor local — o navegador bloqueia fetch em file://</p>
      </div>`;
    const destino = document.getElementById('lista-gratis')
                 || document.getElementById('mapa-lista');
    if(destino) destino.innerHTML = aviso;
    return;
  }

  // A landing é vitrine de OPORTUNIDADE: mostra só o que ainda dá para
  // fazer. Editais encerrados ficam no acervo (têm aba própria dentro da
  // plataforma, em app.html), mas na página pública eles diluiriam a
  // promessa — quem chega quer saber onde se inscrever agora, não o que
  // já passou.
  const vivos = editais.filter(e => e.status !== 'encerrado');

  renderStats(vivos);
  renderFeed(vivos);

  // Os mais urgentes primeiro: é a melhor vitrine da plataforma.
  // Tudo abaixo deriva daqui — cards grátis, paywall e mapa —, então
  // partir de `vivos` mantém a página inteira coerente.
  const ordenados = ordenarPorPrazo(vivos);

  // A seção de amostra + paywall é OPCIONAL desde ago/2026, quando a
  // landing foi enxugada para mapa + filtros.
  //
  // Cada bloco confere o próprio alvo antes de escrever. Sem isso, um
  // `getElementById` devolvendo null lança TypeError e MATA o resto da
  // função — foi exatamente o que aconteceu: o mapa parou de aparecer
  // porque a linha do `lista-gratis` quebrava antes de `montarMapa`.
  const alvoGratis = document.getElementById('lista-gratis');
  if(alvoGratis){
    const gratis = ordenados.slice(0, LIMITE_GRATIS);
    const bloqueados = ordenados.slice(LIMITE_GRATIS);

    alvoGratis.innerHTML = gratis.map(e => cardEdital(e)).join('');

    // Os bloqueados entram sem ações e sem link — o blur é visual,
    // então o conteúdo real não pode ficar clicável por baixo dele.
    const alvoBloqueado = document.getElementById('lista-bloqueada');
    const trancado = document.getElementById('trancado');

    if(bloqueados.length && alvoBloqueado){
      // Mostra no máximo 4 cards borrados: o suficiente para dar volume
      // sem esticar a página à toa.
      alvoBloqueado.innerHTML = bloqueados.slice(0,4)
        .map(e => cardEdital(e, { interativo:false })).join('');
      const n = document.getElementById('n-bloqueados');
      if(n) n.textContent = bloqueados.length;
    }else if(trancado){
      // Acervo menor que o limite grátis: não há o que bloquear. Some o
      // paywall e troca o discurso — prometer "veja o restante" quando
      // não há restante quebra a confiança logo na primeira visita.
      trancado.style.display = 'none';
      ajustarSemBloqueio(ordenados.length);
    }
  }

  // O mapa usa TODOS os editais, inclusive os do paywall: esconder
  // onde existem vagas não cria desejo, só esconde o produto.
  montarMapa(ordenados);

  ajustarParaLogado();
  observar();

  // Por último: registrar a visita antes daqui apagaria a referência
  // que o selo "Novo" usa para comparar, e nada seria marcado.
  marcarVisita();
  ligarAnuncios();
}

iniciar();
