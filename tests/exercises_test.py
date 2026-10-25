"""Pruebas del formato de ejercicios, del corrector y de lo que build.py publica.

    uv run pytest tests/exercises_test.py

Cada ejercicio de exercises/ se corrige con su solución (pasa) y con una solución equivocada (falla
con un mensaje útil). No necesitan red.
"""

import ast
import collections
import contextlib
import functools
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
import types
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pytest

resource = pytest.importorskip("resource", reason="El corrector requiere Linux o macOS")

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "lessons_src")]
os.environ.setdefault("MPLBACKEND", "Agg")

import build  # noqa: E402

from qgcheck import grade, learner, spec  # noqa: E402


def load_tool(name: str, filename: str) -> types.ModuleType:
    tool = importlib.util.spec_from_file_location(name, ROOT / "tools" / filename)
    assert tool and tool.loader
    module = importlib.util.module_from_spec(tool)
    tool.loader.exec_module(module)
    return module


exercises_tool = load_tool("exercises_tool", "exercises.py")

REAL = spec.all_ids()


def broken(exercise_id: str, old: str, new: str) -> str:
    """Devuelve la solución de referencia con un cambio incorrecto."""
    code = (spec.folder(exercise_id) / "solution.py").read_text(encoding="utf-8")
    assert old in code, (exercise_id, old)
    return code.replace(old, new)


# (ejercicio, código equivocado, texto esperado en algún mensaje de fallo)
WRONG = [
    (
        "q1-montecarlo/estimar-p",
        broken("q1-montecarlo/estimar-p", 'return conteos.get("1", 0) / shots', "return 0.5"),
        "Con θ",
    ),
    ("q2-kernel/kernel-fidelidad", "def kernel(x, y):\n    return 0.0\n", "kernel("),
]


def read(exercise_id: str, name: str) -> str:
    return (spec.folder(exercise_id) / name).read_text(encoding="utf-8")


