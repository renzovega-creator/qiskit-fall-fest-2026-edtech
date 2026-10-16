"""Muestra dónde se atascan los alumnos, a partir de la base D1 de las cuentas.

    uv run python tools/dashboard.py --database-id <uuid> [--since AAAA-MM-DD] [--until AAAA-MM-DD]
    uv run python tools/dashboard.py --local [--persist-to DIR]
    uv run python tools/dashboard.py --json ...

Lee con `wrangler d1 execute` (la que instala runner/worker), sin escribir nada. Por defecto lee la
base remota, que necesita sesión de Cloudflare y el uuid de la base (`--database-id` o la variable
QG_D1_ID). Con `--local` lee la copia local de `wrangler dev`, o la de `--persist-to`.

El periodo va de `--since` a `--until`, ambos días UTC incluidos. Por defecto, los últimos 30 días.
Cuenta, en ese periodo:
  - los usuarios nuevos, los usuarios con algún intento y los intentos (con y sin cuenta);
  - las lecciones terminadas, por lección: solo cuentas;
  - los ejercicios con más comprobaciones fallidas y los casos que más fallan. Una comprobación
    fallida es un intento `check` que no acabó en `pass`; cuenta también sin cuenta;
  - los ejercicios aprobados con más pistas abiertas: solo cuentas, una vez por alumno.
"""
import argparse
import datetime
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKER = ROOT / "runner" / "worker"
DAY = 86400
DEFAULT_DAYS = 30

# {S} y {E} son segundos Unix. {E} queda excluido. {SD} y {ED} son días desde
# la época. {ED} queda excluido. {N} es el tope de filas.
QUERIES = {
    "summary": """
        SELECT
          (SELECT COUNT(*) FROM users WHERE created_day >= {SD} AND created_day < {ED}) AS new_users,
          (SELECT COUNT(DISTINCT user_id) FROM attempts WHERE at >= {S} AND at < {E}) AS active_users,
          (SELECT COUNT(*) FROM attempts WHERE at >= {S} AND at < {E}) AS attempts,
          (SELECT COUNT(*) FROM attempts WHERE at >= {S} AND at < {E} AND user_id IS NULL)
            AS anonymous_attempts""",
    "completions": """
        SELECT lesson, COUNT(*) AS completions
        FROM lesson_done WHERE done_at >= {S} AND done_at < {E}
        GROUP BY lesson ORDER BY completions DESC, lesson""",
    "failed_checks": """
        SELECT exercise, COUNT(*) AS failed_checks, COUNT(DISTINCT user_id) AS users,
               SUM(user_id IS NULL) AS anonymous
        FROM attempts
        WHERE mode = 'check' AND outcome <> 'pass' AND at >= {S} AND at < {E}
        GROUP BY exercise ORDER BY failed_checks DESC, exercise LIMIT {N}""",
    "failed_cases": """
        SELECT a.exercise, j.value AS "case", COUNT(*) AS failures
        FROM attempts a, json_each(a.failed) j
        WHERE a.mode = 'check' AND a.at >= {S} AND a.at < {E}
        GROUP BY a.exercise, j.value ORDER BY failures DESC, a.exercise, j.value LIMIT {N}""",
    "hints_before_pass": """
        SELECT exercise, COUNT(*) AS passed_by, SUM(hints) AS hints,
               ROUND(AVG(hints), 2) AS hints_per_learner
        FROM exercise_state
        WHERE passed = 1 AND updated_at >= {S} * 1000 AND updated_at < {E} * 1000
        GROUP BY exercise HAVING SUM(hints) > 0
        ORDER BY hints DESC, exercise LIMIT {N}""",
}

# Título y columnas de cada sección en el texto.
SECTIONS = {
    "completions": ("Lecciones terminadas", [("lesson", "lección"), ("completions", "terminadas")]),
    "failed_checks": (
        "Ejercicios con más comprobaciones fallidas",
        [
            ("exercise", "ejercicio"),
            ("failed_checks", "fallidas"),
            ("users", "con cuenta"),
            ("anonymous", "anónimas"),
        ],
    ),
    "failed_cases": (
        "Casos que más fallan",
        [("exercise", "ejercicio"), ("case", "caso"), ("failures", "fallos")],
    ),
    "hints_before_pass": (
        "Ejercicios aprobados con más pistas abiertas",
        [
            ("exercise", "ejercicio"),
            ("passed_by", "aprobaron"),
            ("hints", "pistas"),
            ("hints_per_learner", "por alumno"),
        ],
    ),
}


def day_start(text):
    """Devuelve el inicio UTC de un día con formato AAAA-MM-DD."""
    try:
        day = datetime.datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        raise SystemExit(f"error: «{text}» no es una fecha AAAA-MM-DD")
    return int(day.replace(tzinfo=datetime.timezone.utc).timestamp())


