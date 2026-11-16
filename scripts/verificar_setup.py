#!/usr/bin/env python3
"""Confere se a máquina está pronta para o experimento.

  python3 scripts/verificar_setup.py --lado nosdd --repo ../share-screen-nosdd
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HOOK = os.path.join(HERE, "hook_registrar.py")

falhas = 0


def ok(msg):
    print("✅ " + msg)


def aviso(msg):
    print("⚠️  " + msg)


def erro(msg, como=""):
    global falhas
    falhas += 1
    print("❌ " + msg + ("\n   → " + como if como else ""))


def run(*cmd, **kw):
    try:
        return subprocess.run(list(cmd), capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=30, **kw)
    except (OSError, subprocess.TimeoutExpired) as e:
        return subprocess.CompletedProcess(cmd, 1, "", str(e))


def _mesmo_caminho(cmd, path):
    # No Windows o instalador grava o caminho com "/", então compara ignorando o tipo de barra.
    return path.replace("\\", "/").lower() in cmd.replace("\\", "/").lower() if os.name == "nt" else path in cmd


def main():
    # No Windows a saída em pipe é cp1252, que não tem os emojis abaixo.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--lado", required=True, choices=["sdd", "nosdd"])
    p.add_argument("--repo", required=True, help="pasta do repo de implementação")
    args = p.parse_args()
    repo = os.path.realpath(args.repo)

    # Ferramentas
    if sys.version_info >= (3, 9):
        ok("Python %d.%d" % sys.version_info[:2])
    else:
        erro("Python %d.%d: precisa ser 3.9+" % sys.version_info[:2])
    if shutil.which("git"):
        ok("git instalado")
        name = run("git", "config", "user.name").stdout.strip()
        if name:
            ok("git user.name = %s" % name)
        else:
            erro("git sem user.name", 'git config --global user.name "seu-usuario"')
    else:
        erro("git não encontrado")
    if not shutil.which("gh"):
        aviso("GitHub CLI (gh) não encontrado; o push depende de você ter outro login do git configurado")
    elif run("gh", "auth", "status").returncode == 0:
        ok("gh logado")
    else:
        erro("gh não está logado", "gh auth login && gh auth setup-git")

    projects = os.environ.get("CLAUDE_PROJECTS_DIR", os.path.expanduser("~/.claude/projects"))
    if os.path.isdir(projects):
        ok("transcripts do Claude Code em %s" % projects)
    else:
        erro("não achei %s" % projects, "abra pelo menos uma sessão do Claude Code antes")

    # Workspace
    if run("git", "-C", ROOT, "ls-remote", "--heads", "origin").returncode == 0:
        ok("workspace conectado ao GitHub")
    else:
        erro("não consegui acessar o remote do workspace", "confira o login (gh auth status) e o convite de colaborador")
    if shutil.which("gh"):
        url = run("git", "-C", ROOT, "remote", "get-url", "origin").stdout.strip()
        slug = url.rstrip("/").replace(".git", "").split("github.com")[-1].lstrip(":/")
        perm = run("gh", "api", "repos/" + slug, "-q", ".permissions.push").stdout.strip()
        if perm == "true":
            ok("permissão de push no workspace (%s)" % slug)
        elif perm == "false":
            erro("sem permissão de push em %s" % slug, "peça para o Sergio te adicionar como colaborador e aceite o convite")

    # Repo de implementação
    if not os.path.isdir(os.path.join(repo, ".git")):
        erro("%s não existe ou não é um repo git" % repo, "gh repo clone Sergio0203/share-screen-%s" % args.lado)
        return fim()
    origin = run("git", "-C", repo, "remote", "get-url", "origin").stdout.strip()
    if ("share-screen-%s" % args.lado) in origin:
        ok("repo de implementação: %s" % origin)
    else:
        aviso("o remote de %s é '%s', esperava share-screen-%s" % (repo, origin, args.lado))
    if os.path.realpath(os.path.dirname(repo)) != os.path.realpath(os.path.dirname(ROOT)):
        aviso("o workspace e o repo de implementação não estão na mesma pasta pai (funciona, mas foge do SETUP)")

    if args.lado == "nosdd":
        sdd_rastros = [x for x in (".specify", "specs", ".claude/skills") if os.path.exists(os.path.join(repo, x))]
        if sdd_rastros:
            erro("o lado nosdd tem coisas de SDD: %s" % ", ".join(sdd_rastros), "remova; o lado nosdd não usa Spec Kit")
        else:
            ok("sem Spec Kit no lado nosdd")
    elif os.path.isdir(os.path.join(repo, ".specify")):
        ok("Spec Kit presente no lado sdd")
    else:
        erro("Spec Kit não encontrado no lado sdd")

    # Hook
    settings = os.path.join(repo, ".claude", "settings.local.json")
    cmds = []
    if os.path.exists(settings):
        try:
            with open(settings, encoding="utf-8") as f:
                data = json.load(f)
            for g in data.get("hooks", {}).get("UserPromptSubmit", []):
                cmds += [h.get("command", "") for h in g.get("hooks", [])]
        except ValueError:
            erro("%s não é um JSON válido" % settings)
    mine = [c for c in cmds if "hook_registrar.py" in c]
    instalar = ("python" if os.name == "nt" else "python3") + " scripts/instalar_hook.py --lado %s --repo %s" % (args.lado, args.repo)
    if not mine:
        erro("hook do /registrar não instalado", instalar)
    elif not any(_mesmo_caminho(c, HOOK) and "--lado %s" % args.lado in c for c in mine):
        erro("hook instalado aponta para outro workspace ou lado: %s" % mine[0], instalar)
    else:
        ok("hook do /registrar instalado (lado %s)" % args.lado)
        if run("git", "-C", repo, "check-ignore", "-q", settings).returncode == 0:
            ok(".claude/settings.local.json está no .gitignore")
        else:
            erro(".claude/settings.local.json não está no .gitignore",
                 "printf '.claude/settings.local.json\\n' >> %s/.gitignore" % args.repo)

        normal = run(sys.executable, HOOK, "--lado", args.lado, "--sem-push",
                     input=json.dumps({"session_id": "x", "prompt": "oi"}))
        reg = run(sys.executable, HOOK, "--lado", args.lado, "--sem-push",
                  input=json.dumps({"session_id": "x", "prompt": "/registrar"}))
        try:
            bloqueou = json.loads(reg.stdout).get("decision") == "block"
        except ValueError:
            bloqueou = False
        if normal.returncode == 0 and not normal.stdout.strip() and bloqueou:
            ok("hook responde certo (mensagem normal passa, /registrar é interceptado)")
        else:
            erro("o hook não respondeu como esperado: %s" % (reg.stderr.strip() or reg.stdout.strip()))

    return fim()


def fim():
    print()
    if falhas:
        print("%d problema(s) para resolver." % falhas)
        sys.exit(1)
    print("Tudo certo. Falta só o teste no app: abra uma sessão NOVA no repo de implementação e mande /registrar.")


if __name__ == "__main__":
    main()
