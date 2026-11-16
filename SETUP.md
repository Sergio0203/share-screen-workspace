# Setup

Passo a passo para deixar a máquina pronta para o experimento. Serve para os dois lados,
mas foi escrito pensando no **Perion (lado `nosdd`)**; o lado `sdd` já está configurado.

> **Atalho:** abra o Claude Code nesta pasta (`share-screen-workspace`) e peça
> **"faz o setup do lado nosdd"**. Ele segue este arquivo e confere tudo no final.

## 1. Pré-requisitos

| O quê | Como conferir |
|---|---|
| git | `git --version` |
| GitHub CLI logado na sua conta | `gh auth status` |
| Python 3.9+ | `python3 --version` |
| Claude Code (app desktop ou CLI) | já ter aberto pelo menos uma sessão |

Se o `gh` não estiver logado: `gh auth login` e depois `gh auth setup-git`, para o git usar o mesmo login no push.

Você já é colaborador dos repos `Sergio0203/share-screen-workspace` e `Sergio0203/share-screen-nosdd`;
se o GitHub mostrar um convite pendente, aceite antes de continuar.

## 2. Clonar os repos lado a lado

Os dois precisam ficar na **mesma pasta pai** (os comandos abaixo usam `../`):

```bash
mkdir -p ~/Share-screen && cd ~/Share-screen
gh repo clone Sergio0203/share-screen-workspace
gh repo clone Sergio0203/share-screen-nosdd
```

Resultado:

```
Share-screen/
├── share-screen-workspace/   métricas (este repo)
└── share-screen-nosdd/       onde você implementa
```

O `share-screen-nosdd` está vazio. Se o git reclamar ao dar o primeiro push, crie a branch: `git checkout -b main`.

## 3. Instalar o `/registrar`

A partir de `share-screen-workspace`:

```bash
python3 scripts/instalar_hook.py --lado nosdd --repo ../share-screen-nosdd
```

Isso grava um hook em `share-screen-nosdd/.claude/settings.local.json`. Esse arquivo é pessoal
e **não pode ir para o git**: adicione ao `.gitignore` do nosdd se o instalador avisar.

```bash
printf '.DS_Store\n.claude/settings.local.json\n' >> ../share-screen-nosdd/.gitignore
```

## 4. Conferir

```bash
python3 scripts/verificar_setup.py --lado nosdd --repo ../share-screen-nosdd
```

Tudo deve sair com ✅. Depois, o teste de verdade:

1. Abra uma **sessão nova** do Claude Code na pasta `share-screen-nosdd`.
2. Se o app pedir para aprovar o hook, aprove.
3. Mande só `/registrar`.
4. Deve aparecer a mensagem de uso **e o Claude não deve responder**. Se responder, o hook não está ativo.

Se o app recusar `/registrar` como comando desconhecido, use `registrar:` no lugar (ex.: `registrar: T01 implement ok`).

## 5. Combinar antes de começar

Preencham juntos o topo do [`tasks.md`](tasks.md):

- **Modelo e esforço** iguais para os dois, e conferir que a sessão está usando eles.
- **Stack**, se vai ser a mesma.
- **As tasks** com critérios de aceite.

## 6. Como trabalhar (lado `nosdd`)

Para cada task do `tasks.md`:

1. Abra (ou continue) uma sessão do Claude Code **na pasta `share-screen-nosdd`**.
2. Cole o texto da task e os critérios de aceite e peça para implementar. Do jeito que você trabalharia normalmente.
3. Teste. Se algo não atende o critério, peça a correção e conte isso como um retrabalho.
4. Quando terminar, no mesmo chat: `/registrar T01 implement ok` (ou `ajustes 2`, ou `falhou`).
5. Bug achado depois? Na sessão em que corrigir: `/registrar T01 fix ok`.

### Regras do lado `nosdd`

- **Nada de SDD:** não use Spec Kit nem escreva spec, plano ou lista de tasks em arquivo antes de implementar.
  O pedido vai direto do `tasks.md` para o Claude.
- **Não abra o workspace dentro da sessão de implementação** nem fale de métricas com o Claude que implementa.
- **Não edite `data/sdd.csv`**; o seu é o `data/nosdd.csv`, e o `/registrar` já cuida dele.
- **Não pergunte ao Claude** como o lado SDD está fazendo, e vice-versa.

As regras gerais estão no [README](README.md#regras-do-jogo).
