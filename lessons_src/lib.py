"""Ayudantes para escribir lecciones en Python (cadenas crudas para LaTeX y código).

Cada módulo de contenido define LESSONS: una lista de dicts creados con lesson().
build.py los escribe en site/lessons/<id>/lesson.json y genera site/course.json.
"""


def T(text, style="body", **k):
    return dict(type="text", text=text, style=style, **k)


def M(tex, **k):
    return dict(type="math", tex=tex, **k)


def L(items, **k):
    return dict(type="list", items=items, **k)


def Row(*items, **k):
    return dict(type="row", items=list(items), **k)


def Box(kind, title, *body, **k):
    return dict(type="box", kind=kind, title=title, body=list(body), **k)


def Plot(**k):
    return dict(type="plot", **k)


def Plane(**k):
    return dict(type="plane", **k)


def Code(src, lang="python", **k):
    """Código con resaltado. reveal=True oculta las líneas hasta la acción 'lines'.
    norun=True excluye un bloque de Python de tools/verify.py cuando necesita una cuenta de IBM.
    setup="…" aporta el contexto de un fragmento. tools/verify.py lo ejecuta antes del bloque y la página no lo muestra."""
    return dict(type="code", src=src.strip(chr(10)), lang=lang, **k)


def Out(src, **k):
    """Salida de consola (texto tal como lo imprime Python)."""
    return dict(type="code", src=src.strip(chr(10)), lang="out", **k)


def Sh(src, **k):
    return dict(type="code", src=src.strip(chr(10)), lang="sh", **k)


def Circ(qubits, ops, **k):
    """Diagrama de circuito. ops: dict(g='h', q=[0]), dict(g='cx', q=[0, 1]), dict(g='measure', q=[0], c=0)…"""
    return dict(type="circuit", qubits=qubits, ops=ops, **k)


def G(g, *q, **k):
    """Atajo para una operación de circuito: G('cx', 0, 1, hidden=True)."""
    return dict(g=g, q=list(q), **k)


def Hist(data, **k):
    return dict(type="hist", data=[list(d) for d in data], **k)


def Table(head, rows, **k):
    return dict(type="table", head=head, rows=rows, **k)


def Flow(steps, **k):
    return dict(type="flow", steps=[s if isinstance(s, dict) else dict(t=s) for s in steps], **k)


def Graph(nodes, edges, **k):
    return dict(type="graph", nodes=nodes, edges=edges, **k)


def A(do, id=None, at=None, t=0, **k):
    """Acción: A('show', 'eq1', at='marca', t=0.5)."""
    d = dict(do=do, **k)
    if id is not None:
        d["id"] = id
    if at is not None:
        d["at"] = at
    if t:
        d["t"] = t
    return d


def shows(*pairs):
    """shows(('marca', 'id'), ...) → acciones 'show' en esas marcas."""
    return [A("show", i, at=m) for m, i in pairs]


def beat(id, tag, say, scene, actions=(), ask=None, title=None, **k):
    b = dict(id=id, tag=list(tag), say=" ".join(say.split()), scene=scene, actions=list(actions), **k)
    if title:
        b["title"] = title
    if ask:
        b["ask"] = ask
        b.setdefault("align", "top")
    return b


def choice(prompt, options, right, why, wrong=None, hint=None):
    d = dict(kind="choice", prompt=prompt, options=options, right=right, why=why)
    if wrong:
        d["wrong"] = wrong
    if hint:
        d["hint"] = hint
    return d


def numeric(prompt, answer, why, tol=0.01, hint=None, solution=None, unit=None):
    d = dict(kind="numeric", prompt=prompt, answer=answer, why=why, tol=tol)
    for key, v in (("hint", hint), ("solution", solution), ("unit", unit)):
        if v:
            d[key] = v
    return d


def reveal(prompt, solution, button=None):
    d = dict(kind="reveal", prompt=prompt, solution=solution)
    if button:
        d["button"] = button
    return d


def predict(prompt, options, after):
    """Apuesta antes de ver el resultado: cualquier opción vale; no cuenta en la puntuación.
    after: lo que se dice al elegir (el resultado se revela en el paso siguiente)."""
    return dict(kind="predict", prompt=prompt, options=options, after=after)


def reflect(*prompts):
    """Preguntas abiertas con cuadro de texto; las respuestas se guardan en el navegador."""
    return dict(kind="reflect", prompts=list(prompts))


def Mission(notebook, tasks, **k):
    """Tarjeta «Tu turno»: tasks = [(nivel, texto)] con nivel 1 (reproducir), 2 (modificar) o 3 (crear)."""
    return dict(type="mission", notebook=notebook, tasks=[dict(level=l, text=t) for l, t in tasks], **k)


def Exercise(path, prompt, level, needs="qiskit", hints=(), **k):
    """Declara un ejercicio y valida sus opciones antes de publicarlo."""
    if level not in (1, 2, 3):
        raise ValueError(f"{path}: level debe ser 1, 2 o 3, no {level!r}")
    if needs not in ("qiskit", "aer"):
        raise ValueError(f"{path}: needs debe ser 'qiskit' o 'aer', no {needs!r}")
    return dict(type="exercise", exercise=path, prompt=prompt, level=level,
                needs=needs, hints=list(hints), **k)


def lesson(id, title, summary, goals, beats, sources=(), practice=()):
    """sources: nombres de las guías originales de Qiskit/documentation
    (docs/guides/<nombre>) que cubre la lección.
    practice: ejercicios para hacer en tu propio entorno al terminar."""
    return dict(id=id, part="", section="", title=title, summary=summary, goals=list(goals),
                beats=beats, sources=list(sources), practice=list(practice), next=None,
                voice="es-PE-AlexNeural", rate="-4%")
