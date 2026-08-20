/* ============================================================
   CFC ACADEMY · RADAR CONCURSOS CONTABILIDADE
   Faixa de aviso sobre a procedência dos editais.
   ------------------------------------------------------------
   Some sozinha quando o conteúdo é captura real — assim ninguém
   precisa lembrar de removê-la à mão, e ela também não fica
   exibida indevidamente depois da virada.

   O CRITÉRIO ANTIGO ESTAVA ERRADO e por isso a faixa nunca sumia:
   exigia `editalUrl` começando com "http", mas o edital real
   aponta para a PÁGINA INTERNA (`edital.html?id=...`) — que é a
   regra do produto, já que o site nunca manda o visitante para
   agregador concorrente. O critério contradizia o próprio produto.

   Critério atual — o edital é real quando tem os campos que só a
   captura produz: um prazo de inscrição e a origem (banca ou
   órgão) de onde o dado veio. Dado inventado não tem procedência.
   ============================================================ */

const faixa = document.getElementById('faixa-demo');

function medir(){
  if(!faixa) return;
  const h = Math.round(faixa.getBoundingClientRect().height);
  document.documentElement.style.setProperty('--faixa-demo-h', `${h}px`);
}

function esconder(){
  faixa?.remove();
  document.body.classList.remove('tem-demo');
  document.documentElement.style.removeProperty('--faixa-demo-h');
}

/** Real = veio de captura, não de exemplo escrito à mão. */
function capturado(e){
  return typeof e.inscricaoFim === 'string' && e.inscricaoFim.length >= 10
      && (typeof e.siteInscricao === 'string' && e.siteInscricao.startsWith('http')
          || typeof e.procedencia === 'string' && e.procedencia.startsWith('http'));
}

async function avaliar(){
  if(!faixa) return;

  // Mostra por padrão: se a checagem falhar, o aviso permanece.
  // O erro seguro aqui é avisar demais, nunca de menos.
  document.body.classList.add('tem-demo');
  medir();
  addEventListener('resize', medir);

  try{
    const res = await fetch('data/editais.json');
    if(!res.ok) return;
    const editais = await res.json();
    if(!Array.isArray(editais) || editais.length === 0) return;

    // A maioria esmagadora precisa ser captura real. Não exigimos
    // 100% porque um único registro incompleto não torna o acervo
    // inteiro uma demonstração — mas 5% já indica base de exemplo.
    const reais = editais.filter(capturado).length;
    if(reais / editais.length >= 0.95) esconder();
  }catch{
    /* mantém a faixa */
  }
}

avaliar();
