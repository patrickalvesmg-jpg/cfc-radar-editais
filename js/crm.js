/* ============================================================
   CFC ACADEMY · RADAR CONCURSOS CONTABILIDADE
   Envio do e-mail para o ActiveCampaign.
   ------------------------------------------------------------
   É SÓ O E-MAIL. Decisão de produto (Patrick, ago/2026): não
   pedimos nome, telefone nem senha. Menos dado coletado é menos
   exposição em LGPD — e o e-mail é o que sustenta a lista de
   avisos, que é o objetivo.

   POR QUE NÃO USAMOS A API DO ACTIVECAMPAIGN

   A API exige uma chave secreta. Este site é estático: o
   JavaScript roda no navegador do visitante, então qualquer
   chave colocada aqui fica LEGÍVEL para quem abrir o código —
   e robôs varrem sites atrás disso. Com a chave em mãos, um
   estranho lê e apaga a lista inteira de contatos.

   Por isso usamos o endpoint PÚBLICO de formulário
   (`/proc.php`), o mesmo que o embed oficial do AC usa. Ele foi
   feito para receber envio de página pública: aceita só criação
   de contato, nunca leitura. Não há segredo exposto.

   O QUE ISSO CUSTA: o AC não devolve resposta legível para
   requisição de outra origem (CORS). Mandamos em `no-cors`, o
   que significa que NÃO conseguimos confirmar se o contato
   entrou. Por isso a liberação do acesso nunca depende deste
   envio — ver `enviar()` e js/auth.js.
   ============================================================ */

/* ------------------------------------------------------------
   CONFIGURAÇÃO — preencher com os dados do seu ActiveCampaign.
   Passo a passo completo em ACTIVECAMPAIGN.md.

   Resumo: no AC, Site › Forms › crie um formulário só com o
   campo de e-mail › Integrate › Simple Embed. No código que
   aparecer, copie o `action` do form e o `value` do input "u".

   Enquanto ATIVO for false, nada é enviado e o site funciona
   normalmente — o acesso é liberado do mesmo jeito.
   ------------------------------------------------------------ */
export const CRM = {
  ativo: true,

  endpoint: 'https://cfcacademy.activehosted.com/proc.php',

  // ATENÇÃO: "u" e "f" são valores DIFERENTES, e é fácil errar.
  //   u = código do formulário (alfanumérico)
  //   f = número do formulário (o mesmo do embed.php?id=)
  // Mandar o número nos dois faz o contato ser rejeitado em silêncio —
  // e o site não tem como perceber, porque não lê a resposta do AC.
  // Estes vieram do embed real (id=85), conferidos no arquivo do AC.
  formulario: '6A875235C00B6',
  numero: '85',
};

/**
 * Manda o e-mail para o ActiveCampaign.
 *
 * NUNCA lança erro e NUNCA bloqueia: se o AC estiver fora do ar,
 * mal configurado ou o visitante tiver um bloqueador de anúncios
 * (que costuma barrar domínio de automação de marketing), o
 * acesso tem de ser liberado do mesmo jeito. Perder um contato na
 * lista é ruim; travar quem acabou de informar o e-mail é pior.
 *
 * @returns {Promise<boolean>} true se a requisição saiu — não é
 *          confirmação de que o contato entrou, porque o modo
 *          `no-cors` não deixa ler a resposta.
 */
export async function enviar({ email }){
  if(!CRM.ativo || !CRM.endpoint || !CRM.formulario) return false;

  const limpo = (email || '').trim().toLowerCase();
  if(!limpo) return false;

  try{
    const dados = new FormData();
    dados.append('u', CRM.formulario);
    dados.append('f', CRM.numero || CRM.formulario);
    dados.append('email', limpo);

    // O AC espera estes três em todo envio de formulário.
    dados.append('s', '');
    dados.append('c', '0');
    dados.append('m', '0');

    await fetch(CRM.endpoint, {
      method: 'POST',
      mode: 'no-cors',
      body: dados,
    });
    return true;
  }catch{
    // Silencioso de propósito: ver o comentário do cabeçalho.
    return false;
  }
}
