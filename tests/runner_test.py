"""Prueba el corredor por HTTP contra la imagen real en Docker.

    uv run --group runner-test pytest tests/runner_test.py

Construye `qg-runner` con `runner/local.py`. Se salta si Docker no responde.
`QG_DOCKER` y `QG_RUNTIME` eligen el comando y el runtime.
"""
import json
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "runner"))
import local  # noqa: E402

EXERCISES = ROOT / "exercises"
EXERCISE_IDS = sorted(
    str(p.parent.relative_to(EXERCISES)) for p in EXERCISES.glob("*/*/check.py")
)


@pytest.fixture(scope="module")
def runner():
    try:
        local.docker("info")
    except (OSError, subprocess.CalledProcessError) as e:
        pytest.skip(f"Docker no responde: {e}")
    local.build()
    container = local.start()
    yield container
    container.stop()


def post(container, body, raw=None):
    data = raw if raw is not None else json.dumps(body).encode()
    req = urllib.request.Request(
        f"{container.url}/run", data, {"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.load(e)


def run(container, code):
    status, out = post(container, {"code": code})
    assert status == 200, out
    return out


def check(container, exercise, code):
    status, out = post(container, {"mode": "check", "exercise": exercise, "code": code})
    assert status == 200, out
    return out


def health(container):
    with urllib.request.urlopen(f"{container.url}/health", timeout=5) as r:
        return r.status


def processes(container):
    out = run(container, "import os; print(*[p for p in os.listdir('/proc') if p.isdigit()])")
    return out["stdout"].split()


def test_run_returns_stdout_and_exit_code(runner):
    out = run(runner, "import sys\nprint('hola')\nprint('aviso', file=sys.stderr)")
    assert out["ok"] is True
    assert out["stdout"] == "hola\n"
    assert out["stderr"] == "aviso\n"
    assert out["exit_code"] == 0
    assert out["tests"] == []
    assert out["ms"] > 0


def test_run_reports_the_traceback(runner):
    out = run(runner, "def f():\n    return 1 / 0\nf()")
    assert out["ok"] is False
    assert out["exit_code"] == 1
    assert "ZeroDivisionError" in out["stderr"]


def test_image_has_qiskit_aer_and_runtime(runner):
    out = run(
        runner,
        "import qiskit, qiskit_aer, qiskit_ibm_runtime, pytest\n"
        "from qiskit_aer import AerSimulator\nprint(qiskit.__version__)",
    )
    assert out["ok"], out["stderr"]
    assert out["stdout"].strip() == "2.5.2"


@pytest.mark.parametrize("exercise", EXERCISE_IDS)
def test_check_passes_the_solution(runner, exercise):
    out = check(runner, exercise, (EXERCISES / exercise / "solution.py").read_text())
    assert out["ok"], out
    assert out["tests"] and all(t["passed"] for t in out["tests"])


@pytest.mark.parametrize("exercise", EXERCISE_IDS)
def test_check_fails_the_starter_with_messages(runner, exercise):
    out = check(runner, exercise, (EXERCISES / exercise / "starter.py").read_text())
    assert out["ok"] is False
    failed = [t for t in out["tests"] if not t["passed"]]
    assert failed and all(t["message"] for t in failed)


def test_check_hides_the_name_of_hidden_cases(runner):
    out = check(runner, "p1-quickstart/ghz", "from qiskit import QuantumCircuit\n"
                "def ghz(n):\n    qc = QuantumCircuit(n)\n    qc.measure_all()\n    return qc\n")
    by_visible = {t["visible"]: t for t in out["tests"]}
    assert by_visible[True]["name"] == "n = 2, 3 y 4"
    assert by_visible[True]["message"] == "con n = 2 salen ['00']"
    assert by_visible[False]["name"] is None


def test_check_names_the_missing_function(runner):
    out = check(runner, "p1-quickstart/ghz", "x = 1\n")
    assert out["ok"] is False
    assert all("Falta `ghz`" in t["message"] for t in out["tests"])


def test_check_survives_a_syntax_error(runner):
    out = check(runner, "p1-quickstart/ghz", "def ghz(n:\n")
    assert out["ok"] is False
    assert all("SyntaxError" in t["message"] for t in out["tests"])
    assert "SyntaxError" in out["stderr"]


def test_check_returns_what_the_code_prints(runner):
    code = (EXERCISES / "p1-quickstart/ghz/solution.py").read_text() + "\nprint('cargado')\n"
    out = check(runner, "p1-quickstart/ghz", code)
    assert out["ok"] and out["stdout"] == "cargado\n"


def test_check_cannot_pass_by_exiting_early(runner):
    out = check(runner, "p1-quickstart/ghz", "import os\nos._exit(0)\n")
    assert out["ok"] is False
    assert out["tests"] and not any(t["passed"] for t in out["tests"])


GOOD_GHZ = """
from qiskit import QuantumCircuit
def good(n):
    qc = QuantumCircuit(n)
    qc.h(0)
    for k in range(n - 1):
        qc.cx(k, k + 1)
    qc.measure_all()
    return qc
"""


def failed_everything(out):
    return out["ok"] is False and out["tests"] and not any(t["passed"] for t in out["tests"])


def test_check_grades_the_submitted_function_not_a_replaced_one(runner):
    code = GOOD_GHZ + """
import qgcheck
qgcheck.learner.ghz = good
def ghz(n):
    qc = QuantumCircuit(n)
    qc.measure_all()
    return qc
"""
    assert failed_everything(check(runner, "p1-quickstart/ghz", code))


def test_check_cannot_be_passed_by_replacing_the_checker(runner):
    code = """
import builtins, pytest, qgcheck, sys
qgcheck.learner.ghz = lambda n: None
qgcheck.counts = lambda *a, **k: {"0": 1}
sys.modules["qgcheck"] = None
pytest.fail = pytest.skip = lambda *a, **k: None
"""
    assert failed_everything(check(runner, "p1-quickstart/ghz", code))


def test_check_cannot_pass_by_forging_the_report(runner):
    code = """
import os
forged = b'{"tests": [{"name": null, "visible": false, "passed": true, "message": null}]}'
for fd in range(3, 64):
    try:
        os.write(fd, forged)
    except OSError:
        pass
"""
    assert failed_everything(check(runner, "p1-quickstart/ghz", code))


def test_check_cannot_pass_by_flooding_the_channel(runner):
    code = "import os\nfor fd in range(3, 64):\n    try: os.write(fd, b'\\xff' * 100000)\n    except OSError: pass\n"
    assert failed_everything(check(runner, "p1-quickstart/ghz", code))


def test_check_processes_are_out_of_reach_of_the_learner_code(runner):
    code = GOOD_GHZ + """
import ctypes, os
broker = os.getppid()
checker = int(open(f"/proc/{broker}/stat").read().split(")")[1].split()[1])
for pid in (broker, checker):
    for path, mode in ((f"/proc/{pid}/mem", "r+b"), (f"/proc/{pid}/environ", "rb")):
        try:
            open(path, mode).read(1)
            print("leido", path)
        except OSError:
            print("denegado")
    opened = []
    for n in range(3, 64):
        try:
            opened.append(open(f"/proc/{pid}/fd/{n}", "wb", buffering=0))
        except OSError:
            pass
    print("abiertos" if opened else "denegado")
    if ctypes.CDLL(None, use_errno=True).ptrace(16, pid, 0, 0) == 0:
        print("ptrace")
    else:
        print("denegado")
ghz = good
"""
    out = check(runner, "p1-quickstart/ghz", code)
    assert out["ok"], out
    assert out["stdout"] == "denegado\n" * 8


def test_check_learner_code_holds_only_its_own_reply_channel(runner):
    code = GOOD_GHZ + """
import os
def ghz(n):
    print(len([f for f in os.listdir("/proc/self/fd") if int(f) > 2]))
    return good(n)
"""
    out = check(runner, "p1-quickstart/ghz", code)
    assert out["ok"], out
    assert set(out["stdout"].split()) == {"2"}


def test_check_cannot_pass_by_prewriting_replies(runner):
    code = """
import os
from qiskit import QuantumCircuit
from qgcheck.wire import encode, send
def ghz(n):
    qc = QuantumCircuit(n)
    qc.h(0)
    for k in range(n - 1):
        qc.cx(k, k + 1)
    qc.measure_all()
    return qc
for fd in range(255, 2, -1):
    for n in (2, 3, 4, 5, 7):
        try:
            send(fd, {"value": encode(ghz(n))})
        except Exception:
            pass
del ghz
"""
    assert failed_everything(check(runner, "p1-quickstart/ghz", code))


def test_check_does_not_import_what_the_learner_plants(runner):
    code = GOOD_GHZ + """
import os
for name in ("qiskit", "qiskit_aer", "numpy", "pytest", "qgcheck", "json"):
    open(f"{name}.py", "w").write("print('PLANTADO')")
ghz = good
"""
    out = check(runner, "p1-quickstart/ghz", code)
    assert out["ok"], out
    assert "PLANTADO" not in out["stdout"]


@pytest.mark.parametrize(
    "body, raw, status",
    [
        ({}, b"no es json", 400),
        ({"code": 5}, None, 400),
        ({"code": "x", "mode": "otro"}, None, 400),
        ({"code": "x", "mode": "check"}, None, 400),
        ({"code": "x", "mode": "check", "exercise": "../etc/passwd"}, None, 400),
        ({"code": "x", "mode": "check", "exercise": "p9-nada/nada"}, None, 404),
        ({"code": "x" * 20_001}, None, 413),
        ({"code": "x" * 130_000}, None, 413),
    ],
)
def test_rejects_bad_requests(runner, body, raw, status):
    got, out = post(runner, body, raw)
    assert got == status
    assert out["error"]


def test_accepts_code_whose_json_is_six_times_longer(runner):
    tail = "\nprint('ok')\n"
    code = "# " + "\x01" * (20_000 - 2 - len(tail)) + tail
    assert len(code.encode()) == 20_000 and len(json.dumps({"code": code})) > 100_000
    assert run(runner, code)["stdout"] == "ok\n"


def test_unknown_path_is_404(runner):
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(f"{runner.url}/nada", timeout=5)
    assert e.value.code == 404


def test_rejects_a_second_job_while_one_runs(runner):
    first = {}
    t = threading.Thread(
        target=lambda: first.update(out=run(runner, "import time; time.sleep(2); print('listo')"))
    )
    t.start()
    time.sleep(0.7)
    status, out = post(runner, {"code": "print(1)"})
    t.join()
    assert status == 503
    assert first["out"]["stdout"] == "listo\n"


def test_timeout_kills_the_job(runner):
    out = run(runner, "while True: pass")
    assert out["ok"] is False
    assert out["timed_out"] is True
    assert out["exit_code"] is None
    assert 9_000 < out["ms"] < 13_000
    assert health(runner) == 200


@pytest.mark.parametrize(
    "code",
    [
        "x = bytearray(2 << 30)",
        "xs = []\nwhile True: xs.append(bytearray(50 << 20))",
        "import numpy as np\nx = np.ones((30000, 30000))",
    ],
)
def test_memory_cap(runner, code):
    out = run(runner, code)
    assert out["ok"] is False
    assert out["killed"] == "memory" or "MemoryError" in out["stderr"]
    assert out["peak_mb"] < 700
    assert out["ms"] < 5_000
    assert health(runner) == 200


def test_job_runs_without_privileges(runner):
    out = run(
        runner,
        "import os\nprint(os.getuid())\nprint(os.getgroups())\n"
        "print([l for l in open('/proc/self/status') if l.startswith('CapEff')][0].split()[1])",
    )
    uid, groups, caps = out["stdout"].split("\n")[:3]
    assert (uid, groups, int(caps, 16)) == ("20000", "[]", 0)


NETWORK_CODE = """
import socket
for family, address in ((socket.AF_INET, ("1.1.1.1", 53)), (socket.AF_INET6, ("2606:4700:4700::1111", 53))):
    try:
        socket.socket(family).connect(address)
        print("conectó")
    except PermissionError:
        print("denegado")
"""


def test_no_network(runner):
    out = run(runner, NETWORK_CODE)
    assert out["stdout"] == "denegado\ndenegado\n"


def test_no_network_even_when_the_container_has_internet():
    try:
        local.docker("info")
    except (OSError, subprocess.CalledProcessError) as e:
        pytest.skip(f"Docker no responde: {e}")
    container = local.start(egress=True)
    try:
        try:
            container.exec(
                "python", "-c", "import socket; socket.create_connection(('1.1.1.1', 53), timeout=3)"
            )
        except subprocess.CalledProcessError:
            pytest.skip("el anfitrión no tiene salida a internet; no hay con qué comparar")
        out = run(container, NETWORK_CODE)
        assert out["stdout"] == "denegado\ndenegado\n"
    finally:
        container.stop()


def test_fork_bomb_is_contained(runner):
    before = len(processes(runner))
    out = run(runner, "import os\nwhile True: os.fork()")
    assert out["ok"] is False
    assert out["ms"] < 13_000
    assert health(runner) == 200
    assert len(processes(runner)) <= before


def test_fork_bomb_that_swallows_errors_is_contained(runner):
    before = len(processes(runner))
    out = run(runner, "import os\nwhile True:\n    try: os.fork()\n    except OSError: pass")
    assert out["ok"] is False
    assert out["ms"] < 13_000
    assert health(runner) == 200
    assert len(processes(runner)) <= before


def test_detached_process_does_not_outlive_the_job(runner):
    before = len(processes(runner))
    out = run(runner, "import os, time\nif os.fork() == 0:\n    os.setsid()\n    time.sleep(300)\n    os._exit(0)")
    assert out["ok"] is True
    assert len(processes(runner)) <= before


@pytest.mark.parametrize(
    "path",
    ["/x", "/app/x", "/app/server.py", "/etc/x", "/usr/local/x", "/var/tmp/x",
     "/tmp/x", "/dev/shm/x", "/scratch/x", "/proc/x", "/root/x", "/home/x"],
)
def test_writes_outside_the_work_directory_fail(runner, path):
    out = run(runner, f"open({path!r}, 'w').write('x')")
    assert out["ok"] is False
    assert "Error" in out["stderr"]


def test_writes_to_the_work_directory_work_and_do_not_persist(runner):
    out = run(runner, "import os\nopen('nota.txt', 'w').write('hola')\nprint(sorted(os.listdir('.')))")
    assert out["stdout"] == "['main.py', 'nota.txt']\n"
    again = run(runner, "import os\nprint(sorted(os.listdir('.')))")
    assert again["stdout"] == "['main.py']\n"


def test_a_job_cannot_read_the_files_of_the_previous_one(runner):
    run(runner, "open('secreto.txt', 'w').write('x')")
    out = run(runner, "import glob\nprint(glob.glob('/scratch/*/secreto.txt'))")
    assert out["stdout"] == "[]\n"


def test_disk_fill_is_stopped(runner):
    out = run(runner, "for i in range(100):\n    open(f'f{i}', 'wb').write(b'x' * (8 << 20))")
    assert out["ok"] is False
    assert out["killed"] == "disk" or "No space left" in out["stderr"]
    assert out["ms"] < 5_000
    assert health(runner) == 200


def test_single_huge_file_is_refused(runner):
    out = run(runner, "open('grande', 'wb').write(b'x' * (64 << 20))")
    assert out["ok"] is False
    assert "File too large" in out["stderr"]


def test_output_flood_is_cut(runner):
    out = run(runner, "while True: print('x' * 1000)")
    assert out["ok"] is False
    assert out["killed"] == "output"
    assert len(out["stdout"]) <= 64 * 1024
