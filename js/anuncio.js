/* ============================================================
   CFC ACADEMY · RADAR CONCURSOS CONTABILIDADE
   Anúncio do curso Contador Concursado.
   ------------------------------------------------------------
   Duas formas, conforme o espaço disponível:

     · COMPUTADOR — banner fixo na lateral esquerda, que acompanha
       a rolagem. Há espaço ocioso ali, e o anúncio ocupa sem
       disputar lugar com o conteúdo.

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

/** Rolagem mínima antes de mostrar o cartão do celular. Metade da
 *  primeira tela: o suficiente para a pessoa ter visto o que o
 *  site é. */
const GATILHO = 0.6;

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

/* ---------------- banner lateral (computador) ---------------- */

function montarLateral(){
  if(document.querySelector('.anuncio-lateral')) return;

  const a = document.createElement('a');
  a.className = 'anuncio-lateral';
  a.href = LINK;
  a.target = '_blank';
  a.rel = 'noopener';
  a.setAttribute('aria-label',
    'Contador Concursado — curso da CFC Academy para concursos contábeis');

  // A arte já diz o nome do curso e da marca. Repetir tudo embaixo
  // dela dobrava a informação e ocupava o dobro da altura — o texto
  // aqui é só o que a imagem NÃO diz: o convite.
  a.innerHTML = `
    <img src="assets/img/anuncio-ccc.svg" alt="" loading="lazy"
         onerror="this.remove()">
    <div class="anuncio-lateral-txt">
      <span class="btn btn-lima btn-sm btn-block">Começar a estudar</span>
    </div>`;

  document.body.appendChild(a);
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

  const estreito = window.matchMedia('(max-width: 1100px)');

  if(!estreito.matches){
    montarLateral();
    return;
  }

  // No celular, espera a rolagem. `once:true` para o cartão não
  // ser remontado a cada rolagem depois de fechado.
  const aoRolar = () => {
    if(window.scrollY > window.innerHeight * GATILHO){
      montarRodape();
      window.removeEventListener('scroll', aoRolar);
    }
  };
  window.addEventListener('scroll', aoRolar, { passive:true });
}
