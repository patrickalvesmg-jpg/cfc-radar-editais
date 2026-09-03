/* ============================================================
   CFC ACADEMY · RADAR DE EDITAIS
   Painel do dono — página SEM link em lugar nenhum do site,
   protegida só pelo nome do arquivo ser difícil de adivinhar
   (ver painel-felipe-*.html). Não tem sessão, não tem senha:
   quem tem a URL, tem acesso. Ver decisão em ago-set/2026.

   Mostra os editais de UMA varredura por vez (seletor no topo),
   restrito aos que também estão ATIVOS no site público (decisão do
   Patrick, 03/09/2026: o que a varredura pegou mas ainda não tem
   link, ou já venceu, fica de fora — não adianta o Felipe postar
   sobre um edital que ninguém consegue acessar). Por isso usamos
   carregarEditais(), o MESMO filtro de "pronto para visitante" que
   index/app usam — qualquer mudança nessa regra vale aqui também,
   sem duplicar lógica.

   ATUALIZAÇÃO: automática, sem passo manual nenhum. O robô
   (.github/workflows/radar.yml) sobrescreve data/editais.json toda
   segunda-feira, e esta página lê esse mesmo arquivo — o próximo
   carregamento já mostra a varredura nova no seletor. Não existe
   rotina separada de "atualizar o relatório do Felipe" (decisão do
   Patrick, 03/09/2026).
   ============================================================ */

import { brl, dataBR, cardEdital, observar, carregarEditais } from './comum.js';

/** Agrupa os editais ativos por dia de captura — cada dia distinto é
 *  uma varredura (o robô roda uma vez por semana, então cada grupo
 *  tende a ser uma segunda-feira diferente). Mais recente primeiro. */
function agruparPorVarredura(ativos){
  const porData = new Map();
  for(const e of ativos){
    const data = (e.capturadoEm || '').slice(0, 10);
    if(!data) continue;
    if(!porData.has(data)) porData.set(data, []);
    porData.get(data).push(e);
  }
  return [...porData.entries()]
    .sort((a, b) => b[0].localeCompare(a[0]))
    .map(([data, lista]) => ({
      data,
      lista: [...lista].sort((x, y) => (y.capturadoEm || '').localeCompare(x.capturadoEm || '')),
    }));
}

function preencherSeletor(varreduras, aoTrocar){
  const sel = document.getElementById('f-semana');
  sel.innerHTML = varreduras.map((v, i) => `
    <option value="${v.data}">
      ${dataBR(v.data)}${i === 0 ? ' (mais recente)' : ''} — ${v.lista.length} editais
    </option>`).join('');
  sel.addEventListener('change', () => aoTrocar(sel.value));
}

function renderResumo(data, lista){
  document.getElementById('r-total').textContent = lista.length;
  document.getElementById('r-data').textContent = data ? dataBR(data) : '—';

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
    const varreduras = agruparPorVarredura(ativos);

    if(!varreduras.length){
      renderResumo('', []);
      renderLista([]);
      document.querySelector('.painel-semana').hidden = true;
      return;
    }

    const porData = new Map(varreduras.map(v => [v.data, v.lista]));
    const mostrar = (data) => {
      renderResumo(data, porData.get(data) || []);
      renderLista(porData.get(data) || []);
    };

    preencherSeletor(varreduras, mostrar);
    mostrar(varreduras[0].data); // mais recente por padrão
  }catch(erro){
    console.error('[painel-felipe] falha ao carregar editais:', erro);
    document.getElementById('vazio').hidden = false;
    document.getElementById('vazio').textContent =
      'Não foi possível carregar os editais agora. Recarregue a página.';
  }
}

iniciar();
