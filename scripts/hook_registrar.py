#!/usr/bin/env python3
"""Hook UserPromptSubmit do Claude Code: intercepta "/registrar ..." no chat da task.

A mensagem é bloqueada antes de chegar ao Claude (não gasta tokens e o modelo não fica sabendo).
O hook mede a sessão atual, grava em data/<lado>.csv e faz commit + push do workspace.
Qualquer outra mensagem passa direto, sem efeito.

Uso no chat:
  /registrar <task> <fase> <resultado> [retrabalhos] [notas...]
  /registrar T01 implement ok_primeira
  /registrar T02 implement ajustes 2 o seletor de tela não abria no Safari

Instalado por scripts/instalar_hook.py, que passa --lado.
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ALIASES = {
    "ok": "ok_primeira", "ok1": "ok_primeira", "ok_primeira": "ok_primeira", "primeira": "ok_primeira",
    "ajustes": "ok_com_ajustes", "ok_ajustes": "ok_com_ajustes", "ok_com_ajustes": "ok_com_ajustes",
    "falhou": "falhou", "falha": "falhou",
}
USO = ("Uso: /registrar <task> <fase> <resultado> [retrabalhos] [notas]\n"
       "  fase: spec | plan | tasks | implement | fix\n"
       "  resultado: ok (de primeira) | ajustes | falhou\n"
       "  ex.: /registrar T01 implement ajustes 2 faltou tratar permissão negada")


def block(msg):
    print(json.dumps({"decision": "block", "reason": msg}, ensure_ascii=False))
    sys.exit(0)


def parse(prompt):
    body = prompt.strip()
    for prefix in ("/registrar", "registrar:"):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break
    parts = body.split()
    if len(parts) < 3:
        raise ValueError("faltam argumentos.")
    task, fase, res = parts[0], parts[1].lower(), parts[2].lower()
    if res not in ALIASES:
        raise ValueError("resultado '%s' não reconhecido." % res)
    rest = parts[3:]
    retrab = 0
    if rest and rest[0].isdigit():
        retrab = int(rest[0])
        rest = rest[1:]
    return task, fase, ALIASES[res], retrab, " ".join(rest)


def git(root, *args):
    return subprocess.run(["git", "-C", root] + list(args), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=40)


def _utf8_stdio():
    # O Claude Code troca JSON em UTF-8 com o hook. No Windows o padrão do Python em pipe é cp1252,
    # o que corrompe acentos nas notas e quebra o registro com letras como "Á".
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def main():
    _utf8_stdio()
    ap = argparse.ArgumentParser()
    ap.add_argument("--lado", required=True)
    ap.add_argument("--sem-push", action="store_true")
    opts = ap.parse_args()

    try:
        event = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    prompt = (event.get("prompt") or "").lstrip()
    if not prompt.startswith(("/registrar", "registrar:")):
        sys.exit(0)  # mensagem normal: segue para o Claude

    import log  # só importa quando é registro, para não atrasar as outras mensagens

    try:
        task, fase, resultado, retrab, notas = parse(prompt)
    except ValueError as e:
        block("Registro não feito: %s\n\n%s" % (e, USO))

    root = log.ROOT
    avisos = []
    if not opts.sem_push:
        r = git(root, "pull", "--rebase", "--autostash", "-q")
        if r.returncode != 0:
            avisos.append("git pull falhou, registrando só localmente: " + (r.stderr.strip() or r.stdout.strip()))

    try:
        row = log.registrar(opts.lado, task, fase, [event["session_id"]], resultado, retrab, notas)
    except (ValueError, SystemExit, KeyError) as e:
        block("Registro não feito: %s\n\n%s" % (e, USO))

    if not opts.sem_push and not avisos:
        rel = os.path.relpath(log.csv_path(opts.lado), root)
        msg = "%s: %s %s (%s)" % (opts.lado, row["task"], fase, resultado)
        for args in (("add", rel), ("commit", "-q", "-m", msg), ("push", "-q")):
            r = git(root, *args)
            if r.returncode != 0:
                avisos.append("git %s falhou: %s" % (args[0], r.stderr.strip() or r.stdout.strip()))
                break

    linhas = [
        "Registrado %s · %s · %s · %s" % (opts.lado, row["task"], fase, resultado),
        "tokens: %s total (%s saída) · tempo ativo: %s min · prompts: %s · retrabalhos: %s"
        % ("{:,}".format(int(row["total_tokens"])).replace(",", "."),
           "{:,}".format(int(row["output_tokens"])).replace(",", "."),
           row["duracao_min"], row["prompts"], retrab),
    ]
    if notas:
        linhas.append("notas: " + notas)
    linhas.append("workspace " + ("enviado ao GitHub" if not (opts.sem_push or avisos) else "atualizado localmente"))
    linhas += ["⚠ " + a for a in avisos]
    block("\n".join(linhas))


if __name__ == "__main__":
    main()
