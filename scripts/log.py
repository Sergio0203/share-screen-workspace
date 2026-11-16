#!/usr/bin/env python3
"""Registra uma task concluída em data/<lado>.csv, com tokens e tempo tirados do transcript.

Exemplo:
  python3 scripts/log.py --lado sdd --task T01 --fase implement --ultima ../share-screen-sdd \\
      --resultado ok_primeira --retrabalhos 0 --notas "subiu de primeira"
"""
import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tokens  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIELDS = [
    "lado", "task", "fase", "data", "sessoes", "modelo",
    "input_tokens", "cache_write_tokens", "cache_read_tokens", "output_tokens", "total_tokens",
    "duracao_min", "prompts", "resultado", "retrabalhos", "notas",
]
FASES = ["spec", "plan", "tasks", "implement", "fix"]
RESULTADOS = ["ok_primeira", "ok_com_ajustes", "falhou"]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--lado", required=True, choices=["sdd", "nosdd"])
    p.add_argument("--task", required=True, help="ID do tasks.md, ex.: T01")
    p.add_argument("--fase", required=True, choices=FASES)
    tokens.add_session_args(p)
    p.add_argument("--resultado", required=True, choices=RESULTADOS)
    p.add_argument("--retrabalhos", type=int, default=0, help="pedidos de correção feitos ao Claude")
    p.add_argument("--duracao", type=float, help="sobrescreve o tempo ativo calculado (minutos)")
    p.add_argument("--notas", default="")
    p.add_argument("--dry-run", action="store_true", help="mostra a linha sem gravar")
    args = p.parse_args()

    session_ids = tokens.resolve_sessions(args)
    s = tokens.summarize(session_ids)
    if args.duracao is not None:
        s["duracao_min"] = args.duracao

    row = dict(s, lado=args.lado, task=args.task.upper(), fase=args.fase,
               resultado=args.resultado, retrabalhos=args.retrabalhos, notas=args.notas)
    row = {k: row.get(k, "") for k in FIELDS}

    for k in FIELDS:
        print("%-19s %s" % (k, row[k]))
    if args.dry_run:
        print("\n(dry-run: nada gravado)")
        return

    path = os.path.join(ROOT, "data", args.lado + ".csv")
    new = not os.path.exists(path) or os.path.getsize(path) == 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
    print("\nGravado em %s" % os.path.relpath(path, os.getcwd()))


if __name__ == "__main__":
    main()
