# share-screen-workspace

Este repo guarda as **métricas** de um experimento: o mesmo app de compartilhamento de tela é feito
duas vezes com o Claude Code. O Sergio faz no lado `sdd` (com Spec Kit, repo `share-screen-sdd`) e
o Perion no lado `nosdd` (sem SDD, repo `share-screen-nosdd`). Aqui não se implementa o app.

Leia o [README.md](README.md) para as regras e o [SETUP.md](SETUP.md) para a configuração.

## Quando pedirem "setup"

Siga o SETUP.md para o lado indicado. Se não souber o lado, pergunte: Sergio = `sdd`, Perion = `nosdd`.

- Execute os passos 1 a 4 e termine com `scripts/verificar_setup.py`.
- Os repos ficam lado a lado na mesma pasta pai deste workspace. Clone com `gh repo clone` (HTTPS).
- Se faltar login no `gh`, peça para a pessoa rodar `gh auth login`: você não digita credenciais.
- O passo 4 (mandar `/registrar` numa sessão nova no repo de implementação) só a pessoa pode fazer.
  Diga a ela exatamente o que fazer e o que deve aparecer.
- No lado `nosdd`, **não** instale Spec Kit nem crie specs, planos, `CLAUDE.md` ou outra documentação
  no repo de implementação: isso estragaria a comparação.

## Regras para mexer aqui

- Cada lado só escreve no próprio CSV (`data/sdd.csv` ou `data/nosdd.csv`). Nunca edite o do outro lado.
- Não edite à mão linhas já registradas, a não ser que a pessoa peça uma correção específica.
- Para registrar pelo terminal use `scripts/log.py`. Para o comparativo, `scripts/report.py`.
- Os scripts usam só a biblioteca padrão do Python 3.9. Não adicione dependências.
- Nada sobre o experimento ou métricas deve ir para os repos de implementação.
