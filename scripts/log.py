#!/usr/bin/env python3
"""Registra uma task concluída em data/<lado>.csv, com tokens e tempo tirados do transcript.

Se a mesma sessão já tiver sido registrada antes (ex.: spec e depois implement na mesma sessão),
só conta o que aconteceu depois do registro anterior.

Exemplo:
  python3 scripts/log.py --lado sdd --task T01 --fase implement --ultima ../share-screen-sdd \\
      --resultado ok_primeira --retrabalhos 0 --notas "subiu de primeira"
"""
import argparse
import csv
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tokens  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIELDS = [
    "lado", "task", "fase", "data", "sessoes", "modelo",
    "input_tokens", "cache_write_tokens", "cache_read_tokens", "output_tokens", "total_tokens",
    "duracao_min", "prompts", "resultado", "retrabalhos", "notas", "ate",
]
LADOS = ["sdd", "nosdd"]
FASES = ["spec", "plan", "tasks", "implement", "fix"]
RESULTADOS = ["ok_primeira", "ok_com_ajustes", "falhou"]


def csv_path(lado):
    return os.path.join(ROOT, "data", lado + ".csv")


def _parse_iso(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None


def previous_cutoffs(lado, session_ids):
    """Para cada sessão, o instante do último registro que a incluiu."""
    path = csv_path(lado)
    cut = {}
    if not os.path.exists(path):
        return cut
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            ate = _parse_iso(r.get("ate") or "")
            if not ate:
                continue
            for sid in (r.get("sessoes") or "").split(";"):
                if sid in session_ids and (sid not in cut or ate > cut[sid]):
                    cut[sid] = ate
    return cut


def registrar(lado, task, fase, session_ids, resultado, retrabalhos=0, notas="", duracao=None, dry_run=False,
              ate=None):
    if lado not in LADOS:
        raise ValueError("lado inválido: %s (use %s)" % (lado, ", ".join(LADOS)))
    if fase not in FASES:
        raise ValueError("fase inválida: %s (use %s)" % (fase, ", ".join(FASES)))
    if resultado not in RESULTADOS:
        raise ValueError("resultado inválido: %s (use %s)" % (resultado, ", ".join(RESULTADOS)))

    agora = ate or datetime.now(timezone.utc)
    s = tokens.summarize(session_ids, since=previous_cutoffs(lado, session_ids), until=agora)
    if duracao is not None:
        s["duracao_min"] = duracao

    row = dict(s, lado=lado, task=task.upper(), fase=fase, resultado=resultado,
               retrabalhos=retrabalhos, notas=notas, ate=agora.isoformat(timespec="milliseconds"))
    row = {k: row.get(k, "") for k in FIELDS}
    if dry_run:
        return row

    path = csv_path(lado)
    new = not os.path.exists(path) or os.path.getsize(path) == 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
    return row


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--lado", required=True, choices=LADOS)
    p.add_argument("--task", required=True, help="ID do tasks.md, ex.: T01")
    p.add_argument("--fase", required=True, choices=FASES)
    tokens.add_session_args(p)
    p.add_argument("--resultado", required=True, choices=RESULTADOS)
    p.add_argument("--retrabalhos", type=int, default=0, help="pedidos de correção feitos ao Claude")
    p.add_argument("--duracao", type=float, help="sobrescreve o tempo ativo calculado (minutos)")
    p.add_argument("--notas", default="")
    p.add_argument("--ate", help="registra só até este instante (ISO; sem fuso = horário local), "
                                 "ex.: 2026-11-16T18:51:14. Para quem esqueceu de registrar uma fase")
    p.add_argument("--dry-run", action="store_true", help="mostra a linha sem gravar")
    args = p.parse_args()
    ate = None
    if args.ate:
        ate = datetime.fromisoformat(args.ate.replace("Z", "+00:00"))
        ate = (ate if ate.tzinfo else ate.astimezone()).astimezone(timezone.utc)

    row = registrar(args.lado, args.task, args.fase, tokens.resolve_sessions(args), args.resultado,
                    args.retrabalhos, args.notas, args.duracao, args.dry_run, ate)
    for k in FIELDS:
        print("%-19s %s" % (k, row[k]))
    print("\n(dry-run: nada gravado)" if args.dry_run else "\nGravado em %s" % os.path.relpath(csv_path(args.lado)))


if __name__ == "__main__":
    main()
