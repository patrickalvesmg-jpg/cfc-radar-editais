/* ============================================================
   CFC ACADEMY · RADAR CONCURSOS CONTABILIDADE
   Página interna do edital.
   ------------------------------------------------------------
   Aqui o candidato encontra TUDO sobre o concurso sem sair da
   plataforma. O único link externo permitido é o da inscrição
   oficial (órgão ou banca organizadora) — nunca agregador.
   ============================================================ */

import {
  STATUS, ESFERA, brl, dataBR, diasAte, esc,
  ligarMenuMobile, ligarBarraRolagem, carregarEditais, observar,
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
  const pdf = linkSeguro(e.pdfEdital);

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

  document.title = `${e.cargo} — ${e.orgao} · Radar Concursos Contabilidade`;

  // O campo `resumo` da fonte não é exibido de propósito: ele descreve
  // o concurso INTEIRO ("vagas para advogado, motorista, serviços
  // gerais") e cita salários de outros cargos. Num radar de
  // contabilidade isso é ruído, e engana — o número que aparece ali não
  // é o da nossa vaga. O editorial logo abaixo cobre o que importa.
  document.getElementById('detalhe').innerHTML = `
    <div class="edital-topo" style="margin-bottom:var(--s-4)">
      <span class="badge ${st.classe}">${st.rot}</span>
      <span class="badge badge-neutro">${ESFERA[e.nivel] || esc(e.nivel)}</span>
    </div>

    <h1 style="margin-bottom:var(--s-2)">${esc(e.cargo)}</h1>
    <p style="color:var(--cinza);font-size:1.1rem;margin-bottom:var(--s-4)">${esc(e.orgao)}</p>

    <div class="detalhe-grid">
      <div>
        <div class="card" style="padding:var(--s-5);margin-bottom:var(--s-4)">
          <h2 style="font-size:var(--t-h3);margin-bottom:var(--s-4)">Dados do concurso</h2>
          ${linha('Cargo', esc(e.cargo))}
          ${linha('Órgão', esc(e.orgao))}
          ${linha('Local', esc(local))}
          ${linha('Organizadora', e.bancaDominio && !BLOQUEADOS.test(e.bancaDominio)
              ? `<a class="link-banca" href="https://${esc(e.bancaDominio)}/"
                    target="_blank" rel="noopener noreferrer nofollow">${esc(e.banca)}</a>`
              : esc(e.banca))}
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

        ${blocoDetalhes(e)}
        ${blocoEditorial(e)}
      </div>

      <aside>
        <div class="card destaque-salario">
          <span class="rot">${e.salarioObs ? 'Remuneração a partir de' : 'Remuneração do cargo'}</span>
          <div class="valor">${e.salario ? brl.format(e.salario) : '—'}</div>
          ${e.salario ? `<p class="obs">${e.salarioObs
              ? 'O edital publicou apenas a faixa do concurso; este é o piso. O valor do cargo está no anexo de vencimentos.'
              : 'Vencimento inicial deste cargo, lido no anexo do edital. Confirme antes de se inscrever.'}</p>` : ''}
        </div>

        <div class="card" style="padding:var(--s-5);margin-top:var(--s-4)">
          <h2 style="font-size:var(--t-h3);margin-bottom:var(--s-3)">Como se inscrever</h2>
          ${pdf ? `
            <a href="${esc(pdf)}" class="btn btn-lima btn-block"
               target="_blank" rel="noopener noreferrer nofollow">
              <svg viewBox="0 0 24 24" width="17" height="17" fill="none"
                   stroke="currentColor" stroke-width="2.2"
                   stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <path d="M7 10l5 5 5-5M12 15V3"/>
              </svg>
              Abrir edital em PDF
            </a>
            <p class="nota-pdf">Arquivo oficial da banca, sempre na versão vigente.</p>
          ` : ''}

          ${inscricao ? `
            <p style="color:var(--cinza);font-size:var(--t-sm);margin:${pdf ? 'var(--s-5) 0 var(--s-4)' : '0 0 var(--s-4)'}">
              ${pdf
                ? 'A inscrição é feita no site oficial do concurso.'
                : 'O edital completo em PDF e a inscrição ficam no site oficial responsável pelo concurso.'}
            </p>
            <a href="${esc(inscricao)}" class="btn btn-lima btn-block"
               target="_blank" rel="noopener noreferrer nofollow">
              <svg viewBox="0 0 24 24" width="17" height="17" fill="none"
                   stroke="currentColor" stroke-width="2.2"
                   stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <path d="M7 10l5 5 5-5M12 15V3"/>
              </svg>
              ${pdf ? 'Ir para a inscrição' : 'Baixar edital e se inscrever'}
            </a>
            <p class="micro-fonte">${esc(new URL(inscricao).hostname)}</p>
            ${pdf ? '' : `
              <p class="nota-pdf">
                O arquivo fica no site da banca, não aqui: assim você sempre
                pega a versão vigente, inclusive depois de retificação.
              </p>`}
          ` : `
            <p style="color:var(--cinza);font-size:var(--t-sm)">
              O endereço de inscrição ainda não foi confirmado para este concurso.
              Procure o edital oficial no site do órgão responsável.
            </p>
          `}
        </div>

        <!-- Espaço do anúncio do curso.
             A arte definitiva entra em assets/img/anuncio-ccc.svg —
             basta trocar o arquivo, o link e o layout já estão prontos.
             Enquanto ela não existe, o bloco de texto abaixo ocupa o
             lugar: melhor um convite honesto que um retângulo vazio. -->
        <a class="card anuncio-curso" href="https://cfcacademy.com.br/ccc/"
           target="_blank" rel="noopener"
           aria-label="Conheça o curso da CFC Academy para concursos contábeis">
          <img src="assets/img/anuncio-ccc.svg" alt="" loading="lazy"
               onerror="this.remove()">
          <div class="anuncio-texto">
            <span class="eyebrow">CFC Academy</span>
            <h2>Vai prestar este concurso?</h2>
            <p>Conheça a preparação da CFC Academy para concursos da área contábil.</p>
            <span class="btn btn-lima btn-block btn-sm">Começar a estudar</span>
          </div>
        </a>
      </aside>
    </div>

    <p class="aviso-legal">
      Informação reunida automaticamente pelo Radar Concursos Contabilidade a partir de fontes
      públicas. Confirme sempre os dados no edital oficial antes de se inscrever.
    </p>
  `;

  observar();
}

