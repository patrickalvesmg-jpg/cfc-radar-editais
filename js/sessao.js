/* ============================================================
   CFC ACADEMY · RADAR DE EDITAIS
   Sessão — cadastro/login SIMULADOS em localStorage.
   ------------------------------------------------------------
   ATENÇÃO: isto NÃO é autenticação. Não há backend, não há
   verificação e a "senha" nem é guardada. Serve só para navegar
   o front-end como se o usuário estivesse logado.
   Na fase 2 este arquivo inteiro é substituído por auth real.
   ============================================================ */

const CHAVE = 'cfc:sessao';
const CHAVE_CONTAS = 'cfc:contas';

/** Quantos editais o visitante não-cadastrado vê por inteiro. */
export const LIMITE_GRATIS = 3;

/* ---------------- leitura ---------------- */

export function usuario(){
  try{ return JSON.parse(localStorage.getItem(CHAVE) || 'null'); }
  catch{ return null; }
}

export function logado(){
  return usuario() !== null;
}

/* ---------------- escrita ---------------- */

function contas(){
  try{ return JSON.parse(localStorage.getItem(CHAVE_CONTAS) || '{}'); }
  catch{ return {}; }
}

function salvarContas(c){
  try{ localStorage.setItem(CHAVE_CONTAS, JSON.stringify(c)); }catch{}
}

function abrirSessao(dados){
  const sessao = { ...dados, desde:new Date().toISOString() };
  try{ localStorage.setItem(CHAVE, JSON.stringify(sessao)); }catch{}
  return sessao;
}

/**
 * Cria a conta simulada. Rejeita e-mail já cadastrado para que o
 * fluxo de erro exista na demonstração.
 */
export function cadastrar({ nome, email, uf, interesse }){
  const base = contas();
  const chave = email.trim().toLowerCase();

  if(base[chave]){
    throw new Error('Este e-mail já tem cadastro. Entre com ele.');
  }

  base[chave] = { nome:nome.trim(), email:chave, uf, interesse,
                  criadoEm:new Date().toISOString() };
  salvarContas(base);
  return abrirSessao(base[chave]);
}

/**
 * "Login": aceita qualquer e-mail já cadastrado neste navegador.
 * Se não existir, cria na hora — é demonstração, não barreira.
 */
export function entrar({ email }){
  const base = contas();
  const chave = email.trim().toLowerCase();

  if(!base[chave]){
    base[chave] = { nome:chave.split('@')[0], email:chave, uf:'', interesse:'',
                    criadoEm:new Date().toISOString() };
    salvarContas(base);
  }
  return abrirSessao(base[chave]);
}

export function sair(){
  try{ localStorage.removeItem(CHAVE); }catch{}
}

/* ---------------- proteção de página ---------------- */

/**
 * Chame no topo de uma página privada. Se não houver sessão,
 * manda para o cadastro guardando o destino pretendido.
 */
export function exigirLogin(){
  if(logado()) return true;
  const destino = encodeURIComponent(location.pathname.split('/').pop() || 'app.html');
  location.replace(`cadastro.html?destino=${destino}`);
  return false;
}

/** Primeiro nome, para saudação. */
export function primeiroNome(){
  const u = usuario();
  if(!u) return '';
  return (u.nome || u.email || '').split(/[\s@.]/)[0]
    .replace(/^./, c => c.toUpperCase());
}
