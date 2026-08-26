/* ============================================================
   CFC ACADEMY · RADAR CONCURSOS CONTABILIDADE
   Anúncio do curso Contador Concursado.
   ------------------------------------------------------------
   Duas formas, conforme o espaço disponível:

     · COMPUTADOR — faixa horizontal fixa no rodapé, atravessando a
       largura da página.

       Duas tentativas anteriores falharam, e o motivo é o mesmo:
       não existe espaço LATERAL neste layout. A margem tem 100px
       numa tela de 1440 (o container ocupa 1240), e dentro da
       coluna do mapa sobravam -266px abaixo da legenda — o cartão
       ficava fora da tela. Vertical espremido em 260px parecia
       escanteado, que foi como o Patrick descreveu.

       Horizontal resolve: 1240px de largura em vez de 260, a arte
       respira, e a faixa fica visível em qualquer ponto da rolagem
       sem cobrir conteúdo.

       POR QUE NÃO POP-UP: cobre o que a pessoa veio ler. Ela chegou
       para procurar concurso; janela na frente é obstáculo, não
       oferta. A faixa está sempre presente e não interrompe.

     · CELULAR — não há lateral. Aparece como um cartão no rodapé
       da tela, DEPOIS de a pessoa ter rolado um pouco: quem
       acabou de chegar ainda está entendendo o site, e interromper
       nesse momento é o que faz fechar a aba.

   Regras que respeitamos de propósito:
     · aparece UMA vez por sessão, não a cada rolagem;
     · fechar é definitivo naquele dia — insistir irrita e não
       converte;
     · nunca cobre o conteúdo no celular: empurra o rodapé.
   ============================================================ */

const LINK = 'https://cfcacademy.com.br/ccc/';
const CHAVE_FECHADO = 'cfc:anuncio-fechado';

/** Rolagem mínima antes de anunciar. 40% da primeira tela: o
 *  suficiente para a pessoa ter visto o que o site é, sem esperar
 *  demais e perder quem sai cedo. */
const GATILHO = 0.4;

function fechadoHoje(){
  try{
    const quando = localStorage.getItem(CHAVE_FECHADO);
    if(!quando) return false;
    // Volta a aparecer no dia seguinte: quem fechou ontem pode
    // estar interessado hoje, mas insistir na mesma visita não.
    return new Date(quando).toDateString() === new Date().toDateString();
  }catch{
    return false;
  }
}

function marcarFechado(){
  try{ localStorage.setItem(CHAVE_FECHADO, new Date().toISOString()); }catch{}
}

/* ---------------- faixa horizontal (computador) ---------------- */

function montarFaixa(){
  if(document.querySelector('.anuncio-faixa')) return;

  const cx = document.createElement('div');
  cx.className = 'anuncio-faixa';
  cx.innerHTML = `
    <a href="${LINK}" target="_blank" rel="noopener" class="anuncio-faixa-link">
      <span class="anuncio-selo" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 12l5 5L20 6"/>
        </svg>
      </span>

      <span class="anuncio-faixa-txt">
        <strong>Contador Concursado</strong>
        <span>A preparação completa da CFC Academy para concursos da área contábil</span>
      </span>

      <span class="btn btn-lima btn-sm">Começar a estudar</span>
    </a>
    <button type="button" class="anuncio-fechar" aria-label="Fechar anúncio">✕</button>`;

  cx.querySelector('.anuncio-fechar').addEventListener('click', () => {
    cx.classList.remove('visivel');
    marcarFechado();
    setTimeout(() => cx.remove(), 300);
  });

  document.body.appendChild(cx);
  requestAnimationFrame(() => cx.classList.add('visivel'));
}

/* ---------------- cartão de rodapé (celular) ---------------- */

function montarRodape(){
  if(document.querySelector('.anuncio-rodape')) return;

  const cx = document.createElement('div');
  cx.className = 'anuncio-rodape';
  cx.innerHTML = `
    <a href="${LINK}" target="_blank" rel="noopener" class="anuncio-rodape-link">
      <div>
        <strong>Contador Concursado</strong>
        <span>A preparação da CFC Academy para a área contábil</span>
      </div>
      <span class="btn btn-lima btn-sm">Ver curso</span>
    </a>
    <button type="button" class="anuncio-fechar" aria-label="Fechar anúncio">✕</button>`;

  cx.querySelector('.anuncio-fechar').addEventListener('click', () => {
    cx.classList.remove('visivel');
    marcarFechado();
    // Espera a transição terminar antes de tirar do DOM.
    setTimeout(() => cx.remove(), 300);
  });

  document.body.appendChild(cx);
  requestAnimationFrame(() => cx.classList.add('visivel'));
}

/* ---------------- decisão ---------------- */

export function ligarAnuncios(){
  if(fechadoHoje()) return;

  const estreito = window.matchMedia('(max-width: 920px)');
  const montar = estreito.matches ? montarRodape : montarFaixa;

  // Espera a rolagem nos DOIS formatos. Quem acabou de chegar ainda
  // está entendendo o site, e anunciar nesse momento é o que faz
  // fechar a aba — vale tanto para celular quanto para computador.
  const aoRolar = () => {
    if(window.scrollY > window.innerHeight * GATILHO){
      montar();
      window.removeEventListener('scroll', aoRolar);
    }
  };
  window.addEventListener('scroll', aoRolar, { passive:true });
}
