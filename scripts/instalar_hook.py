#!/usr/bin/env python3
"""Instala o hook do /registrar no repo de implementação (em .claude/settings.local.json).

O settings.local.json é pessoal (não vai pro git) e guarda o caminho absoluto deste workspace,
então cada um roda isso na própria máquina:

  python3 scripts/instalar_hook.py --lado sdd   --repo ../share-screen-sdd
  python3 scripts/instalar_hook.py --lado nosdd --repo ../share-screen-nosdd

Rodar de novo é seguro: substitui a instalação anterior. Use --remover para desinstalar.
"""
import argparse
import json
import os
import shlex
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(HERE, "hook_registrar.py")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--lado", required=True, choices=["sdd", "nosdd"])
    p.add_argument("--repo", required=True, help="pasta do repo de implementação")
    p.add_argument("--remover", action="store_true")
    args = p.parse_args()

    repo = os.path.realpath(args.repo)
    if not os.path.isdir(os.path.join(repo, ".git")):
        sys.exit("%s não parece um repo git" % repo)

    path = os.path.join(repo, ".claude", "settings.local.json")
    settings = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            settings = json.load(f)

    hooks = settings.setdefault("hooks", {})
    groups = [g for g in hooks.get("UserPromptSubmit", [])
              if not any("hook_registrar.py" in h.get("command", "") for h in g.get("hooks", []))]
    if not args.remover:
        cmd = "python3 %s --lado %s" % (shlex.quote(HOOK), args.lado)
        groups.append({"hooks": [{"type": "command", "command": cmd, "timeout": 60}]})
    if groups:
        hooks["UserPromptSubmit"] = groups
    else:
        hooks.pop("UserPromptSubmit", None)
    if not hooks:
        settings.pop("hooks")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(("Hook removido de " if args.remover else "Hook instalado em ") + path)
    ignored = subprocess.run(["git", "-C", repo, "check-ignore", "-q", path]).returncode == 0
    if not ignored:
        print("⚠ %s não está no .gitignore do repo. Adicione '.claude/settings.local.json' para não commitar"
              " o caminho da sua máquina." % os.path.relpath(path, repo))
    if not args.remover:
        print("Abra (ou reabra) a sessão do Claude Code em %s e use /registrar ao terminar cada task." % repo)


if __name__ == "__main__":
    main()
