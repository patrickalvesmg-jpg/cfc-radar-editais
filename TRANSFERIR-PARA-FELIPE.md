# Transferir o site para a conta do Felipe

O GitHub transfere repositório inteiro, com **histórico, Actions e
Pages**. Nada é perdido e nada precisa ser recriado.

São 6 passos: 2 seus, 1 do Felipe, 3 de ajuste depois.

---

## Antes: o que muda

**A URL do site muda.** De

```
https://patrickalvesmg-jpg.github.io/cfc-radar-editais/
```

para

```
https://USUARIO-DO-FELIPE.github.io/cfc-radar-editais/
```

O GitHub redireciona o endereço antigo por um tempo, mas não para
sempre. **Se o link já tiver sido divulgado**, vale registrar um
domínio próprio (ex.: `radar.cfcacademy.com.br`) e apontá-lo para o
Pages — aí uma troca de conta nunca mais muda o endereço.

**O que NÃO muda:** os 124 editais, a integração com o ActiveCampaign
(o formulário é da conta do Felipe, não do repositório) e todo o
histórico de commits.

---

## Passo 1 — você inicia a transferência

1. Abra <https://github.com/patrickalvesmg-jpg/cfc-radar-editais/settings>
2. Role até o fim, em **Danger Zone**
3. Clique em **Transfer** (Transfer ownership)
4. Digite o nome do repositório para confirmar: `cfc-radar-editais`
5. Em **New owner**, coloque o usuário do Felipe
6. Confirme

## Passo 2 — o Felipe aceita

Ele recebe um e-mail do GitHub com o convite. **Precisa aceitar em até
1 dia**, senão o convite expira e o passo 1 tem de ser refeito.

## Passo 3 — reativar o GitHub Pages

A transferência costuma manter o Pages, mas vale conferir:

1. No repositório (agora na conta dele): **Settings › Pages**
2. Em **Source**, deve estar `Deploy from a branch`
3. Branch: `main`, pasta `/ (root)`
4. Salvar

Em poucos minutos o site responde no novo endereço.

## Passo 4 — liberar a varredura automática

O workflow vai junto, mas o GitHub **desativa Actions agendadas em
repositório recém-transferido** (é proteção contra repo abandonado
rodando sozinho).

1. Aba **Actions** do repositório
2. Se aparecer aviso pedindo para habilitar workflows, clique em
   **I understand my workflows, go ahead and enable them**
3. Clique em **Varredura de editais** na lista à esquerda
4. Se houver o botão **Enable workflow**, clique nele

## Passo 5 — dar permissão de escrita ao robô

A varredura publica direto, então precisa poder gravar:

1. **Settings › Actions › General**
2. Role até **Workflow permissions**
3. Marque **Read and write permissions**
4. Salvar

> Sem isto a varredura roda, acha os editais e **falha ao publicar**,
> com erro de permissão negada.

## Passo 6 — testar antes de confiar

Não espere o horário agendado:

1. Aba **Actions › Varredura de editais**
2. **Run workflow › Run workflow**
3. Acompanhe — leva cerca de 50 minutos

Ao terminar, confira se o site mostra a data de captura atualizada.

---

## Depois: atualizar a identificação do robô

Em `robo/config.py`, o `USER_AGENT` traz a URL do site como forma de os
portais saberem quem os está acessando:

```python
USER_AGENT = (
    "CFCRadarEditais/1.0 (+https://patrickalvesmg-jpg.github.io/cfc-radar-editais/; "
    "contato via GitHub issues) Python-urllib"
)
```

Trocar para a URL nova **não é urgente** — nada quebra —, mas é questão
de honestidade com quem hospeda os dados: o endereço deve levar a uma
página que existe.

---

## Como fica a operação

| | |
|---|---|
| Quando roda | Todo dia, 06:00 (Brasília) |
| Onde roda | Servidores do GitHub — nenhum computador precisa estar ligado |
| Publica | Direto no site, sem aprovação |
| Se der problema | O job falha e o site **fica como está** |
| Tempo | ~50 min (a pausa entre requisições é obrigatória) |

### A rede de segurança

Como ninguém revisa mais, `robo/conferir.py` roda **antes** de publicar
e barra o que não pode ir ao ar:

- link para agregador concorrente (PCI, JC, Folha Dirigida…)
- cargo que não é da área contábil
- cargo com especialidade errada ("Auditor… - Engenharia Civil")
- edital vencido exibido como aberto
- edital sem UF (sumiria do mapa) ou com UF inexistente
- id duplicado (dois cards do mesmo concurso)
- acervo vazio ou abaixo de 40 editais (sinal de fonte quebrada)

Se qualquer uma disparar, **a publicação é abortada** e o site continua
com o conteúdo anterior. Um dia desatualizado é melhor que um dia
errado: quem lê o site decide se vai estudar meses para um concurso.

Para conferir na mão a qualquer momento:

```bash
python robo/conferir.py
```