/**
 * Editorial: texto de apoio gerado a partir dos dados capturados.
 * Vem pronto do robô (campo `editorial`), então é igual para todos os
 * leitores e indexável por buscador.
 *
 * O HTML vem de fonte própria — o robô monta só <p> e <b> a partir de
 * campos já validados, sem repassar texto de terceiro.
 */
function blocoEditorial(e){
  if(!e.editorial) return '';
  return `
    <article class="card editorial" style="padding:var(--s-5);margin-top:var(--s-4)">
      <span class="eyebrow" style="margin-bottom:var(--s-3)">Análise do radar</span>
      <h2 style="font-size:var(--t-h3);margin-bottom:var(--s-4)">Sobre este concurso</h2>
      ${e.editorial}
      <p class="editorial-nota">
        Texto produzido pelo Radar Concursos Contabilidade a partir dos dados
        publicados pela organizadora. Confirme sempre no edital oficial.
      </p>
    </article>`;
}

/**
 * Bloco com o que a matéria de origem contou além dos campos fixos:
 * etapas do certame, taxa, isenção, validade. Some inteiro quando não
 * há nada a dizer — cartão vazio é pior que cartão ausente.
 */
function blocoDetalhes(e){
  const d = e.detalhes || {};
  const temAlgo = d.etapas?.length || d.taxaTexto || d.isencao || d.validade || d.provaTexto;
  if(!temAlgo) return '';

  return `
    <div class="card" style="padding:var(--s-5);margin-top:var(--s-4)">
      <h2 style="font-size:var(--t-h3);margin-bottom:var(--s-4)">Sobre o concurso</h2>

      ${d.etapas?.length ? `
        <div class="det-item">
          <span class="det-rot">Etapas do certame</span>
          <ul class="det-etapas">
            ${d.etapas.map(x => `<li>${esc(x)}</li>`).join('')}
          </ul>
        </div>` : ''}

      ${d.taxaTexto ? `
        <div class="det-item">
          <span class="det-rot">Taxa de inscrição</span>
          <p>${esc(d.taxaTexto)}</p>
        </div>` : ''}

      ${d.isencao ? `
        <div class="det-item">
          <span class="det-rot">Isenção</span>
          <p>${esc(d.isencao)}</p>
        </div>` : ''}

      ${d.provaTexto ? `
        <div class="det-item">
          <span class="det-rot">Prova</span>
          <p>${esc(d.provaTexto)}</p>
        </div>` : ''}

      ${d.validade ? `
        <div class="det-item">
          <span class="det-rot">Validade</span>
          <p>${esc(d.validade)}</p>
        </div>` : ''}
    </div>`;
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
  ligarBarraRolagem();

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
