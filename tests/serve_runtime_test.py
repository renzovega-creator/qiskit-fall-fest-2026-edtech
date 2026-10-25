import importlib.util
import json
import os
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
NO_NUMPY_PYTHON = Path("C:/Python313/python.exe")


def load_serve() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("serve_runtime", ROOT / "tools" / "serve.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.skipif(
    os.name != "nt" or not NO_NUMPY_PYTHON.is_file(),
    reason="Reproduce la instalación de Python de Windows que no contiene NumPy.",
)
def test_local_qiskit_run_uses_project_venv_when_server_python_lacks_numpy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    serve = load_serve()
    monkeypatch.setattr(serve.sys, "executable", str(NO_NUMPY_PYTHON))

    result = serve.run_plain(
        "q1-montecarlo/estimar-p",
        "import json\n"
        "import numpy as np\n"
        "from qiskit import QuantumCircuit\n"
        "from qiskit.primitives import StatevectorSampler\n"
        "qc = QuantumCircuit(1)\n"
        "qc.ry(np.pi / 3, 0)\n"
        "qc.measure_all()\n"
        "N = 500\n"
        "estimaciones = []\n"
        "for r in range(30):\n"
        "    res = StatevectorSampler(seed=100 + r).run([qc], shots=N).result()\n"
        "    estimaciones.append(res[0].data.meas.get_counts().get('1', 0) / N)\n"
        "print(json.dumps({'estimaciones': estimaciones}))\n",
    )

    assert result["error"] is None, result
    estimaciones = json.loads(result["stdout"])["estimaciones"]
    assert len(estimaciones) == 30
    assert all(0 <= value <= 1 for value in estimaciones)
