/* ============================================================
   CFC ACADEMY · RADAR CONCURSOS CONTABILIDADE
   Envio do e-mail para o ActiveCampaign.
   ------------------------------------------------------------
   É SÓ O E-MAIL. Decisão de produto (Patrick, ago/2026): não
   pedimos nome, telefone nem senha. Menos dado coletado é menos
   exposição em LGPD — e o e-mail é o que sustenta a lista de
   avisos, que é o objetivo.

   COMO ISTO FUNCIONA

   O ActiveCampaign expõe `/proc.php`, o mesmo endereço que o
   embed oficial usa. Não há chave secreta envolvida: o endpoint
   aceita criar contato, nunca ler — então nada fica exposto no
   código do site, que é público por natureza.

   Chamamos por JSONP (`<script src=...>`), exatamente como o
   embed do AC faz. Isso não é gambiarra: é o mecanismo que o
   próprio AC usa, e tem uma vantagem concreta sobre o `fetch`
   em `no-cors` — a resposta é executável, então CONSEGUIMOS
   saber se o contato entrou. O AC responde chamando
   `_show_thank_you(...)` no sucesso ou `_show_error(...)` na
   falha, e nós definimos essas funções abaixo.

   CAMPOS OBRIGATÓRIOS (descobertos lendo o embed real)

     u, f   número do formulário — no formulário 85, AMBOS são 85
     act    'sub'  — sem isto o AC ignora o envio em silêncio
     v      '2'    — versão do protocolo do formulário
     or     id de origem do formulário

   `act` e `v` são fáceis de esquecer e não dão erro visível: a
   requisição responde 302 e o contato simplesmente não entra.
   ============================================================ */

/* ------------------------------------------------------------
   CONFIGURAÇÃO — dados do formulário do ActiveCampaign.
   Passo a passo em ACTIVECAMPAIGN.md.
   Para trocar de formulário: pegue o embed em Site › Forms ›
   Integrate › Simple Embed e copie os `value` dos inputs
   escondidos (u, f, or).
   ------------------------------------------------------------ */
export const CRM = {
  ativo: true,

  endpoint: 'https://cfcacademy.activehosted.com/proc.php',

  // No formulário 85 os dois valem '85'. Não presuma que sejam
  // sempre iguais: leia os dois no embed ao trocar de formulário.
  u: '85',
  f: '85',
  or: '16041baa-b78b-4fdf-91f1-c38fb8f4a9da',
};

/** Quanto esperamos pela resposta do AC antes de desistir. */
const LIMITE_MS = 8000;

/**
 * Manda o e-mail para o ActiveCampaign.
 *
 * NUNCA lança erro: se o AC estiver fora do ar, mal configurado
 * ou barrado por um bloqueador de anúncios (comum com domínios
 * de automação de marketing), quem chamou segue em frente. O
 * acesso ao site não pode depender de servidor de terceiro —
 * perder um contato na lista é ruim, travar quem acabou de
 * informar o e-mail é pior.
 *
 * @returns {Promise<boolean>} true quando o AC confirmou o
 *          cadastro. false em falha, recusa ou tempo esgotado.
 */
export function enviar({ email }){
  return new Promise(resolve => {
    if(!CRM.ativo || !CRM.endpoint || !CRM.u){ resolve(false); return; }

    const limpo = (email || '').trim().toLowerCase();
    if(!limpo){ resolve(false); return; }

    let respondido = false;
    const anterior = {
      ok: window._show_thank_you,
      erro: window._show_error,
    };

    const encerrar = (sucesso) => {
      if(respondido) return;
      respondido = true;
      window._show_thank_you = anterior.ok;
      window._show_error = anterior.erro;
      script.remove();
      clearTimeout(relogio);
      resolve(sucesso);
    };

    // O AC responde chamando uma destas duas. Guardamos o que
    // existia antes para não atropelar nada da página.
    window._show_thank_you = () => encerrar(true);
    window._show_error = () => encerrar(false);

    const params = new URLSearchParams({
      u: CRM.u,
      f: CRM.f || CRM.u,
      s: '',
      c: '0',
      m: '0',
      act: 'sub',
      v: '2',
      email: limpo,
      jsonp: 'true',
    });
    if(CRM.or) params.set('or', CRM.or);

    const script = document.createElement('script');
    script.src = `${CRM.endpoint}?${params}`;
    script.charset = 'utf-8';
    // Bloqueador de anúncios costuma barrar este domínio: aí cai
    // no onerror e seguimos em frente, sem travar ninguém.
    script.onerror = () => encerrar(false);

    const relogio = setTimeout(() => encerrar(false), LIMITE_MS);
    document.head.appendChild(script);
  });
}
