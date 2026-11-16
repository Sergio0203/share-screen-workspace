# share-screen-workspace

Workspace do experimento **SDD vs. sem SDD**: o mesmo app de compartilhamento de tela é construído duas vezes,
com o Claude Code, e aqui guardamos as métricas de cada lado para comparar no final.

| Lado    | Quem   | Repo                 |
|---------|--------|----------------------|
| `sdd`   | Sergio | `share-screen-sdd`   |
| `nosdd` | Perion | `share-screen-nosdd` |

## Estrutura

```
tasks.md            backlog comum: as MESMAS tasks, com os mesmos IDs, nos dois lados
data/sdd.csv        registros do lado SDD (só o Sergio edita)
data/nosdd.csv      registros do lado sem SDD (só o Perion edita)
scripts/tokens.py   lê os transcripts do Claude Code e soma tokens/tempo/prompts de uma sessão
scripts/log.py      registra uma linha no CSV (tokens e tempo vêm automáticos do transcript)
scripts/report.py   gera reports/comparativo.md com o comparativo dos dois lados
scripts/hook_registrar.py  hook do Claude Code que atende o /registrar no chat
scripts/instalar_hook.py   instala esse hook no repo de implementação
```

Só precisa de Python 3.9+, sem dependências.

## Regras do jogo

Para a comparação ser justa:

1. **Mesmo backlog.** As tasks saem do `tasks.md`, com os mesmos IDs e critérios de aceite nos dois lados.
2. **Mesmo modelo e esforço.** Combinem modelo e nível de esforço e não troquem no meio.
3. **Registre cada fase/task na sessão em que ela aconteceu.** Pode ter várias na mesma sessão (ex.: spec e depois implement): cada registro conta só o que veio depois do anterior.
4. **Tudo que gasta token conta.** No lado SDD, escrever spec, plano e quebra de tasks também é registrado (fases `spec`, `plan`, `tasks`).
5. **Registre logo ao terminar a task**, enquanto lembra quantas correções foram necessárias.
6. **Bugs descobertos depois** voltam para a task original: registre de novo com fase `fix` e o mesmo ID.
7. **Nada de métricas dentro do repo de implementação.** O Claude que implementa não deve saber que está sendo medido: nada disso vai em prompts, specs ou constituição.

## Como registrar

### Pelo chat do Claude Code (recomendado)

Instale o hook uma vez, na sua máquina, a partir da raiz deste repo:

```bash
python3 scripts/instalar_hook.py --lado sdd --repo ../share-screen-sdd      # Sergio
python3 scripts/instalar_hook.py --lado nosdd --repo ../share-screen-nosdd  # Perion
```

Ele grava em `.claude/settings.local.json` do repo de implementação, que é pessoal e não vai pro git.
Abra (ou reabra) a sessão do Claude Code nesse repo. Se o app pedir para aprovar o hook, aprove.

Ao terminar uma task, digite no próprio chat da sessão:

```
/registrar <task> <fase> <resultado> [retrabalhos] [notas]
```

```
/registrar GERAL spec ok
/registrar T01 implement ok
/registrar T02 implement ajustes 2 o seletor de tela não abria no Safari
/registrar T02 fix ok bug de áudio achado depois
```

- `fase`: `spec`, `plan`, `tasks`, `implement` ou `fix`
- `resultado`: `ok` (de primeira), `ajustes` ou `falhou`
- `retrabalhos`: quantas vezes pediu correção ao Claude (padrão 0)

O hook intercepta a mensagem **antes** de ela chegar ao Claude, então o registro não gasta tokens
e o modelo não fica sabendo. Ele mede a sessão, grava em `data/<lado>.csv`, faz commit e push
deste workspace e mostra o resumo no chat. Se o app recusar `/registrar` como comando desconhecido,
use `registrar: T01 implement ok`, que funciona igual.

### Pelo terminal

Se preferir, ou para registrar uma sessão antiga, a partir da raiz deste repo:

```bash
# pega automaticamente a sessão mais recente do Claude Code feita dentro do repo indicado
python3 scripts/log.py --lado sdd --task T01 --fase implement \
  --ultima ../share-screen-sdd \
  --resultado ok_primeira --retrabalhos 0 --notas "subiu de primeira"
```

Ou indicando a(s) sessão(ões) explicitamente (o ID aparece no nome do arquivo em `~/.claude/projects/...`):

```bash
python3 scripts/log.py --lado nosdd --task T03 --fase implement \
  --sessao 574b91c9-6aa1-4916-94bf-7f64c24da6b1 --sessao 2dfd427c-... \
  --resultado ok_com_ajustes --retrabalhos 2
```

Para só conferir os números de uma sessão sem gravar nada:

```bash
python3 scripts/tokens.py --ultima ../share-screen-sdd
```

### Campos

| Campo | Origem | Significado |
|---|---|---|
| `task` | manual | ID do `tasks.md` (ex.: `T01`) |
| `fase` | manual | `spec`, `plan`, `tasks`, `implement` ou `fix` |
| `data` | auto | início da primeira sessão (UTC) |
| `sessoes` | auto | IDs das sessões do Claude Code, separados por `;` |
| `modelo` | auto | modelo(s) usados |
| `input_tokens` | auto | tokens de entrada sem cache |
| `cache_write_tokens` | auto | tokens gravados no cache de prompt |
| `cache_read_tokens` | auto | tokens lidos do cache de prompt |
| `output_tokens` | auto | tokens de saída (inclui thinking) |
| `total_tokens` | auto | soma dos quatro acima |
| `duracao_min` | auto | tempo ativo: soma dos intervalos entre mensagens, com pausas acima de 10 min contando só 10 min. Dá para sobrescrever com `--duracao` |
| `prompts` | auto | quantas mensagens você mandou para o Claude |
| `resultado` | manual | `ok_primeira`: aceite cumprido sem correção; `ok_com_ajustes`: precisou corrigir; `falhou`: não ficou pronta |
| `retrabalhos` | manual | quantas vezes você teve que pedir correção de algo que o Claude entregou errado |
| `notas` | manual | texto livre |
| `ate` | auto | instante do registro; um próximo registro da mesma sessão só conta o que veio depois |

Subagentes contam: os tokens deles entram na soma da sessão.

## Comparativo

```bash
python3 scripts/report.py
```

Gera `reports/comparativo.md` com totais por lado, custo das fases de especificação do SDD,
assertividade e uma tabela task a task.
