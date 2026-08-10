/* ============================================================
   CFC ACADEMY · RADAR DE EDITAIS
   Faixa de demonstração.
   ------------------------------------------------------------
   Some sozinha quando o conteúdo deixar de ser exemplo — assim
   ninguém precisa lembrar de removê-la à mão no dia da virada,
   e ela também não fica exibida indevidamente depois disso.

   Critério: um edital é "real" quando tem link de verdade
   (não "#") E já passou por revisão humana ("revisado": true).
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

    const todosReais = editais.every(e =>
      typeof e.editalUrl === 'string' &&
      e.editalUrl.startsWith('http') &&
      e.revisado === true
    );

    if(todosReais) esconder();
  }catch{
    /* mantém a faixa */
  }
}

avaliar();
