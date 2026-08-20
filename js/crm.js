/* ============================================================
   CFC ACADEMY · RADAR CONCURSOS CONTABILIDADE
   Envio do contato para o ActiveCampaign.
   ------------------------------------------------------------
   Captura nome, e-mail e telefone (Patrick, ago/2026). Só o
   e-mail é obrigatório: nome e telefone vão apenas quando a
   pessoa preenche, e campo vazio NÃO é enviado — mandar branco
   apagaria um dado que ela já tivesse informado antes.

   O site continua sem guardar nada disso: os três campos vão
   direto para o AC e o navegador retém só a marca de acesso
   (ver js/sessao.js). Quem responde por esses dados é o AC.

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
     or     id de origem — MUDA quando você edita o formulário
            no painel do AC; reconferir no embed a cada mudança

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
  or: 'a0961656-11b8-4672-a291-19a683f688e7',
};

/** Quanto esperamos pela resposta do AC antes de desistir.
 *
 *  4s é um meio-termo deliberado: a resposta real leva menos de 1s, e
 *  quem tem bloqueador de anúncios (que barra este domínio) não pode
 *  ficar olhando um botão travado. Passou disso, seguimos sem o
 *  contato — o acesso da pessoa vale mais que a linha na lista. */
const LIMITE_MS = 4000;

/**
 * Telefone no formato internacional que o AC exige.
 *
 * Testado contra o servidor: "83999991234" é RECUSADO com
 * `_show_error("Forneça um número de telefone válido (formato
 * +XXXXXXXXXXXXX)")`; "+5583999991234" é aceito. Como a pessoa
 * digita "(83) 99999-1234", a conversão tem de acontecer aqui —
 * exigir o formato dela seria empurrar o problema para quem usa.
 *
 * Devolve '' quando não dá para afirmar que é um número válido:
 * melhor cadastrar sem telefone do que ter o contato inteiro
 * recusado por causa dele.
 */
function paraE164(bruto){
  const so = (bruto || '').replace(/\D/g, '');
  if(!so) return '';

  // Já veio com o código do país.
  if(so.length === 12 || so.length === 13){
    return so.startsWith('55') ? `+${so}` : '';
  }
  // DDD + número: 10 (fixo) ou 11 (celular).
  if(so.length === 10 || so.length === 11) return `+55${so}`;

  return '';
}

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
export function enviar({ nome, email, telefone }){
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

    // Nome e telefone são opcionais no site: só vão quando existem.
    // Campo vazio enviado ao AC sobrescreveria com branco um dado que
    // a pessoa já tivesse informado num cadastro anterior.
    const primeiro = (nome || '').trim().split(/\s+/)[0];
    if(primeiro) params.set('firstname', primeiro);

    const tel = paraE164(telefone);
    if(tel) params.set('phone', tel);

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
