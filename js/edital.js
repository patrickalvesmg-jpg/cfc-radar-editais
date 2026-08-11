/* ============================================================
   CFC ACADEMY · RADAR DE EDITAIS
   Página interna do edital.
   ------------------------------------------------------------
   Aqui o candidato encontra TUDO sobre o concurso sem sair da
   plataforma. O único link externo permitido é o da inscrição
   oficial (órgão ou banca organizadora) — nunca agregador.
   ============================================================ */

import {
  STATUS, ESFERA, brl, dataBR, diasAte, esc,
  ligarMenuMobile, carregarEditais, observar,
} from './comum.js';

import { logado } from './sessao.js';

/** Domínios que nunca devem virar link: agregadores concorrentes. */
const BLOQUEADOS = /pciconcursos|jcconcursos|concursosnobrasil|folhadirigida|qconcursos|grancursos|estrategiaconcursos/i;

function linkSeguro(url){
  if(!url || !/^https?:\/\//i.test(url)) return '';
  return BLOQUEADOS.test(url) ? '' : url;
}

function linha(rotulo, valor){
  if(!valor) return '';
  return `
    <div class="ficha-linha">
      <span class="ficha-rot">${esc(rotulo)}</span>
      <span class="ficha-val">${valor}</span>
    </div>`;
}

function render(e){
  const st = STATUS[e.status] || STATUS.encerrado;
  const dias = diasAte(e.inscricaoFim);
  const inscricao = linkSeguro(e.siteInscricao);

  let prazoTexto;
  if(e.status === 'previsto'){
    prazoTexto = 'Edital ainda não publicado';
  }else if(e.status === 'encerrado'){
    prazoTexto = `Encerrado em ${dataBR(e.inscricaoFim)}`;
  }else if(dias !== null && dias >= 0){
    prazoTexto = dias === 0
      ? `<b style="color:var(--warn)">Último dia</b> — até ${dataBR(e.inscricaoFim)}`
      : `<b>${dias} ${dias === 1 ? 'dia' : 'dias'}</b> — até ${dataBR(e.inscricaoFim)}`;
  }else{
    prazoTexto = 'Prazo a confirmar';
  }

  const local = e.cidade && e.uf ? `${esc(e.cidade)}/${esc(e.uf)}`
              : e.cidade || e.uf || '';

  document.title = `${e.cargo} — ${e.orgao} · Radar de Editais`;

  document.getElementById('detalhe').innerHTML = `
    <div class="edital-topo" style="margin-bottom:var(--s-4)">
      <span class="badge ${st.classe}">${st.rot}</span>
      <span class="badge badge-neutro">${ESFERA[e.nivel] || esc(e.nivel)}</span>
      ${e.revisado ? '' : '<span class="badge badge-warn">Aguardando conferência</span>'}
    </div>

    <h1 style="margin-bottom:var(--s-2)">${esc(e.cargo)}</h1>
    <p style="color:var(--cinza);font-size:1.1rem;margin-bottom:var(--s-6)">${esc(e.orgao)}</p>

    <div class="detalhe-grid">
      <div>
        <div class="card" style="padding:var(--s-5);margin-bottom:var(--s-4)">
          <h2 style="font-size:var(--t-h3);margin-bottom:var(--s-4)">Dados do concurso</h2>
          ${linha('Cargo', esc(e.cargo))}
          ${linha('Órgão', esc(e.orgao))}
          ${linha('Local', esc(local))}
          ${linha('Banca', esc(e.banca))}
          ${linha('Vagas', esc(e.vagas))}
          ${linha('Escolaridade', e.escolaridade === 'medio' ? 'Médio / Técnico' : 'Superior')}
          ${linha('Carga horária', esc(e.cargaHoraria))}
          ${linha('Esfera', ESFERA[e.nivel] || esc(e.nivel))}
        </div>

        <div class="card" style="padding:var(--s-5)">
          <h2 style="font-size:var(--t-h3);margin-bottom:var(--s-4)">Prazos</h2>
          ${linha('Inscrições', e.inscricaoInicio && e.inscricaoFim
              ? `${dataBR(e.inscricaoInicio)} a ${dataBR(e.inscricaoFim)}`
              : (e.inscricaoFim ? `até ${dataBR(e.inscricaoFim)}` : ''))}
          ${linha('Situação', prazoTexto)}
          ${linha('Data da prova', e.dataProva ? dataBR(e.dataProva) : '')}
          ${linha('Taxa de inscrição', e.taxaInscricao ? brl.format(e.taxaInscricao) : '')}
        </div>
      </div>

      <aside>
        <div class="card destaque-salario">
          <span class="rot">Remuneração até</span>
          <div class="valor">${e.salario ? brl.format(e.salario) : '—'}</div>
          ${e.salarioObs ? `<p class="obs">${esc(e.salarioObs)}</p>` : ''}
          ${e.salario ? '<p class="obs">Valor informado para o concurso. Confirme a remuneração do cargo no edital.</p>' : ''}
        </div>

        <div class="card" style="padding:var(--s-5);margin-top:var(--s-4)">
          <h2 style="font-size:var(--t-h3);margin-bottom:var(--s-3)">Como se inscrever</h2>
          ${inscricao ? `
            <p style="color:var(--cinza);font-size:var(--t-sm);margin-bottom:var(--s-4)">
              As inscrições são feitas no site oficial responsável pelo concurso.
            </p>
            <a href="${esc(inscricao)}" class="btn btn-lima btn-block"
               target="_blank" rel="noopener noreferrer nofollow">
              Ir para a inscrição oficial
            </a>
            <p class="micro-fonte">${esc(new URL(inscricao).hostname)}</p>
          ` : `
            <p style="color:var(--cinza);font-size:var(--t-sm)">
              O endereço de inscrição ainda não foi confirmado para este concurso.
              Procure o edital oficial no site do órgão responsável.
            </p>
          `}
        </div>

        <div class="card" style="padding:var(--s-5);margin-top:var(--s-4);
             background:linear-gradient(150deg,rgba(159,227,26,.12),var(--carvao) 60%);
             border-color:rgba(159,227,26,.3)">
          <span class="eyebrow" style="margin-bottom:var(--s-3)">CFC Academy</span>
          <h2 style="font-size:var(--t-h3);margin-bottom:var(--s-3)">Vai prestar este concurso?</h2>
          <p style="color:var(--cinza);font-size:var(--t-sm);margin-bottom:var(--s-4)">
            Conheça a preparação da CFC Academy para concursos da área contábil.
          </p>
          <a href="#" class="btn btn-ghost btn-block btn-sm">Conhecer o método</a>
        </div>
      </aside>
    </div>

    <p class="aviso-legal">
      Informação reunida automaticamente pelo Radar de Editais a partir de fontes
      públicas. Confirme sempre os dados no edital oficial antes de se inscrever.
    </p>
  `;

  observar();
}

function erro(msg){
  document.getElementById('detalhe').innerHTML = `
    <div class="vazio">
      <div class="ico">
        <svg viewBox="0 0 24 24" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>
        </svg>
      </div>
      <h3>${esc(msg)}</h3>
      <p>O edital pode ter sido removido do radar ou o endereço está incorreto.</p>
      <a href="index.html" class="btn btn-ghost btn-sm">Ver todos os editais</a>
    </div>`;
}

async function iniciar(){
  ligarMenuMobile();

  if(logado()){
    const cta = document.getElementById('cta-topo');
    if(cta){ cta.textContent = 'Abrir plataforma'; cta.href = 'app.html'; }
  }

  const id = new URLSearchParams(location.search).get('id');
  if(!id){ erro('Edital não informado'); return; }

  let editais;
  try{
    editais = await carregarEditais();
  }catch{
    erro('Não foi possível carregar os editais');
    return;
  }

  const edital = editais.find(e => e.id === id);
  if(!edital){ erro('Edital não encontrado'); return; }

  render(edital);
}

iniciar();
