/* ============================================================
   CFC ACADEMY · RADAR CONCURSOS CONTABILIDADE
   Liberação de acesso por e-mail.
   ------------------------------------------------------------
   A pessoa informa o e-mail, ele vai para o ActiveCampaign e o
   acesso é liberado neste navegador. Não há conta, senha nem
   dado guardado aqui — ver js/sessao.js.

   Serve as duas telas (cadastro.html e login.html). A de login
   existe por continuidade: quem chegar nela informa o e-mail do
   mesmo jeito e entra, sem tratamento diferente. Não há o que
   "recuperar" quando não se guarda senha.
   ============================================================ */

import { liberar, logado } from './sessao.js';
import { enviar as enviarCRM } from './crm.js';

const form = document.getElementById('form');

/** Para onde ir depois de liberar (?destino=... vem de exigirLogin). */
function destino(){
  const p = new URLSearchParams(location.search).get('destino');
  // Só aceita nome de arquivo local — evita redirecionar para fora do site.
  return (p && /^[\w.-]+\.html$/.test(p)) ? p : 'app.html';
}

/* ---------------- validação ---------------- */

function marcar(id, valido){
  document.getElementById(id)?.classList.toggle('invalido', !valido);
  return valido;
}

function validarEmail(v){
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v.trim());
}

/** Telefone é OPCIONAL: vazio passa. Preenchido precisa ter cara de
 *  número brasileiro — 10 dígitos (fixo) ou 11 (celular), com DDD.
 *  Validar evita mandar lixo para o AC, mas sem exigir formato: a
 *  pessoa digita como quiser e nós limpamos. */
function validarTelefone(v){
  const so = (v || '').replace(/\D/g, '');
  if(!so) return true;
  return so.length === 10 || so.length === 11;
}

function mostrarErro(msg){
  const cx = document.getElementById('erro-geral');
  if(!cx) return;
  document.getElementById('erro-geral-txt').textContent = msg;
  cx.style.display = 'flex';
}

function limparErro(){
  const cx = document.getElementById('erro-geral');
  if(cx) cx.style.display = 'none';
}

/* ---------------- envio ---------------- */

function ligar(){
  if(!form) return;

  // Tira o estado de erro assim que a pessoa corrige o campo.
  form.querySelectorAll('.campo').forEach(campo => {
    campo.addEventListener('input', () => {
      campo.closest('.campo-grupo')?.classList.remove('invalido');
      limparErro();
    });
  });

  form.addEventListener('submit', ev => {
    ev.preventDefault();
    limparErro();

    // O login.html tem só o e-mail; o cadastro.html tem os três.
    // Por isso lemos com `?.` — campo ausente vira string vazia e a
    // validação dele é pulada, em vez de quebrar a página inteira.
    const nome     = document.getElementById('nome')?.value ?? '';
    const email    = document.getElementById('email').value;
    const telefone = document.getElementById('telefone')?.value ?? '';

    let ok = validarEmail(email);
    marcar('g-email', ok);
    if(document.getElementById('nome')){
      ok = marcar('g-nome', nome.trim().length >= 2) && ok;
    }
    if(document.getElementById('telefone')){
      ok = marcar('g-telefone', validarTelefone(telefone)) && ok;
    }

    if(!ok){
      form.querySelector('.campo-grupo.invalido .campo')?.focus();
      return;
    }

    const btn = document.getElementById('enviar');
    btn.disabled = true;
    btn.textContent = 'Liberando seu acesso…';

    // O acesso é liberado antes de saber o resultado do envio: se o
    // ActiveCampaign estiver fora do ar ou barrado por bloqueador de
    // anúncios, quem acabou de preencher não pode ficar de fora.
    liberar();

    // ESPERAMOS a resposta antes de trocar de página — e isto não é
    // detalhe. O envio ao AC é um <script> que o navegador ainda está
    // baixando; se a página navegar antes de ele responder, a
    // requisição é CANCELADA e o contato nunca entra na lista. Foi
    // exatamente o que aconteceu: por linha de comando funcionava,
    // no navegador não, porque só ali existe o redirecionamento.
    //
    // O limite de 8s do crm.js protege contra espera infinita, e o
    // `.then` roda tanto no sucesso quanto na falha — ou seja, a
    // pessoa entra no site de qualquer forma.
    enviarCRM({ nome, email, telefone }).then(ok => {
      if(!ok && navigator.onLine){
        console.warn('[radar] o contato não foi confirmado pela lista de avisos');
      }
      location.href = destino();
    });
  });
}

// Quem já liberou não precisa ver o formulário de novo.
if(logado()){
  location.replace(destino());
}else{
  ligar();
}
