/* ============================================================
   CFC ACADEMY · RADAR CONCURSOS CONTABILIDADE
   Novidades desde a última visita.
   ------------------------------------------------------------
   O radar varre toda semana e traz dezenas de editais de uma vez
   (33 na varredura de 21/08). Sem sinalizar o que é novo, quem
   acompanha precisa reler a lista inteira para descobrir o que
   mudou — e desiste.

   "Novo" aqui é novo PARA AQUELA PESSOA, não para o site: o
   navegador guarda quando ela esteve aqui pela última vez. Quem
   entra todo dia vê só o que chegou desde ontem; quem some por um
   mês vê tudo do mês. Uma janela fixa de 7 dias falharia nos dois
   casos.

   O QUE GUARDAMOS: uma data, no navegador da própria pessoa. Nada
   vai para servidor nenhum — mesma regra do resto do site.
   ============================================================ */

const CHAVE = 'cfc:ultima-visita';

/** Antes de qualquer marcação, a visita anterior — lida uma vez e
 *  congelada, senão o próprio ato de registrar a visita de hoje
 *  apagaria a referência que precisamos para comparar. */
const VISITA_ANTERIOR = (() => {
  try{
    const bruto = localStorage.getItem(CHAVE);
    if(!bruto) return null;
    const d = new Date(bruto);
    return Number.isNaN(d.getTime()) ? null : d;
  }catch{
    return null;
  }
})();

/** Registra que a pessoa esteve aqui. Chamar DEPOIS de já ter
 *  usado `ehNovo`, nunca antes. */
export function marcarVisita(){
  try{ localStorage.setItem(CHAVE, new Date().toISOString()); }catch{}
}

/**
 * O edital entrou depois da última visita?
 *
 * Primeira visita devolve `false` para todos: marcar 127 editais
 * como novidade não informa nada — novidade só existe em relação
 * a algo já visto.
 */
export function ehNovo(edital){
  if(!VISITA_ANTERIOR) return false;

  const capturado = edital?.capturadoEm;
  if(!capturado) return false;

  const d = new Date(capturado);
  if(Number.isNaN(d.getTime())) return false;

  return d > VISITA_ANTERIOR;
}

/** Quantos editais da lista são novos para esta pessoa. */
export function contarNovos(lista){
  return (lista || []).filter(ehNovo).length;
}

/** Há quantos dias a pessoa não vem? Null na primeira visita. */
export function diasDesdeAUltimaVisita(){
  if(!VISITA_ANTERIOR) return null;
  const ms = Date.now() - VISITA_ANTERIOR.getTime();
  return Math.max(0, Math.floor(ms / 86400000));
}

/**
 * Mostra o aviso de novidades no topo da página.
 *
 * Some sozinho quando não há o que anunciar — barra vazia dizendo
 * "0 novos" é ruído, e o visitante de primeira viagem não tem
 * referência nenhuma para comparar.
 */
export function mostrarAviso(lista, alvo){
  if(!alvo) return 0;

  const novos = contarNovos(lista);
  if(!novos){ alvo.hidden = true; return 0; }

  const dias = diasDesdeAUltimaVisita();
  const quando = dias === 0 ? 'hoje'
               : dias === 1 ? 'desde ontem'
               : dias < 30  ? `nos últimos ${dias} dias`
               : 'desde a sua última visita';

  alvo.innerHTML = `
    <span class="novidades-n">${novos}</span>
    <span class="novidades-txt">
      ${novos === 1 ? 'edital novo' : 'editais novos'} ${quando}
      <b>— marcados na lista</b>
    </span>`;
  alvo.hidden = false;
  return novos;
}
