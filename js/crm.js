/* ============================================================
   CFC ACADEMY · RADAR CONCURSOS CONTABILIDADE
   Envio do cadastro para o ActiveCampaign.
   ------------------------------------------------------------
   POR QUE NÃO USAMOS A API DO ACTIVECAMPAIGN

   A API exige uma chave secreta. Este site é estático: o
   JavaScript roda no navegador do visitante, então qualquer
   chave colocada aqui fica LEGÍVEL para todo mundo que abrir o
   código-fonte — e robôs varrem sites atrás disso. Com a chave
   em mãos, um estranho lê e apaga a lista inteira de contatos.

   Por isso usamos o endpoint PÚBLICO de formulário
   (`/proc.php`), o mesmo que o embed oficial do AC usa. Ele foi
   feito para receber envio de página pública: aceita só criação
   de contato, nunca leitura. Não há segredo exposto.

   O QUE ISSO CUSTA: o AC não devolve resposta legível para
   requisição de outra origem (CORS). Mandamos em `no-cors`, o
   que significa que NÃO conseguimos confirmar se o contato
   entrou. Por isso a sessão local nunca depende deste envio —
   ver `enviar()` abaixo.
   ============================================================ */

/* ------------------------------------------------------------
   CONFIGURAÇÃO — preencher com os dados do seu ActiveCampaign.

   Onde achar (leva 2 minutos):
   1. No AC, vá em  Site  ›  Forms  e crie (ou abra) um formulário.
   2. Clique em  Integrate  ›  aba  Simple Embed.
   3. No código que aparecer, procure:
        <form ... action="https://SUACONTA.activehosted.com/proc.php"
        <input name="u" value="27">      ← ID do formulário
        <input name="f" value="27">
      Copie o endereço e o valor de "u".
   4. Ainda no formulário, crie os campos personalizados de
      ESTADO e INTERESSE. O AC dá a cada um um nome tipo
      "field[3,0]" — copie exatamente como aparece no embed.

   Enquanto ATIVO for false, nada é enviado e o site funciona
   normalmente (a conta fica só no navegador, como hoje).
   ------------------------------------------------------------ */
export const CRM = {
  ativo: false,

  // Ex.: 'https://cfcacademy.activehosted.com/proc.php'
  endpoint: '',

  // Valor do input "u" no embed. Ex.: '27'
  formulario: '',

  // Nomes dos campos personalizados, copiados do embed do AC.
  // Deixe vazio o que você não tiver criado — o campo é ignorado.
  campos: {
    estado: '',     // ex.: 'field[3,0]'
    interesse: '',  // ex.: 'field[4,0]'
  },
};

/** Divide "João da Silva" em primeiro nome e sobrenome, que é como
 *  o AC guarda. Sem sobrenome, manda só o primeiro. */
function separarNome(completo){
  const partes = (completo || '').trim().split(/\s+/);
  return {
    primeiro: partes[0] || '',
    ultimo: partes.length > 1 ? partes.slice(1).join(' ') : '',
  };
}

/**
 * Manda o contato para o ActiveCampaign.
 *
 * NUNCA lança erro e NUNCA bloqueia: se o AC estiver fora do ar,
 * mal configurado ou o visitante tiver um bloqueador de anúncios
 * (que costuma barrar domínio de automação de marketing), o
 * cadastro no site tem de acontecer do mesmo jeito. Perder um
 * contato na lista é ruim; impedir a pessoa de entrar é pior.
 *
 * @returns {Promise<boolean>} true se a requisição saiu — não é
 *          confirmação de que o contato entrou, porque o modo
 *          `no-cors` não deixa ler a resposta.
 */
export async function enviar({ nome, email, uf, interesse }){
  if(!CRM.ativo || !CRM.endpoint || !CRM.formulario) return false;

  try{
    const { primeiro, ultimo } = separarNome(nome);
    const dados = new FormData();

    dados.append('u', CRM.formulario);
    dados.append('f', CRM.formulario);
    dados.append('email', (email || '').trim().toLowerCase());
    dados.append('firstname', primeiro);
    if(ultimo) dados.append('lastname', ultimo);

    if(CRM.campos.estado && uf) dados.append(CRM.campos.estado, uf);
    if(CRM.campos.interesse && interesse) dados.append(CRM.campos.interesse, interesse);

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