def failed(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [t for t in result["tests"] if not t["passed"]]


# Parte 3: (ejercicio, nombre del archivo en tests/mutants/<ejercicio>/, texto esperado en algún mensaje).


# Códigos equivocados que hacen fallar los casos ocultos: (ejercicio, código). Cada mensaje de un
# caso oculto que falla se compara con la solución de referencia en test_hidden_messages_*.
MUTANTS = [(eid, code) for eid, code, _ in WRONG]


# El corredor da a un trabajo 10 s con 1/4 de vCPU, unas 4 veces el tiempo de un núcleo, así que un
# trabajo que pase de 2,5 s de CPU ya no cabe. La solución más lenta (fidelidad) usa 1,9 s.
CPU_BUDGET_S = 2.5


@pytest.mark.parametrize("exercise_id", REAL)
def test_solution_passes_within_the_cpu_budget(exercise_id: str) -> None:
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    result = grade(exercise_id, read(exercise_id, "solution.py"), timeout=60)
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    assert result["passed"], result
    assert result["tests"] and all(t["passed"] and t["message"] is None for t in result["tests"])
    cpu = after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime
    assert cpu <= CPU_BUDGET_S, f"La solución usó {cpu:.1f} s de CPU; el tope es {CPU_BUDGET_S} s."


@pytest.mark.parametrize("exercise_id", REAL)
def test_starter_fails(exercise_id: str) -> None:
    result = grade(exercise_id, read(exercise_id, "starter.py"))
    assert result["error"] is None and not result["passed"] and failed(result)


@pytest.mark.parametrize(
    "exercise_id,code,expected", WRONG, ids=[f"{w[0]}#{k}" for k, w in enumerate(WRONG)]
)
def test_wrong_solution_fails_with_message(exercise_id: str, code: str, expected: str) -> None:
    result = grade(exercise_id, code)
    assert not result["passed"]
    assert any(expected in t["message"] for t in failed(result)), [
        t["message"] for t in failed(result)
    ]


def test_wrong_solutions_cover_every_exercise() -> None:
    assert {w[0] for w in WRONG} == set(REAL)


def learner_names(exercise_id: str) -> set[str]:
    """Nombres que el código inicial define: las variables y funciones del alumno."""
    names: set[str] = set()
    for node in ast.walk(ast.parse(read(exercise_id, "starter.py"))):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names |= {t.id for t in node.targets if isinstance(t, ast.Name)}
    return names


def names_its_input(exercise_id: str, message: str) -> bool:
    """Un mensaje nombra su entrada con `n = 7` o con el nombre del alumno entre comillas invertidas."""
    return bool(re.search(r"\b\w+ = \S", message)) or any(
        f"`{name}" in message for name in learner_names(exercise_id)
    )


def graded_attempts(exercise_id: str) -> list[str]:
    """El código inicial y cada código equivocado de WRONG para este ejercicio."""
    return [
        read(exercise_id, "starter.py"),
        *(code for eid, code, *_ in WRONG if eid == exercise_id),
    ]


@pytest.mark.parametrize("exercise_id", REAL)
def test_graded_hidden_messages_name_their_input(exercise_id: str) -> None:
    """Lo que `grade` devuelve para un caso oculto que falla dice con qué entrada falló."""
    for code in graded_attempts(exercise_id):
        for test in failed(grade(exercise_id, code)):
            if not test["visible"]:
                assert names_its_input(exercise_id, test["message"]), (
                    f"{test['name']} no nombra su entrada: {test['message']}"
                )


# Un `assert` de un caso mira el código del alumno a través de estas expresiones, y lleva escritos
# los valores esperados como literales.
OBSERVED = (
    ast.Name,
    ast.Attribute,
    ast.Subscript,
    ast.Call,
    ast.BinOp,
    ast.UnaryOp,
    ast.Compare,
    ast.BoolOp,
    ast.ListComp,
    ast.DictComp,
    ast.List,
    ast.Tuple,
    ast.Dict,
    ast.Set,
)


def plain(value: Any) -> str:
    """repr de un valor, con los de numpy convertidos a los de Python, como los imprime un mensaje."""
    if isinstance(value, (np.ndarray, np.generic)):
        value = value.tolist()
    return repr(value)


def forms(value: Any) -> list[str]:
    """Cómo puede aparecer un valor en un mensaje: su repr y, si es un texto, el texto mismo."""
    return [plain(value)] + ([value] if isinstance(value, str) and len(value) > 1 else [])


def informative(value: Any) -> bool:
    """Un valor que un mensaje puede mostrar: ni módulos ni funciones ni objetos con repr de dirección."""
    if isinstance(value, (bool, np.bool_, types.ModuleType, type)) or callable(value):
        return False
    return " at 0x" not in repr(value)


def expressions(tree: ast.AST) -> list[ast.expr]:
    """Las expresiones observables de `tree`. De un literal cuenta la colección entera, no cada número."""
    found: list[ast.expr] = []
    inside: set[int] = set()
    for node in ast.walk(tree):
        if id(node) in inside:
            continue
        if isinstance(node, (ast.List, ast.Tuple, ast.Dict, ast.Set, ast.UnaryOp)):
            inside |= {id(n) for n in ast.walk(node) if isinstance(n, ast.Constant)}
        number = (
            isinstance(node, ast.Constant)
            and isinstance(node.value, (int, float))
            and not isinstance(node.value, bool)
        )
        if isinstance(node, ast.expr) and (number or isinstance(node, OBSERVED)):
            found.append(node)
    return found


def names_in(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


class Site:
    """El assert que falló: sus expresiones y de qué depende cada una.

    kind[texto] es "learner" si la expresión depende del código del alumno, "input" si es una variable
    de entrada del caso (la n de un bucle) y "fixed" si no depende de ninguno: un valor esperado.
    """

    def __init__(self, tree: ast.Module, lineno: int) -> None:
        asserts = [
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.Assert) and n.lineno <= lineno <= (n.end_lineno or n.lineno)
        ]
        node = max(asserts, key=lambda n: n.lineno)
        scope = min(
            (
                n
                for n in ast.walk(tree)
                if isinstance(n, ast.FunctionDef)
                and n.lineno <= node.lineno <= (n.end_lineno or n.lineno)
            ),
            key=lambda n: (n.end_lineno or n.lineno) - n.lineno,
        )
        tainted, inputs = self.dependencies(tree, scope)
        self.sources = collections.defaultdict(list)
        for n in ast.walk(scope):
            if isinstance(n, ast.Assign):
                for target in n.targets:
                    for x in ast.walk(target):
                        if isinstance(x, ast.Name):
                            self.sources[x.id].append(n.value)
        self.first = node.lineno
        self.test = {ast.unparse(n): n for n in expressions(node.test)}
        self.message = {ast.unparse(n): n for n in expressions(node.msg)} if node.msg else {}
        self.interpolated = {
            ast.unparse(n.value)
            for n in ast.walk(node.msg or node.test)
            if isinstance(n, ast.FormattedValue)
        }
        self.nodes = [*self.test.values(), *self.message.values()]
        # Lo que el check le pasa al código del alumno es su entrada, aunque sea un literal o una variable.
        given = [
            a
            for n in ast.walk(scope)
            if isinstance(n, ast.Call) and names_in(n.func) & tainted
            for a in (*n.args, *(k.value for k in n.keywords))
        ]
        given_names = {name for a in given for name in names_in(a)} | inputs
        given_texts = {ast.unparse(a) for a in given}
        self.derived = tainted - {"learner", *(a.arg for a in scope.args.args)}
        self.kind = {}
        for n in self.nodes:
            base = n
            while isinstance(base, (ast.Attribute, ast.Subscript)):
                base = base.value
            if ast.unparse(n) in given_texts or (
                isinstance(base, ast.Name) and base.id in given_names - tainted
            ):
                self.kind[ast.unparse(n)] = "input"
            else:
                self.kind[ast.unparse(n)] = "learner" if names_in(n) & tainted else "fixed"

    def parts(self, node: ast.AST, seen: tuple[str, ...] = ()) -> set[str]:
        """Textos de lo que la expresión toma del código del alumno, también a través de las variables que usa."""
        found: set[str] = set()
        for n in ast.walk(node):
            if (isinstance(n, ast.Name) and n.id in self.derived) or (
                isinstance(n, (ast.Call, ast.Attribute)) and "learner" in names_in(n)
            ):
                found.add(ast.unparse(n))
            if isinstance(n, ast.Name) and n.id not in seen:
                for source in self.sources[n.id]:
                    found |= self.parts(source, (*seen, n.id))
        return found

    @staticmethod
    def dependencies(tree: ast.Module, scope: ast.FunctionDef) -> tuple[set[str], set[str]]:
        """(nombres que dependen del alumno, nombres de entrada).

        Dependen del alumno `learner`, las funciones del check que lo usan, los parámetros y lo que se
        asigna desde ellos. Son entrada las variables de un bucle sobre datos fijos.
        """
        functions = [f for f in tree.body if isinstance(f, ast.FunctionDef)]
        tainted = {"learner", *(a.arg for a in scope.args.args)}
        while True:
            using = {f.name for f in functions if names_in(f) & tainted}
            if using <= tainted:
                break
            tainted |= using
        inputs: set[str] = set()
        changed = True
        while changed:
            changed = False
            for n in ast.walk(scope):
                if isinstance(n, ast.Assign):
                    source, targets = n.value, n.targets
                elif (
                    isinstance(n, (ast.AugAssign, ast.AnnAssign, ast.NamedExpr))
                    and n.value is not None
                ):
                    source, targets = n.value, [n.target]
                elif isinstance(n, (ast.For, ast.comprehension)):
                    source, targets = n.iter, [n.target]
                else:
                    continue
                dependent = bool(names_in(source) & tainted)
                for name in (x.id for t in targets for x in ast.walk(t) if isinstance(x, ast.Name)):
                    if dependent and name not in tainted:
                        tainted.add(name)
                        changed = True
                    elif not dependent and isinstance(n, (ast.For, ast.comprehension)):
                        inputs.add(name)
        return tainted, inputs - tainted


def run_hidden_case(
    exercise_id: str,
    code: str,
    case: str,
    probe: tuple[int, int, list[ast.expr]] | None = None,
) -> tuple[str | None, int | None, collections.Counter[int], dict[str, list[str]]]:
    """Corre un caso oculto con `code` como código del alumno, en este proceso.

    Devuelve (mensaje o None, línea del assert que falló, pasadas por cada línea, valores). Con
    probe=(línea, veces, nodos) evalúa los nodos en la pasada número `veces` por esa línea, justo
    antes de su assert, y devuelve {texto de la expresión: cómo la muestra un mensaje}.
    """
    check = spec.folder(exercise_id) / "check.py"
    fn = next(fn for fn, shown in spec.load_cases(check) if fn.__name__ == case)
    arrivals: collections.Counter[int] = collections.Counter()
    values: dict[str, list[str]] = {}
    starts: dict[int, int] = {}

    def on_call(frame: types.FrameType, event: str, arg: Any) -> Any:
        if frame.f_code.co_filename != str(check):
            return None

        def on_line(frame: types.FrameType, event: str, arg: Any) -> Any:
            # Un assert de varias líneas o con `and` puede volver a su primera línea dentro de la
            # misma pasada: solo cuenta la instrucción con que empieza.
            if (
                event == "line"
                and starts.setdefault(frame.f_lineno, frame.f_lasti) == frame.f_lasti
            ):
                arrivals[frame.f_lineno] += 1
                if probe and frame.f_lineno == probe[0] and arrivals[frame.f_lineno] == probe[1]:
                    for node in probe[2]:
                        try:
                            value = eval(
                                compile(ast.Expression(node), str(check), "eval"),
                                frame.f_globals,
                                dict(frame.f_locals),
                            )
                        except Exception:
                            continue
                        if informative(value):
                            values[ast.unparse(node)] = forms(value)
            return on_line

        return on_line

    here = os.getcwd()
    os.chdir(tempfile.mkdtemp(prefix="qg-"))
    message: str | None = None
    lineno: int | None = None
    tb: types.TracebackType | None = None
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            namespace: dict[str, Any] = {"__name__": "__main__"}
            exec(compile(code, "tu_codigo.py", "exec"), namespace)
            learner._bind(namespace)
            sys.settrace(on_call)
            try:
                fn()
            except AssertionError as exc:
                message, tb = str(exc), exc.__traceback__
    finally:
        sys.settrace(None)
        os.chdir(here)
    while tb is not None:
        if tb.tb_frame.f_code.co_filename == str(check):
            lineno = tb.tb_lineno
        tb = tb.tb_next
    return message, lineno, arrivals, values


def hidden_case_names(exercise_id: str) -> list[str]:
    return [
        fn.__name__
        for fn, shown in spec.load_cases(spec.folder(exercise_id) / "check.py")
        if shown is None
    ]


@functools.cache
def hidden_failures(
    exercise_id: str, code: str
) -> list[tuple[str, str, Site, dict[str, list[str]], dict[str, list[str]]]]:
    """[(caso, mensaje, assert que falló, valores con el código equivocado, valores con la referencia)].

    Los valores son los de las expresiones del assert que falló. La referencia las evalúa con la
    misma entrada: la misma pasada por esa línea del mismo caso.
    """
    found = []
    tree = ast.parse(read(exercise_id, "check.py"))
    for case in hidden_case_names(exercise_id):
        message, lineno, arrivals, _ = run_hidden_case(exercise_id, code, case)
        if message is None:
            continue
        assert lineno, f"{case} no falló con un assert: {message}"
        site = Site(tree, lineno)
        probe = (site.first, arrivals[site.first], site.nodes)
        wrong = run_hidden_case(exercise_id, code, case, probe)
        right = run_hidden_case(exercise_id, read(exercise_id, "solution.py"), case, probe)
        assert right[0] is None, f"la solución de referencia falla {case}: {right[0]}"
        assert wrong[0] is not None, f"{case} dejó de fallar al repetirlo"
        found.append((case, wrong[0], site, wrong[3], right[3]))
    return found


def pattern(text: str) -> str:
    """El texto entero, no dentro de otro número o palabra (0.5 no está en 0.50)."""
    return rf"(?<!\w){re.escape(text)}(?!\w|\.\d)"


def shown(message: str, candidates: Iterable[str]) -> bool:
    return any(re.search(pattern(text), message) for text in candidates)


def kinds(site: Site, got: Mapping[str, Any], want: Mapping[str, Any]) -> dict[str, str]:
    """site.kind, y del alumno todo lo que no coincide con la referencia aunque no lo calcule con `learner`
    (un circuito que el alumno modificó, un archivo que dejó en el disco)."""
    return {
        k: "learner" if kind == "fixed" and k in got and want.get(k) != got[k] else kind
        for k, kind in site.kind.items()
    }


def returned_roots(
    site: Site, kind: Mapping[str, str], got: Mapping[str, Any], want: Mapping[str, Any]
) -> list[str]:
    """Lo que el assert observa del código del alumno y no coincide con la referencia, sin sus partes."""
    differing = {
        k: n
        for k, n in site.test.items()
        if kind[k] == "learner" and k in got and want.get(k) != got[k]
    }
    inner = {ast.unparse(d) for n in differing.values() for d in ast.walk(n) if d is not n}
    return [k for k in differing if k not in inner]


@pytest.mark.parametrize(
    "exercise_id,code", MUTANTS, ids=[f"{eid}#{k}" for k, (eid, _) in enumerate(MUTANTS)]
)
def test_hidden_messages_show_the_input_and_the_return_but_not_the_expected_value(
    exercise_id: str, code: str
) -> None:
    failures = hidden_failures(exercise_id, code)
    assert failures, "el código equivocado no falla ningún caso oculto"
    for case, message, site, got, want in failures:
        assert names_its_input(exercise_id, message), f"{case} no nombra su entrada: {message}"

        kind = kinds(site, got, want)

        # Cada cosa que el assert observa del código del alumno llega al mensaje: una expresión que el
        # mensaje interpola se calcula con ella, vale distinto que con la referencia y se ve en el texto.
        roots = returned_roots(site, kind, got, want)
        for root in roots:
            holders = [
                k
                for k in site.interpolated
                if k in got
                and want.get(k) != got[k]
                and (k == root or site.parts(site.message[k]) & site.parts(site.test[root]))
            ]
            # Un entero suelto en el texto puede ser otro número; solo cuenta si viene de una expresión.
            written = [t for t in got[root] if not re.fullmatch(r"-?\d+", t)]
            assert shown(message, written) or any(shown(message, got[k]) for k in holders), (
                f"{case} no muestra lo que devolvió el código ({root} = {got[root][0]}): {message}"
            )
        if not roots:
            changed = [k for k in got if kind[k] == "learner" and want.get(k) != got[k]]
            assert any(shown(message, got[k]) for k in changed), (
                f"{case} no muestra lo que devolvió el código: {message}"
            )

        # Ningún valor esperado: ni el de la referencia en lo que cambia, ni un literal o un valor que
        # el check calcula aparte, salvo que el alumno lo haya devuelto o sea la entrada.
        rest = message
        for text in sorted(
            {t for k in got if kind[k] != "fixed" for t in got[k]}, key=len, reverse=True
        ):
            rest = re.sub(pattern(text), "\0", rest)
        expected = {
            k: v
            for k, v in want.items()
            if kind[k] == "fixed" or (kind[k] == "learner" and v != got.get(k))
        }
        leaked = {k: t for k, v in expected.items() for t in v if shown(rest, [t])}
        assert not leaked, f"{case} muestra el valor esperado {leaked}: {message}"


@pytest.mark.parametrize("exercise_id", REAL)
def test_every_hidden_case_is_checked_against_a_wrong_answer(exercise_id: str) -> None:
    reached = {
        case
        for eid, code in MUTANTS
        if eid == exercise_id
        for case, *_ in hidden_failures(eid, code)
    }
    missing = [case for case in hidden_case_names(exercise_id) if case not in reached]
    assert hidden_case_names(exercise_id) and not missing, (
        f"ningún código equivocado falla {missing}"
    )


def test_run_mode_returns_output_without_tests() -> None:
    result = grade("q2-kernel/kernel-fidelidad", "print('hola')", mode="run")
    assert (
        result["stdout"] == "hola\n"
        and result["tests"] == []
        and result["error"] is None
        and result["passed"]
    )


def test_missing_name_is_explained() -> None:
    result = grade("q2-kernel/kernel-fidelidad", "x = 1")
    assert not result["passed"]
    assert all("Falta definir `kernel`" in t["message"] for t in result["tests"])


def test_syntax_error_names_the_line() -> None:
    result = grade("q2-kernel/kernel-fidelidad", "x = 1\ndef f(:\n")
    assert (
        result["error"].startswith("SyntaxError")
        and "línea 2" in result["error"]
        and result["tests"] == []
    )


def test_runtime_error_names_the_learner_line() -> None:
    result = grade("q2-kernel/kernel-fidelidad", "x = 1\nprint(y)\n")
    assert result["error"] == "NameError: name 'y' is not defined (línea 2: print(y))"


def test_failure_inside_a_case_is_reported_as_the_learner_code() -> None:
    result = grade(
        "q2-kernel/kernel-fidelidad", "def kernel(x, y):\n    raise ValueError('no sé')\n"
    )
    assert any("Tu código lanzó ValueError: no sé" in t["message"] for t in failed(result))
    assert all("Pasó al usar `kernel(" in t["message"] for t in failed(result)), [
        t["message"] for t in failed(result)
    ]


def test_circuit_without_measurement_names_the_call_that_built_it(fixture_dir: Path) -> None:
    write_exercise(
        fixture_dir,
        "leccion/uno",
        check="from qgcheck import counts, learner\ndef test_measurement():\n    assert counts(learner.ghz(3))\n",
    )
    result = grade(
        "leccion/uno",
        "from qiskit import QuantumCircuit\ndef ghz(n):\n    return QuantumCircuit(n)\n",
    )
    messages = [t["message"] for t in failed(result)]
    assert any("no mide ningún qubit" in m and "Pasó al usar `ghz(" in m for m in messages), (
        messages
    )


def test_learner_data_that_cannot_be_rebuilt_is_a_broken_channel(fixture_dir: Path) -> None:
    write_exercise(
        fixture_dir,
        "leccion/uno",
        check="from qgcheck import learner\ndef test_state():\n    assert learner.psi is not None\n",
    )
    code = "from qiskit.quantum_info import Statevector\nclass Torcido(Statevector):\n    def dims(self, qargs=None):\n        return (3,)\npsi = Torcido([1, 0])\n"
    messages = [t["message"] for t in failed(grade("leccion/uno", code))]
    assert messages and set(messages) == {
        "Tu código terminó o rompió el canal antes de dar un resultado."
    }


def test_infinite_loop_is_stopped() -> None:
    result = grade("q2-kernel/kernel-fidelidad", "while True:\n    pass\n", timeout=2)
    assert result["error"] == "Tu código tardó más de 2 s y se detuvo." and not result["passed"]


def test_oversized_code_is_refused() -> None:
    result = grade("q2-kernel/kernel-fidelidad", "x = 1\n" * 10_000)
    assert "supera" in result["error"] and not result["passed"]


def test_blocked_module_cannot_be_imported() -> None:
    result = grade(
        "q2-kernel/kernel-fidelidad", "import qiskit_aer", mode="run", block=("qiskit_aer",)
    )
    assert result["error"].startswith("ModuleNotFoundError: import of qiskit_aer halted")


def test_unknown_or_malformed_id_is_rejected() -> None:
    with pytest.raises(ValueError):
        grade("p1-quickstart/no-existe", "")
    with pytest.raises(ValueError):
        grade("../etc/passwd", "")


SECRET_SOLUTION = "SECRETO_SOLUCION"
SECRET_HIDDEN = "SECRETO_CASO_OCULTO"


def write_exercise(
    base: Path, eid: str, *, solution: str = "x = 1\n", starter: str = "x = 0\n", check: str = ""
) -> None:
    d = base / eid
    d.mkdir(parents=True)
    (d / "solution.py").write_text(solution, encoding="utf-8")
    (d / "starter.py").write_text(starter, encoding="utf-8")
    check = check or (
        "from qgcheck import learner, visible\n\n\n"
        "@visible('x vale uno')\n"
        "def test_shown():\n    assert learner.x == 1, 'x debería valer 1'\n\n\n"
        f"def test_hidden():\n    assert learner.x == 1, '{SECRET_HIDDEN}'\n"
    )
    (d / "check.py").write_text(check, encoding="utf-8")


def lesson_with(*blocks: dict[str, Any]) -> dict[str, Any]:
    return dict(id="leccion", beats=[dict(id="paso", scene=list(blocks))])


def exercise_block(eid: str) -> dict[str, Any]:
    return dict(
        type="exercise", exercise=eid, prompt="Haz x.", level=2, needs="qiskit", hints=["pista"]
    )


@pytest.fixture
def fixture_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    monkeypatch.setenv("QG_EXERCISES", str(tmp_path))
    build.ERRORS.clear()
    yield tmp_path
    build.ERRORS.clear()


def test_build_publishes_only_public_fields(fixture_dir: Path) -> None:
    write_exercise(fixture_dir, "leccion/uno", solution=f"x = 1  # {SECRET_SOLUTION}\n")
    les = lesson_with(
        dict(type="box", kind="idea", title="t", body=[exercise_block("leccion/uno")])
    )
    build.publish_exercises(les, set())
    assert build.ERRORS == []
    published = json.dumps(les, ensure_ascii=False)
    assert (
        SECRET_SOLUTION not in published
        and SECRET_HIDDEN not in published
        and "test_hidden" not in published
    )
    blk = les["beats"][0]["scene"][0]["body"][0]
    assert blk["starter"] == "x = 0" and blk["cases"] == ["x vale uno"]
    assert (
        blk["prompt"] == "Haz x."
        and blk["hints"] == ["pista"]
        and blk["level"] == 2
        and blk["needs"] == "qiskit"
    )
    assert set(blk) == {"type", "exercise", "prompt", "level", "needs", "hints", "starter", "cases"}


def test_build_rejects_a_broken_exercise_reference(fixture_dir: Path) -> None:
    write_exercise(fixture_dir, "leccion/uno")
    write_exercise(fixture_dir, "otra/dos")
    (fixture_dir / "leccion" / "uno" / "check.py").write_text(
        "def test_only_hidden():\n    pass\n", encoding="utf-8"
    )
    seen: set[str] = set()
    for eid in ("leccion/uno", "leccion/uno", "otra/dos", "leccion/falta", "Leccion/Mal"):
        build.publish_exercises(lesson_with(exercise_block(eid)), seen)
    text = "\n".join(build.ERRORS)
    assert "leccion/uno no tiene ningún caso @visible" in text
    assert "otra/dos debe estar en exercises/leccion/" in text
    assert "leccion/falta no tiene starter.py, solution.py, check.py" in text
    assert "id de ejercicio inválido" in text
    assert "leccion/uno está repetido" in text


def test_exercise_rejects_unknown_level_and_needs() -> None:
    from lib import Exercise

    with pytest.raises(ValueError):
        Exercise("a/b", "p", level=4)
    with pytest.raises(ValueError):
        Exercise("a/b", "p", level=1, needs="gpu")


def test_tool_accepts_a_sound_exercise(fixture_dir: Path) -> None:
    write_exercise(fixture_dir, "leccion/uno")
    assert exercises_tool.problems("leccion/uno", "qiskit") == []


def test_tool_flags_a_failing_solution(fixture_dir: Path) -> None:
    write_exercise(fixture_dir, "leccion/uno", solution="x = 2\n")
    assert any(
        "solution.py no pasa: x vale uno: x debería valer 1" in p
        for p in exercises_tool.problems("leccion/uno", "qiskit")
    )


def test_tool_flags_a_starter_that_is_already_solved(fixture_dir: Path) -> None:
    write_exercise(fixture_dir, "leccion/uno", starter="x = 1\n")
    assert "starter.py ya pasa todos los casos" in exercises_tool.problems("leccion/uno", "qiskit")


def test_tool_flags_a_starter_that_crashes(fixture_dir: Path) -> None:
    write_exercise(fixture_dir, "leccion/uno", starter="x = 1 / 0\n")
    assert any(
        "starter.py falla al ejecutarse: ZeroDivisionError" in p
        for p in exercises_tool.problems("leccion/uno", "qiskit")
    )


def test_tool_flags_needs_that_does_not_match_the_solution(fixture_dir: Path) -> None:
    write_exercise(fixture_dir, "leccion/uno", solution="import qiskit_aer\nx = 1\n")
    write_exercise(fixture_dir, "leccion/dos")
    assert any(
        'needs="qiskit" pero solution.py necesita qiskit_aer' in p
        for p in exercises_tool.problems("leccion/uno", "qiskit")
    )
    assert exercises_tool.problems("leccion/uno", "aer") == []
    assert 'needs="aer" pero solution.py pasa sin qiskit_aer' in exercises_tool.problems(
        "leccion/dos", "aer"
    )


HINTED_CHECK = (
    "from qgcheck import hint, learner, visible\n\n\n"
    "@visible('x vale uno')\n@hint(2)\n"
    "def test_shown():\n    assert learner.x == 1, 'x debería valer 1'\n\n\n"
    "@hint(1)\n"
    "def test_hidden():\n    assert learner.x == 1, 'x debería valer 1'\n\n\n"
    "def test_plain():\n    assert learner.x == 1, 'x debería valer 1'\n"
)


def test_grade_reports_the_hint_each_case_names(fixture_dir: Path) -> None:
    write_exercise(fixture_dir, "leccion/uno", check=HINTED_CHECK)
    result = grade("leccion/uno", "x = 0\n")
    assert [(t["name"], t["hint"]) for t in result["tests"]] == [
        ("x vale uno", 2),
        ("caso oculto 1", 1),
        ("caso oculto 2", None),
    ]


def test_tool_flags_a_hint_the_exercise_does_not_have(fixture_dir: Path) -> None:
    write_exercise(fixture_dir, "leccion/uno", check=HINTED_CHECK)
    assert exercises_tool.problems("leccion/uno", "qiskit", hints=2) == []
    assert exercises_tool.problems("leccion/uno", "qiskit", hints=1) == [
        "test_shown nombra la pista 2 y el ejercicio tiene 1"
    ]


def test_tool_reports_a_malformed_declared_id(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(exercises_tool, "declared", lambda: {"Mal/ID": "qiskit"})
    monkeypatch.setattr(sys, "argv", ["exercises.py"])
    with pytest.raises(SystemExit) as stop:
        exercises_tool.main()
    assert stop.value.code == 1
    assert "id de ejercicio inválido" in capsys.readouterr().out


@pytest.fixture
def server() -> Iterator[str]:
    import threading
    from functools import partial
    from http.server import ThreadingHTTPServer

    serve = load_tool("serve_tool", "serve.py")
    handler = type("Quiet", (serve.Handler,), {"log_message": lambda *a: None})
    srv = ThreadingHTTPServer(("127.0.0.1", 0), partial(handler, directory=str(ROOT / "site")))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def post(
    base: str,
    body: dict[str, Any],
    content_type: str = "application/json",
    host: str | None = None,
) -> tuple[int, dict[str, Any]]:
    import urllib.error
    import urllib.request

    req = urllib.request.Request(
        base + "/run",
        data=json.dumps(body).encode(),
        method="POST",
        headers={"Content-Type": content_type, **({"Host": host} if host else {})},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as err:
        return err.code, json.load(err)


def test_server_grades_the_solution_and_a_wrong_answer(server: str) -> None:
    solution = (spec.folder("q2-kernel/kernel-fidelidad") / "solution.py").read_text(
        encoding="utf-8"
    )
    status, ok = post(
        server, {"exercise": "q2-kernel/kernel-fidelidad", "code": solution, "mode": "check"}
    )
    assert (status, ok["passed"]) == (200, True)
    status, bad = post(
        server,
        {"exercise": "q2-kernel/kernel-fidelidad", "code": "def kernel(x, y):\n    return 0.0\n"},
    )
    assert status == 200 and not bad["passed"]


def test_server_serves_the_site_and_rejects_bad_requests(server: str) -> None:
    import urllib.request

    assert b"<title>" in urllib.request.urlopen(server + "/index.html").read()
    assert post(server, {"exercise": "../x", "code": ""})[0] == 400
    assert (
        post(
            server,
            {"exercise": "q2-kernel/kernel-fidelidad", "code": ""},
            content_type="text/plain",
        )[0]
        == 403
    )
    assert (
        post(server, {"exercise": "q2-kernel/kernel-fidelidad", "code": ""}, host="evil.example")[0]
        == 403
    )
