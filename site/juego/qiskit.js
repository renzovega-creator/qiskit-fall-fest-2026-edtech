// Ejecuta los experimentos con Qiskit a través de POST /run (tools/serve.py en el equipo, o el
// corredor desplegado) y devuelve el JSON que imprime el código. Todo corre en un simulador:
// StatevectorSampler muestrea shots del estado exacto; no hay hardware cuántico de por medio.
//
// El código de cada experimento es Python legible: se muestra en la misión y se guarda en la
// evidencia para que cualquiera pueda reproducirlo.
import { LUNAS, RETO_KERNEL } from "./datos.js";
import { DEMO_MODE, resultadoMision } from "../demo.js";

export const BACKEND = "Simulador · StatevectorSampler de Qiskit";
const EXERCISE = "q1-montecarlo/estimar-p";
const TIMEOUT_MS = 30000;

let turnstileLib = null;
const loadTurnstile = () =>
  (turnstileLib ??= new Promise((ok, no) => {
    const sc = document.createElement("script");
    sc.src =
      "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
    sc.addEventListener("load", () => ok(window.turnstile));
    sc.addEventListener("error", () => {
      turnstileLib = null;
      no(
        new Error("No se pudo cargar la comprobación de que eres una persona."),
      );
    });
    document.head.appendChild(sc);
  }));

// El corredor desplegado puede pedir Turnstile en la primera petición; serve.py nunca lo pide.
async function tokenTurnstile(sitekey, signal) {
  const lib = await loadTurnstile();
  const slot = document.createElement("div");
  document.body.appendChild(slot);
  let id;
  try {
    return await new Promise((ok, no) => {
      signal.addEventListener("abort", () =>
        no(new DOMException("", "AbortError")),
      );
      id = lib.render(slot, {
        sitekey,
        appearance: "interaction-only",
        callback: ok,
        "error-callback": () => no(new Error("La comprobación falló.")),
      });
    });
  } finally {
    if (id !== undefined) lib.remove(id);
    slot.remove();
  }
}

export async function ejecutar(code) {
  const ctl = new AbortController();
  const cut = setTimeout(() => ctl.abort(), TIMEOUT_MS);
  const post = (token) =>
    fetch("/run", {
      method: "POST",
      signal: ctl.signal,
      headers: {
        "Content-Type": "application/json",
        ...(token && { "X-Turnstile-Token": token }),
      },
      body: JSON.stringify({ exercise: EXERCISE, code, mode: "run" }),
    });
  try {
    let resp = await post();
    let body = await resp.json().catch(() => null);
    if (resp.status === 403 && body?.reason === "turnstile_missing")
      body = await (
        await post(await tokenTurnstile(body.sitekey, ctl.signal))
      )
        .json()
        .catch(() => null);
    else if ([404, 405, 501].includes(resp.status))
      throw new Error(
        "Esta página no tiene el corredor de Qiskit. Ábrela con `uv run python tools/serve.py` (con QG_CURSO=qml).",
      );
    else if (resp.status === 429)
      throw new Error(
        "Has ejecutado demasiadas veces seguidas. Espera un momento.",
      );
    else if (resp.status === 503)
      throw new Error("El corredor está ocupado. Inténtalo en unos segundos.");
    if (!body)
      throw new Error("El corredor respondió algo que no se entiende.");
    if (body.error) throw new Error(`Qiskit devolvió un error: ${body.error}`);
    const ultima = (body.stdout || "").trim().split("\n").pop();
    return JSON.parse(ultima);
  } catch (e) {
    if (e.name === "AbortError")
      throw new Error(
        `Qiskit no respondió en ${TIMEOUT_MS / 1000} s. Inténtalo de nuevo.`,
        { cause: e },
      );
    if (e instanceof SyntaxError)
      throw new Error("La salida de Qiskit no tiene el formato esperado.", {
        cause: e,
      });
    if (e instanceof TypeError)
      throw new Error("No se pudo conectar con el corredor de Qiskit.", {
        cause: e,
      });
    throw e;
  } finally {
    clearTimeout(cut);
  }
}

const py = (xs) => JSON.stringify(xs).replaceAll(",", ", ");

export async function medirMision(id, params) {
  return DEMO_MODE ? resultadoMision(id, params) : ejecutar(codigo[id](params));
}

