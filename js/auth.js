/* ============================================================
   CFC ACADEMY · RADAR DE EDITAIS
   Cadastro e login (simulados). Serve as duas páginas —
   detecta qual pelos campos presentes no formulário.
   ============================================================ */

import { cadastrar, entrar, logado } from './sessao.js';

const UFS = ['AC','AL','AM','AP','BA','CE','DF','ES','GO','MA','MG','MS','MT',
             'PA','PB','PE','PI','PR','RJ','RN','RO','RR','RS','SC','SE','SP','TO'];

const form = document.getElementById('form');
const ehCadastro = Boolean(document.getElementById('nome'));

/** Para onde ir depois de autenticar (?destino=... vem de exigirLogin). */
function destino(){
  const p = new URLSearchParams(location.search).get('destino');
  // Só aceita nome de arquivo local — evita redirecionar para fora do site.
  return (p && /^[\w.-]+\.html$/.test(p)) ? p : 'app.html';
}

/* ---------------- validação ---------------- */

function marcar(id, valido){
  document.getElementById(id).classList.toggle('invalido', !valido);
  return valido;
}

function validarEmail(v){
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v.trim());
}

function validar(dados){
  let ok = true;

  if(ehCadastro){
    ok = marcar('g-nome', dados.nome.trim().length >= 2) && ok;
    ok = marcar('g-uf', dados.uf !== '') && ok;
    ok = marcar('g-interesse', dados.interesse !== '') && ok;
    ok = marcar('g-senha', dados.senha.length >= 6) && ok;
  }else{
    ok = marcar('g-senha', dados.senha.length > 0) && ok;
  }

  ok = marcar('g-email', validarEmail(dados.email)) && ok;
  return ok;
}

function mostrarErro(msg){
  const cx = document.getElementById('erro-geral');
  document.getElementById('erro-geral-txt').textContent = msg;
  cx.style.display = 'flex';
}

function limparErro(){
  document.getElementById('erro-geral').style.display = 'none';
}

/* ---------------- envio ---------------- */

function ligar(){
  // Popular UFs no cadastro
  const selUf = document.getElementById('uf');
  if(selUf){
    UFS.forEach(uf => selUf.insertAdjacentHTML('beforeend',
      `<option value="${uf}">${uf}</option>`));
  }

  // Tirar o estado de erro assim que a pessoa corrige o campo
  form.querySelectorAll('.campo').forEach(campo => {
    campo.addEventListener('input', () => {
      campo.closest('.campo-grupo')?.classList.remove('invalido');
      limparErro();
    });
  });

  form.addEventListener('submit', ev => {
    ev.preventDefault();
    limparErro();

    const dados = {
      nome:      document.getElementById('nome')?.value || '',
      email:     document.getElementById('email').value,
      uf:        document.getElementById('uf')?.value || '',
      interesse: document.getElementById('interesse')?.value || '',
      senha:     document.getElementById('senha').value,
    };

    if(!validar(dados)){
      form.querySelector('.campo-grupo.invalido .campo')?.focus();
      return;
    }

    const btn = document.getElementById('enviar');
    btn.disabled = true;
    btn.textContent = ehCadastro ? 'Criando sua conta…' : 'Entrando…';

    // Pequeno atraso proposital: sem ele a transição fica brusca demais
    // e não dá para perceber o estado de carregamento na demonstração.
    setTimeout(() => {
      try{
        ehCadastro ? cadastrar(dados) : entrar(dados);
        location.href = destino();
      }catch(err){
        btn.disabled = false;
        btn.textContent = ehCadastro ? 'Criar conta e ver os editais' : 'Entrar';
        mostrarErro(err.message);
      }
    }, 450);
  });
}

// Quem já está logado não precisa ver o formulário.
if(logado()){
  location.replace(destino());
}else{
  ligar();
}
