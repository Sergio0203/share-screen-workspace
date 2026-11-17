# Backlog comum

Este arquivo é a **única fonte de requisitos** do app: o que não está aqui está fora do escopo.
As duas implementações seguem **este** backlog, com os mesmos IDs e critérios de aceite.
Uma task só é "ok" quando todos os critérios de aceite dela passam.
O backlog diz **o que** o usuário consegue fazer, nunca **como** implementar.

Combinado antes de começar:

- **Modelo:** _(ex.: claude-opus-5-5)_
- **Esforço:** _(ex.: medium)_
- **Stack:** _(definir: livre para cada lado ou igual para os dois?)_

## Mudanças no backlog

- **2026-11-17 · T07, T08 e T09:** o recado passa a aparecer **ao vivo enquanto a pessoa digita**, sem precisar de
  `Enter`, e some **8 s depois da última tecla** (antes: `Enter` enviava e sumia depois de 5 s). Quem compartilha
  também vê a própria tela na aba do Telão. Quem já tinha feito essas tasks ajusta e registra como `fix`.

## Tasks

### T01 · Criar uma sala

Qualquer pessoa cria uma sala com um clique, sem cadastro, e já sai com o link pronto para mandar.

- [ ] Um clique em "Criar sala" cria uma sala nova e leva a pessoa para dentro dela.
- [ ] Cada sala tem um link único e difícil de adivinhar.
- [ ] Ao criar a sala, o link é copiado automaticamente para a área de transferência, e a interface mostra uma confirmação ("Link copiado!").
- [ ] Se o navegador bloquear a cópia automática, aparece um botão "Copiar link" que funciona, e o link fica visível na tela.
- [ ] Dentro da sala sempre há um jeito de copiar o link de novo.

### T02 · Entrar na sala pelo link

Quem recebe o link entra na sala e vê quem está lá.

- [ ] Abrir o link leva para a sala. Antes de entrar, a pessoa informa um nome de exibição.
- [ ] Depois de entrar, todos veem a lista de participantes com os nomes, atualizada em até 3 s quando alguém entra ou sai.
- [ ] Um link de sala que não existe mostra uma mensagem clara e um botão para criar uma sala nova.
- [ ] A sala aceita até 6 pessoas. A 7ª vê a mensagem "Sala cheia" e não entra.

### T03 · Conversar por voz

- [ ] A pessoa entra com o microfone desligado.
- [ ] Um botão liga e desliga o microfone. Com ele ligado, todos os outros ouvem a pessoa.
- [ ] Todos veem quem está com o microfone ligado ou desligado.
- [ ] Se a permissão do microfone for negada, aparece uma mensagem explicando como liberar, e o resto da sala continua funcionando.

### T04 · Ativar a webcam

- [ ] A pessoa entra com a câmera desligada.
- [ ] Um botão liga e desliga a câmera. Com ela ligada, todos os outros veem o vídeo da pessoa, identificado pelo nome.
- [ ] Desligar a câmera faz o vídeo sumir para todos em até 3 s.
- [ ] Se a permissão da câmera for negada, aparece uma mensagem explicando como liberar, e o resto da sala continua funcionando.

### T05 · Compartilhar a tela

A feature principal.

- [ ] Um botão "Compartilhar tela" deixa escolher entre a **tela inteira** ou a **janela de um app específico** (ex.: League of Legends).
- [ ] Os outros participantes começam a ver o compartilhamento em até 5 s.
- [ ] A pessoa pode parar pelo botão do app ou pelo botão nativo do navegador. Nos dois casos, os outros param de ver em até 3 s.
- [ ] O compartilhamento aparece em destaque, maior que as câmeras, e pode ir para tela cheia (sai com `Esc`).
- [ ] Se a permissão for negada ou o navegador não permitir compartilhar (ex.: celular), aparece uma explicação, e a pessoa continua podendo assistir.

### T06 · Escolher a qualidade do compartilhamento

