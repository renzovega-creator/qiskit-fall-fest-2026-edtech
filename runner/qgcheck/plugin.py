"""Plugin de pytest: lanza el intermediario del alumno y entrega los resultados.

Lee la ruta del código en QG_LEARNER, lanza `qgcheck.worker` antes de recolectar
las pruebas y escribe en el descriptor QG_REPORT_FD un JSON con una entrada por
prueba. Ese descriptor y el estado de las pruebas viven solo en este proceso; el
código del alumno corre en procesos que solo pueden mandar datos.
"""
import ctypes
import json
import os

import pytest

import qgcheck

_results = []


PR_SET_DUMPABLE = 4


def pytest_configure(config):
    # Sin esto el proceso del alumno, que tiene el mismo uid, podría leer y
    # escribir la memoria de este con /proc/<pid>/mem o ptrace.
    ctypes.CDLL(None).prctl(PR_SET_DUMPABLE, 0, 0, 0, 0)
    qgcheck.learner._start(os.environ["QG_LEARNER"])


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    report = (yield).get_result()
    report.qg_name = getattr(item.obj, "qg_name", None)
    report.qg_message = None
    if call.excinfo is not None:
        error = call.excinfo.value
        if isinstance(error, pytest.fail.Exception):
            text = error.msg
        elif isinstance(error, AssertionError):
            text = str(error) or "No se cumple la comprobación."
        else:
            text = f"{type(error).__name__}: {error}"
        report.qg_message = text[: qgcheck.MESSAGE_CAP]


def pytest_runtest_logreport(report):
    if report.when == "call" or (report.when == "setup" and not report.passed):
        _results.append(
            {
                "name": report.qg_name,
                "visible": report.qg_name is not None,
                "passed": report.passed,
                "message": None if report.passed else report.qg_message,
            }
        )


def pytest_sessionfinish(session):
    qgcheck.learner._stop()
    with os.fdopen(int(os.environ["QG_REPORT_FD"]), "w") as f:
        json.dump({"tests": _results}, f)