export const codigo = {
  m1: ({ theta, shots, seed }) => `import json
import numpy as np
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler
from qiskit.quantum_info import Statevector

theta = np.deg2rad(${theta})    # el ángulo que elegiste, en grados
qc = QuantumCircuit(1)
qc.ry(theta, 0)
p1 = Statevector(qc).probabilities()[1]   # probabilidad teórica (regla de Born)

qc.measure_all()
res = StatevectorSampler(seed=${seed}).run([qc], shots=${shots}).result()
shots = res[0].data.meas.get_bitstrings()  # cada shot, en el orden en que salió
print(json.dumps({"p1": float(p1), "shots": "".join(shots)}))`,

  m2: ({ shots, reps, seed }) => `import json
import numpy as np
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

qc = QuantumCircuit(1)
qc.ry(np.pi / 3, 0)             # la moneda del 25 %: P(1) = sin²(π/6)
qc.measure_all()

N = ${shots}
estimaciones = []
for r in range(${reps}):        # estimaciones independientes de N shots cada una
    res = StatevectorSampler(seed=${seed} + r).run([qc], shots=N).result()
    estimaciones.append(res[0].data.meas.get_counts().get("1", 0) / N)
print(json.dumps({"estimaciones": estimaciones}))`,

  m3: ({ escala, reps }) => `import json
import numpy as np
from qiskit.circuit.library import zz_feature_map
from qiskit.quantum_info import Statevector

escala, reps = ${escala}, ${reps}
mapa = zz_feature_map(2, reps=reps)
train = np.array(${py(LUNAS.train)})   # x, y, clase
test = np.array(${py(LUNAS.test)})


def estado(x):
    return Statevector(mapa.assign_parameters(escala * np.asarray(x)))


conocidos = [estado(p[:2]) for p in train]
clase = train[:, 2]


def puntuacion(x):
    v = estado(x)
    k = np.array([abs(c.inner(v)) ** 2 for c in conocidos])   # kernel cuántico
    return float(k[clase == 1].mean() - k[clase == 0].mean())  # > 0: clase 1


malla = [[round(puntuacion([i / 12, j / 12]), 4) for i in range(13)] for j in range(13)]
print(json.dumps({"test": [round(puntuacion(p[:2]), 4) for p in test], "malla": malla}))`,

  t1: ({ shots, reps }) => `import json
import numpy as np
from qiskit.circuit.library import zz_feature_map
from qiskit.primitives import StatevectorSampler
from qiskit.quantum_info import Statevector

mapa = zz_feature_map(2, reps=1)
U = lambda x: mapa.assign_parameters(${RETO_KERNEL.escala} * np.asarray(x))
punto, a, b = ${py(RETO_KERNEL.punto)}, ${py(RETO_KERNEL.claseA)}, ${py(RETO_KERNEL.claseB)}


def kernel_exacto(x, y):
    return float(abs(Statevector(U(y)).inner(Statevector(U(x)))) ** 2)


def circuito(x, y):             # U(x) y luego U(y)†: P(00) = k(x, y)
    qc = U(x).compose(U(y).inverse())
    qc.measure_all()
    return qc


N = ${shots}
pa, pb = [], []
for r in range(${reps}):        # semillas distintas: cada estimación es independiente
    for ref, lista, s in ((a, pa, 2 * r), (b, pb, 2 * r + 1)):
        res = StatevectorSampler(seed=s).run([circuito(punto, ref)], shots=N).result()
        lista.append(res[0].data.meas.get_counts().get("00", 0) / N)
print(json.dumps({"ka": kernel_exacto(punto, a), "kb": kernel_exacto(punto, b), "pa": pa, "pb": pb}))`,
};

// Función de distribución de la normal estándar (aproximación de Abramowitz y Stegun 7.1.26).
export function phi(z) {
  const t = 1 / (1 + (0.3275911 * Math.abs(z)) / Math.SQRT2);
  const y =
    1 -
    ((((1.061405429 * t - 1.453152027) * t + 1.421413741) * t - 0.284496736) *
      t +
      0.254829592) *
      t *
      Math.exp((-z * z) / 2);
  return z >= 0 ? (1 + y) / 2 : (1 - y) / 2;
}
