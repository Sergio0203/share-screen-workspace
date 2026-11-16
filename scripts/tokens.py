#!/usr/bin/env python3
"""Soma tokens, tempo ativo e prompts de sessões do Claude Code a partir dos transcripts locais.

Os transcripts ficam em ~/.claude/projects/<projeto>/<sessao>.jsonl e os subagentes em
~/.claude/projects/<projeto>/<sessao>/subagents/*.jsonl. Use CLAUDE_PROJECTS_DIR para apontar
para outro lugar.

Uso:
  python3 scripts/tokens.py --sessao <id> [--sessao <id> ...]
  python3 scripts/tokens.py --ultima ../share-screen-sdd
"""
import argparse
import glob
import json
import os
import sys
from datetime import datetime

PAUSA_MAX_MIN = 10  # intervalos maiores que isso entre mensagens não contam como tempo ativo


def projects_dir():
    return os.environ.get("CLAUDE_PROJECTS_DIR", os.path.expanduser("~/.claude/projects"))


def _read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _ts(rec):
    t = rec.get("timestamp")
    if not t:
        return None
    try:
        return datetime.fromisoformat(t.replace("Z", "+00:00"))
    except ValueError:
        return None


def session_files(session_id):
    base = projects_dir()
    main = glob.glob(os.path.join(base, "*", session_id + ".jsonl"))
    if not main:
        raise SystemExit("Sessão não encontrada: %s (procurei em %s)" % (session_id, base))
    subs = glob.glob(os.path.join(base, "*", session_id, "subagents", "*.jsonl"))
    return main[0], subs


def _session_cwd(path):
    for i, rec in enumerate(_read_jsonl(path)):
        if rec.get("cwd"):
            return rec["cwd"]
        if i > 50:
            break
    return None


def latest_session_in(repo_path):
    """ID da sessão mais recente cujo cwd está dentro de repo_path (inclui worktrees dentro dele)."""
    root = os.path.realpath(repo_path)
    best = None
    for path in glob.glob(os.path.join(projects_dir(), "*", "*.jsonl")):
        cwd = _session_cwd(path)
        if not cwd:
            continue
        cwd = os.path.realpath(cwd)
        if cwd != root and not cwd.startswith(root + os.sep):
            continue
        mtime = os.path.getmtime(path)
        if best is None or mtime > best[0]:
            best = (mtime, path)
    if best is None:
        raise SystemExit("Nenhuma sessão do Claude Code encontrada dentro de %s" % root)
    return os.path.splitext(os.path.basename(best[1]))[0]


def _is_human_prompt(rec):
    if rec.get("type") != "user" or rec.get("isSidechain") or rec.get("isMeta"):
        return False
    content = (rec.get("message") or {}).get("content")
    if isinstance(content, str):
        text = content.lstrip()
        return not text.startswith(("<command-", "<local-command")) and not is_registro(text)
    if isinstance(content, list):
        kinds = {c.get("type") for c in content if isinstance(c, dict)}
        if "tool_result" in kinds or not kinds & {"text", "image"}:
            return False
        texts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
        return not (texts and is_registro(texts[0].lstrip()))
    return False


def is_registro(text):
    """Mensagens /registrar são interceptadas pelo hook e não contam como prompt."""
    return text.startswith(("/registrar", "registrar:"))


def _active_minutes(timestamps):
    timestamps = sorted(timestamps)
    total = 0.0
    for a, b in zip(timestamps, timestamps[1:]):
        gap = (b - a).total_seconds() / 60
        total += min(gap, PAUSA_MAX_MIN)
    return total


def summarize(session_ids, since=None):
    """Soma as sessões. `since` = {session_id: datetime}: ignora o que veio até esse instante
    (usado para não contar de novo o que já foi registrado em outra linha)."""
    since = since or {}
    seen = set()
    totals = {"input_tokens": 0, "cache_write_tokens": 0, "cache_read_tokens": 0, "output_tokens": 0}
    models = set()
    prompts = 0
    minutes = 0.0
    start = None

    for sid in session_ids:
        main, subs = session_files(sid)
        cutoff = since.get(sid)
        stamps = []
        for path in [main] + subs:
            is_main = path == main
            for rec in _read_jsonl(path):
                t = _ts(rec)
                if cutoff and (t is None or t <= cutoff):
                    continue
                if is_main and t:
                    stamps.append(t)
                if is_main and _is_human_prompt(rec):
                    prompts += 1
                if rec.get("type") != "assistant":
                    continue
                msg = rec.get("message") or {}
                usage = msg.get("usage")
                key = msg.get("id") or rec.get("requestId") or rec.get("uuid")
                if not usage or key in seen:
                    continue
                seen.add(key)
                totals["input_tokens"] += usage.get("input_tokens") or 0
                totals["cache_write_tokens"] += usage.get("cache_creation_input_tokens") or 0
                totals["cache_read_tokens"] += usage.get("cache_read_input_tokens") or 0
                totals["output_tokens"] += usage.get("output_tokens") or 0
                if msg.get("model") and msg["model"] != "<synthetic>":
                    models.add(msg["model"])
        if stamps:
            minutes += _active_minutes(stamps)
            first = min(stamps)
            start = first if start is None or first < start else start

    totals["total_tokens"] = sum(totals.values())
    return dict(
        totals,
        sessoes=";".join(session_ids),
        modelo=";".join(sorted(models)),
        duracao_min=round(minutes, 1),
        prompts=prompts,
        data=start.strftime("%Y-%m-%d %H:%M") if start else "",
    )


def add_session_args(parser):
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--sessao", action="append", help="ID da sessão (pode repetir)")
    g.add_argument("--ultima", metavar="REPO", help="usa a sessão mais recente feita dentro deste repo")


def resolve_sessions(args):
    return args.sessao if args.sessao else [latest_session_in(args.ultima)]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_session_args(p)
    args = p.parse_args()
    json.dump(summarize(resolve_sessions(args)), sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