- [ ] Antes de compartilhar, a pessoa escolhe entre pelo menos 3 qualidades: **720p 30 fps**, **1080p 30 fps** e **1080p 60 fps**.
- [ ] Dá para trocar a qualidade durante o compartilhamento, sem parar e recomeçar.
- [ ] A interface mostra para quem compartilha qual qualidade está ativa.
- [ ] A qualidade escolhida muda de fato a resolução e o fps enviados (dá para conferir nas estatísticas do navegador).

### T07 · Escrever na tela com `/`

Qualquer participante, inclusive quem está compartilhando, pode escrever um recado que aparece em cima do
compartilhamento, onde está o seu cursor. Para escrever, a pessoa precisa estar com a aba do Telão aberta e em foco.

- [ ] Com a aba do Telão em foco e o cursor sobre o compartilhamento, apertar `/` abre um campo de texto na posição do cursor.
- [ ] Quem está compartilhando também consegue escrever, desde que esteja na aba do Telão. Para isso, ela também vê a própria tela compartilhada na aba do Telão.
- [ ] O recado aparece para todos **enquanto a pessoa digita**, ao vivo (atualiza em até 1 s). Não é preciso apertar `Enter`.
- [ ] `Enter` só fecha o campo (o recado continua até o tempo de sumir). `Esc` fecha o campo e apaga o recado para todos na hora. Um campo fechado sem texto não mostra nada.
- [ ] Apertar `/` enquanto digita em outro campo (ex.: o nome) não abre nada.
- [ ] O texto tem no máximo 100 caracteres. O campo não deixa passar disso e mostra quantos caracteres faltam.
- [ ] O recado aparece para **todos** na sala, **inclusive para quem está compartilhando**, com o nome de quem escreveu.
- [ ] O recado aparece no mesmo ponto da imagem para todo mundo, mesmo com janelas de tamanhos diferentes.
- [ ] O texto é sempre mostrado como texto puro: `<b>oi</b>` aparece literalmente.

### T08 · O recado segue o cursor e some sozinho

- [ ] Enquanto o recado está visível, ele acompanha o cursor de quem escreveu, para todos.
- [ ] 8 s depois da última tecla, o recado some aos poucos, com um fade de 1 s. Se a pessoa voltar a digitar antes disso, a contagem recomeça.
- [ ] Se a mesma pessoa mandar outro recado, o novo substitui o anterior.
- [ ] Recados de várias pessoas podem aparecer ao mesmo tempo, sem um apagar o outro.

### T09 · Janela flutuante para quem transmite

Quem está compartilhando (ex.: jogando em outro app) precisa ver os recados sem voltar para a aba do Telão.

- [ ] Durante o compartilhamento, quem transmite tem um botão para abrir uma janela flutuante que fica sempre por cima dos outros apps.
- [ ] A janela mostra uma miniatura do próprio compartilhamento com os recados em cima, no mesmo ponto e com o mesmo comportamento de T07 e T08 (aparece enquanto a pessoa digita, segue o cursor, some 8 s depois da última tecla).
- [ ] A janela pode ser movida e redimensionada, e fechar a janela não para o compartilhamento.
- [ ] Na janela flutuante só se lê os recados: escrever com `/` é só na aba do Telão.
- [ ] Em navegadores sem suporte a janela flutuante, o botão não aparece, ou aparece desabilitado com uma explicação.

## Limitações conhecidas

Não contam como falha na avaliação:

- **Jogos em tela cheia exclusiva** podem aparecer pretos ao compartilhar só a janela. Para compartilhar um jogo,
  use o modo "janela sem bordas" (borderless) dele.
- **A janela flutuante (T09)** depende do navegador: funciona no Chrome e no Edge.
- O navegador não consegue desenhar por cima de outros apps, então fora da janela flutuante quem transmite só vê
  os recados na aba do Telão.

## Fora do escopo

Chat de texto, landing page, contas e login, gravação, apps nativos e qualquer coisa que não esteja nas tasks acima.
