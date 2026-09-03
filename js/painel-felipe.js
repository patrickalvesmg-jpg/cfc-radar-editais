/* ============================================================
   CFC ACADEMY · RADAR DE EDITAIS
   Painel do dono — página SEM link em lugar nenhum do site,
   protegida só pelo nome do arquivo ser difícil de adivinhar
   (ver painel-felipe-*.html). Não tem sessão, não tem senha:
   quem tem a URL, tem acesso. Ver decisão em ago-set/2026.

   Mostra os editais capturados na ÚLTIMA varredura do robô, restrito
   aos que também estão ATIVOS no site público (decisão do Patrick,
   03/09/2026: o que a varredura pegou mas ainda não tem link, ou já
   venceu, fica de fora — não adianta o Felipe postar sobre um edital
   que ninguém consegue acessar). Por isso usamos carregarEditais(),
   o MESMO filtro de "pronto para visitante" que index/app usam —
   qualquer mudança nessa regra vale aqui também, sem duplicar lógica.
   ============================================================ */

import { brl, dataBR, esc, cardEdital, observar, carregarEditais } from './comum.js';

const brDataCurta = (iso) => {
  const [a, m, d] = iso.split('-');
  return `${d}/${m}`;
};

/** "Novo" aqui = capturado no MESMO DIA da varredura mais recente do
 *  acervo inteiro — não depende de navegador nem de visita anterior,
 *  ao contrário de js/novidades.js (que é "novo para quem visita"). */
function editaisDaUltimaVarredura(ativos){
  const datas = ativos
    .map(e => (e.capturadoEm || '').slice(0, 10))
    .filter(Boolean);
  if(!datas.length) return { data: '', lista: [] };

  const ultima = datas.reduce((max, d) => (d > max ? d : max), datas[0]);
  const lista = ativos
    .filter(e => (e.capturadoEm || '').slice(0, 10) === ultima)
    .sort((a, b) => (b.capturadoEm || '').localeCompare(a.capturadoEm || ''));

  return { data: ultima, lista };
}

function renderResumo(data, lista){
  document.getElementById('r-total').textContent = lista.length;
  document.getElementById('r-data').textContent = data ? brDataCurta(data) : '—';

  const estados = new Set(lista.map(e => e.uf).filter(Boolean));
  document.getElementById('r-estados').textContent = estados.size || '—';

  // Mesmo cálculo do "Maior salário no radar" do site público
  // (renderStats em comum.js) — de propósito sem filtro extra de
  // confirmação, para os dois números baterem. Um valor "a partir
  // de" ainda pode aparecer aqui; o próprio card individual já avisa
  // isso com o rótulo "A partir de" (ver cardEdital em comum.js).
  const salarios = lista.map(e => e.salario || 0).filter(s => s > 0);
  const maior = salarios.length ? Math.max(...salarios) : 0;
  document.getElementById('r-salario').textContent = maior ? brl.format(maior) : '—';
}

function renderLista(lista){
  const alvo = document.getElementById('lista');
  const vazio = document.getElementById('vazio');

  if(!lista.length){
    alvo.innerHTML = '';
    vazio.hidden = false;
    return;
  }

  vazio.hidden = true;
  // interativo:false tira favoritos (não fazem sentido aqui) mas
  // mantém o link "Ver edital" — o próprio cardEdital só omite as
  // ações com favorito, o link de detalhe do card fica no título.
  alvo.innerHTML = lista.map(e => cardEdital(e, { interativo: true, favorito: false })).join('');
  observar();
}

async function iniciar(){
  try{
    const ativos = await carregarEditais();
    const { data, lista } = editaisDaUltimaVarredura(ativos);
    renderResumo(data, lista);
    renderLista(lista);
  }catch(erro){
    console.error('[painel-felipe] falha ao carregar editais:', erro);
    document.getElementById('vazio').hidden = false;
    document.getElementById('vazio').textContent =
      'Não foi possível carregar os editais agora. Recarregue a página.';
  }
}

iniciar();
