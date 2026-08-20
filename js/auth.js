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

    const email = document.getElementById('email').value;

    if(!marcar('g-email', validarEmail(email))){
      document.getElementById('email').focus();
      return;
    }

    const btn = document.getElementById('enviar');
    btn.disabled = true;
    btn.textContent = 'Liberando seu acesso…';

    // Manda o e-mail para o ActiveCampaign. SEM `await` de
    // propósito: a pessoa não pode ficar esperando servidor de
    // terceiro, e o envio não é confirmável mesmo (ver js/crm.js).
    // Se o AC estiver fora do ar ou bloqueado, o acesso é liberado
    // do mesmo jeito — travar quem acabou de informar o e-mail
    // seria pior do que perder um contato na lista.
    enviarCRM({ email });

    // Grava só a marca de acesso: nenhum dado da pessoa.
    liberar();

    // Pequeno atraso para a transição não ficar brusca.
    setTimeout(() => { location.href = destino(); }, 400);
  });
}

// Quem já liberou não precisa ver o formulário de novo.
if(logado()){
  location.replace(destino());
}else{
  ligar();
}