def period(since, until, today):
    """Devuelve el intervalo Unix que incluye todo `until`."""
    end = (day_start(until) if until else day_start(today)) + DAY
    start = day_start(since) if since else end - DEFAULT_DAYS * DAY
    if start >= end:
        raise SystemExit("error: --since debe ser anterior o igual a --until")
    return start, end


def wrangler_json(args):
    """Ejecuta Wrangler con una configuración temporal y devuelve su JSON."""
    # Wrangler no lee cloudflare.config.ts. La configuración temporal declara la base.
    # El id solo importa en remoto.
    config = {
        "name": "qg-dashboard",
        "compatibility_date": "2026-10-01",
        "d1_databases": [
            {
                "binding": "DB",
                "database_name": args.database,
                "database_id": args.database_id or "00000000-0000-0000-0000-000000000000",
            }
        ],
    }
    sql = ";\n".join(" ".join(q.format(**args.bounds).split()) for q in QUERIES.values())
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "wrangler.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        cmd = ["bunx", "wrangler", "d1", "execute", args.database, "--config", str(path), "--json"]
        if args.local:
            persist = Path(args.persist_to or WORKER / ".wrangler" / "state").resolve()
            cmd += ["--local", "--persist-to", str(persist)]
        else:
            cmd += ["--remote"]
        cmd += ["--command", sql]
        run = subprocess.run(cmd, cwd=WORKER, capture_output=True, text=True)
    if run.returncode != 0:
        sys.stderr.write(run.stdout + run.stderr)
        raise SystemExit(f"error: wrangler terminó con código {run.returncode}")
    return json.loads(run.stdout)


def collect(args):
    """Convierte las respuestas de Wrangler en el informe."""
    answers = wrangler_json(args)
    if len(answers) != len(QUERIES):
        raise SystemExit(f"error: wrangler devolvió {len(answers)} respuestas de {len(QUERIES)}")
    rows = {}
    for name, answer in zip(QUERIES, answers):
        if not answer.get("success", False):
            raise SystemExit(f"error: la consulta {name} falló: {answer}")
        rows[name] = answer["results"]
    day = lambda seconds: datetime.datetime.fromtimestamp(seconds, datetime.timezone.utc).date()
    start, end = args.bounds["S"], args.bounds["E"]
    return {
        "period": {"since": day(start).isoformat(), "until": day(end - DAY).isoformat()},
        "summary": rows.pop("summary")[0],
        **rows,
    }


def table(rows, columns):
    """Devuelve líneas alineadas con texto a la izquierda y números a la derecha."""
    cells = [[str(row[key]) for key, _ in columns] for row in rows]
    heads = [head for _, head in columns]
    widths = [max(len(c[i]) for c in [heads, *cells]) for i in range(len(columns))]
    numeric = [all(isinstance(row[key], (int, float)) for row in rows) for key, _ in columns]

    def line(values):
        parts = [v.rjust(w) if n else v.ljust(w) for v, w, n in zip(values, widths, numeric)]
        return ("  ".join(parts)).rstrip()

    return [line(heads), *map(line, cells)]


def render(report):
    """Renderiza el informe como texto alineado."""
    period, summary = report["period"], report["summary"]
    out = [f"Periodo: {period['since']} a {period['until']} (UTC)", ""]
    labels = [
        ("new_users", "Usuarios nuevos"),
        ("active_users", "Usuarios con intentos"),
        ("attempts", "Intentos"),
        ("anonymous_attempts", "Intentos sin cuenta"),
    ]
    width = max(len(label) for _, label in labels)
    out += [f"{label.ljust(width)}  {summary[key]}" for key, label in labels]
    for key, (title, columns) in SECTIONS.items():
        out += ["", title]
        rows = report[key]
        out += table(rows, columns) if rows else ["(ninguno)"]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--since", help="primer día, AAAA-MM-DD (por defecto, 30 días hasta --until)")
    ap.add_argument("--until", help="último día incluido, AAAA-MM-DD (por defecto, hoy)")
    ap.add_argument("--limit", type=int, default=10, help="filas por sección (por defecto, 10)")
    ap.add_argument("--json", action="store_true", help="imprime JSON en lugar de texto")
    ap.add_argument("--local", action="store_true", help="lee la base local, no la remota")
    ap.add_argument("--persist-to", help="con --local, el directorio del estado local de wrangler")
    ap.add_argument("--database", default="qiskit-guides", help="el nombre de la base D1")
    ap.add_argument("--database-id", default=os.environ.get("QG_D1_ID"), help="el uuid (remoto)")
    args = ap.parse_args()
    if not args.local and not args.database_id:
        ap.error("la base remota necesita --database-id o QG_D1_ID")
    if args.limit < 1:
        ap.error("--limit debe ser positivo")

    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    start, end = period(args.since, args.until, today)
    args.bounds = {"S": start, "E": end, "SD": start // DAY, "ED": end // DAY, "N": args.limit}
    report = collect(args)
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else render(report))


if __name__ == "__main__":
    main()
