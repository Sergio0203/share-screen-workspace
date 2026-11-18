#!/usr/bin/env python3
"""Gera reports/comparativo.md a partir de data/sdd.csv e data/nosdd.csv."""
import csv
import os
from collections import OrderedDict, defaultdict
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LADOS = ["sdd", "nosdd"]
FASES_SPEC = {"spec", "plan", "tasks"}
NUM = ["input_tokens", "cache_write_tokens", "cache_read_tokens", "output_tokens",
       "total_tokens", "duracao_min", "prompts", "retrabalhos"]


def load(lado):
    path = os.path.join(ROOT, "data", lado + ".csv")
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            for k in NUM:
                try:
                    r[k] = float(r.get(k) or 0)
                except ValueError:
                    r[k] = 0.0
            rows.append(r)
    return rows


def is_extra(r):
    """Trabalho fora do backlog (task EXTRA-...): fica fora da comparação."""
    return r["task"].upper().startswith("EXTRA")


def ssum(rows, k):
    return sum(r[k] for r in rows)


def ktok(n):
    if n >= 1_000_000:
        return "%.2fM" % (n / 1_000_000)
    if n >= 1000:
        return "%.1fk" % (n / 1000)
    return "%d" % n


def hmin(m):
    m = int(round(m))
    return "%dh%02d" % (m // 60, m % 60) if m >= 60 else "%d min" % m


def pct(a, b):
    return "%.0f%%" % (100.0 * a / b) if b else "-"


def diff(sdd, nosdd):
    if not nosdd:
        return "-"
    d = 100.0 * (sdd - nosdd) / nosdd
    return "%+.0f%%" % d


def per_task(rows):
    """Por task: primeira linha de implement define o resultado 'de primeira'."""
    tasks = OrderedDict()
    for r in rows:
        t = tasks.setdefault(r["task"], {"rows": [], "resultado": "", "fixes": 0})
        t["rows"].append(r)
        if r["fase"] == "implement" and not t["resultado"]:
            t["resultado"] = r["resultado"]
        if r["fase"] == "fix":
            t["fixes"] += 1
    return tasks


def stats(rows):
    impl = [r for r in rows if r["fase"] not in FASES_SPEC]
    spec = [r for r in rows if r["fase"] in FASES_SPEC]
    tasks = {k: v for k, v in per_task(rows).items() if v["resultado"]}
    res = defaultdict(int)
    for v in tasks.values():
        res[v["resultado"]] += 1
    n = len(tasks)
    return {
        "n": n,
        "total": ssum(rows, "total_tokens"),
        "output": ssum(rows, "output_tokens"),
        "min": ssum(rows, "duracao_min"),
        "prompts": ssum(rows, "prompts"),
        "spec_total": ssum(spec, "total_tokens"),
        "spec_min": ssum(spec, "duracao_min"),
        "impl_total": ssum(impl, "total_tokens"),
        "impl_min": ssum(impl, "duracao_min"),
        "ok1": res["ok_primeira"],
        "ajustes": res["ok_com_ajustes"],
        "falhou": res["falhou"],
        "retrab": ssum(rows, "retrabalhos"),
        "fixes": sum(v["fixes"] for v in tasks.values()),
    }


def main():
    todas = {l: load(l) for l in LADOS}
    data = {l: [r for r in todas[l] if not is_extra(r)] for l in LADOS}
    extras = {l: [r for r in todas[l] if is_extra(r)] for l in LADOS}
    s = {l: stats(data[l]) for l in LADOS}
    a, b = s["sdd"], s["nosdd"]
    out = []
    w = out.append

    w("# Comparativo SDD vs. sem SDD")
    w("")
    w("_Gerado em %s a partir de `data/sdd.csv` (%d linhas) e `data/nosdd.csv` (%d linhas)._"
      % (datetime.now().strftime("%Y-%m-%d %H:%M"), len(todas["sdd"]), len(todas["nosdd"])))
    w("")
    w("## Resumo")
    w("")
    w("| Métrica | SDD | sem SDD | SDD vs. sem SDD |")
    w("|---|---:|---:|---:|")
    w("| Tasks implementadas | %d | %d | |" % (a["n"], b["n"]))
    w("| Tokens totais | %s | %s | %s |" % (ktok(a["total"]), ktok(b["total"]), diff(a["total"], b["total"])))
    w("| Tokens de saída | %s | %s | %s |" % (ktok(a["output"]), ktok(b["output"]), diff(a["output"], b["output"])))
    w("| Tempo ativo | %s | %s | %s |" % (hmin(a["min"]), hmin(b["min"]), diff(a["min"], b["min"])))
    w("| Prompts enviados | %d | %d | %s |" % (a["prompts"], b["prompts"], diff(a["prompts"], b["prompts"])))
    w("| ↳ especificação (spec/plan/tasks): tokens | %s | %s | |" % (ktok(a["spec_total"]), ktok(b["spec_total"])))
    w("| ↳ especificação: tempo | %s | %s | |" % (hmin(a["spec_min"]), hmin(b["spec_min"])))
    w("| ↳ implementação + fixes: tokens | %s | %s | %s |"
      % (ktok(a["impl_total"]), ktok(b["impl_total"]), diff(a["impl_total"], b["impl_total"])))
    w("| ↳ implementação + fixes: tempo | %s | %s | %s |"
      % (hmin(a["impl_min"]), hmin(b["impl_min"]), diff(a["impl_min"], b["impl_min"])))
    w("")
    w("## Assertividade")
    w("")
    w("| Métrica | SDD | sem SDD |")
    w("|---|---:|---:|")
    w("| OK de primeira | %d (%s) | %d (%s) |" % (a["ok1"], pct(a["ok1"], a["n"]), b["ok1"], pct(b["ok1"], b["n"])))
    w("| OK com ajustes | %d (%s) | %d (%s) |"
      % (a["ajustes"], pct(a["ajustes"], a["n"]), b["ajustes"], pct(b["ajustes"], b["n"])))
    w("| Falhou | %d (%s) | %d (%s) |"
      % (a["falhou"], pct(a["falhou"], a["n"]), b["falhou"], pct(b["falhou"], b["n"])))
    w("| Retrabalhos (total) | %d | %d |" % (a["retrab"], b["retrab"]))
    w("| Retrabalhos por task | %s | %s |"
      % ("%.1f" % (a["retrab"] / a["n"]) if a["n"] else "-", "%.1f" % (b["retrab"] / b["n"]) if b["n"] else "-"))
    w("| Fixes depois de entregue | %d | %d |" % (a["fixes"], b["fixes"]))
    w("")
    w("## Task a task")
    w("")
    w("Tokens e tempo somam todas as fases da task. Resultado = primeira implementação.")
    w("")
    w("| Task | Tokens SDD | Tokens sem SDD | Tempo SDD | Tempo sem SDD | Resultado SDD | Resultado sem SDD | Retrab. SDD | Retrab. sem SDD | Fixes SDD | Fixes sem SDD |")
    w("|---|---:|---:|---:|---:|---|---|---:|---:|---:|---:|")
    ta, tb = per_task(data["sdd"]), per_task(data["nosdd"])
    for task in sorted(set(ta) | set(tb)):
        x, y = ta.get(task), tb.get(task)

        def col(t, k, fmt):
            return fmt(ssum(t["rows"], k)) if t else "-"

        w("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            task,
            col(x, "total_tokens", ktok), col(y, "total_tokens", ktok),
            col(x, "duracao_min", hmin), col(y, "duracao_min", hmin),
            (x["resultado"] or "-") if x else "-", (y["resultado"] or "-") if y else "-",
            col(x, "retrabalhos", lambda v: "%d" % v), col(y, "retrabalhos", lambda v: "%d" % v),
            x["fixes"] if x else "-", y["fixes"] if y else "-",
        ))
    w("")

    if extras["sdd"] or extras["nosdd"]:
        w("## Extras (fora do backlog)")
        w("")
        w("Trabalho que um lado fez por conta própria. Não entra em nenhum total acima.")
        w("")
        w("| Lado | Task | Tokens | Tempo | Notas |")
        w("|---|---|---:|---:|---|")
        for lado in LADOS:
            for task, t in per_task(extras[lado]).items():
                notas = "; ".join(r["notas"] for r in t["rows"] if r.get("notas"))
                w("| %s | %s | %s | %s | %s |" % (lado, task, ktok(ssum(t["rows"], "total_tokens")),
                                               hmin(ssum(t["rows"], "duracao_min")), notas))
        w("")

    path = os.path.join(ROOT, "reports", "comparativo.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print("Gerado %s" % os.path.relpath(path, os.getcwd()))


if __name__ == "__main__":
    main()
