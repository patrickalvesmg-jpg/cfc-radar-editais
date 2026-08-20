/* ============================================================
   CFC ACADEMY · RADAR CONCURSOS CONTABILIDADE
   Liberação de acesso — SEM conta e SEM guardar dado pessoal.
   ------------------------------------------------------------
   COMO FUNCIONA E POR QUÊ

   A pessoa informa o e-mail, ele é enviado ao ActiveCampaign e o
   acesso é liberado. Aqui no site fica gravada apenas uma MARCA
   de "já liberou" — um carimbo de data, nada mais.

   O que este arquivo NÃO guarda, de propósito:
     · o e-mail          · nome        · telefone
     · senha             · qualquer identificador da pessoa

   Isso é decisão de produto (Patrick, ago/2026): a captura é só
   de e-mail e ele vive no ActiveCampaign, que é ferramenta com
   política e contrato próprios. O site não vira depositário de
   dado pessoal — o que simplifica muito a posição em LGPD: não
   há base de dados nossa para vazar, exportar ou ter de excluir
   a pedido do titular.

   Consequência aceita: não existe "entrar de volta" nem conta
   entre aparelhos. Quem trocar de navegador informa o e-mail de
   novo — e o AC reconhece o contato repetido, não duplica.
   ============================================================ */

const CHAVE = 'cfc:acesso';

/** Quantos editais o visitante vê por inteiro antes de liberar. */
export const LIMITE_GRATIS = 3;

/* ---------------- leitura ---------------- */

/**
 * A marca de acesso, ou null. É só `{ desde: <ISO> }` — nenhum
 * dado da pessoa. Guardamos a data para saber, no futuro, há
 * quanto tempo o acesso foi liberado, se um dia quisermos expirar.
 */
export function acesso(){
  try{
    const bruto = localStorage.getItem(CHAVE);
    if(!bruto) return null;
    const dado = JSON.parse(bruto);
    return (dado && typeof dado === 'object') ? dado : null;
  }catch{
    return null;
  }
}

/** Nome mantido por compatibilidade: o resto do site pergunta
 *  "pode ver tudo?", e a resposta continua sendo sim ou não. */
export function logado(){
  return acesso() !== null;
}

/* ---------------- escrita ---------------- */

/**
 * Libera o acesso neste navegador.
 *
 * Recebe o e-mail apenas para quem chama poder enviá-lo ao CRM —
 * ele NÃO é gravado aqui. O parâmetro existe para deixar isso
 * explícito na assinatura, e não por precisarmos dele.
 */
export function liberar(){
  const marca = { desde: new Date().toISOString() };
  try{ localStorage.setItem(CHAVE, JSON.stringify(marca)); }catch{}
  return marca;
}

/** Desfaz a liberação neste navegador. */
export function sair(){
  try{ localStorage.removeItem(CHAVE); }catch{}
}

/**
 * Barreira das páginas que exigem acesso liberado.
 * Redireciona para a página de liberação e volta depois.
 */
export function exigirLogin(){
  if(logado()) return true;
  const atual = location.pathname.split('/').pop() || 'app.html';
  location.replace(`cadastro.html?destino=${encodeURIComponent(atual)}`);
  return false;
}

/* ---------------- compatibilidade ----------------
   O site foi escrito quando havia conta com nome. Estas funções
   sobrevivem para não quebrar as telas, mas hoje não têm nome
   nenhum para devolver — e é assim que deve ser. */

export function usuario(){
  return acesso();
}

export function primeiroNome(){
  return '';
}
