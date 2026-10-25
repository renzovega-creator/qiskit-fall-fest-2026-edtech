const SHOTS = (theta, shots) => `import numpy as np
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler
qc = QuantumCircuit(1)
qc.ry(${theta}, 0)
qc.measure_all()
res = StatevectorSampler(seed=SEMILLA).run([qc], shots=${shots}).result()
print(res[0].data.meas.get_counts().get("1", 0))`;
export const RETOS = [
  {
    id: "born-50",
    de: "q1-montecarlo",
    p: "Aplicas $R_Y(\\pi/2)$ a $|0\\rangle$ y mides **400 shots**. ¿Cuántos `1` saldrán?",
    code: SHOTS("np.pi / 2", 400),
    tol: 20,
    why: "$P(1)=\\sin^2(\\pi/4)=1/2$: se esperan 200, con un error típico de $\\sqrt{400\\cdot\\tfrac12\\cdot\\tfrac12}=10$.",
  },
  {
    id: "born-75",
    de: "q1-montecarlo",
    p: "Aplicas $R_Y(2\\pi/3)$ y mides **200 shots**. ¿Cuántos `1` saldrán?",
    code: SHOTS("2 * np.pi / 3", 200),
    tol: 12,
    why: "$P(1)=\\sin^2(\\pi/3)=3/4$: se esperan 150, con un error típico de $\\sqrt{200\\cdot\\tfrac34\\cdot\\tfrac14}\\approx 6$.",
  },
  {
    id: "born-25",
    de: "q1-montecarlo",
    p: "Aplicas $R_Y(\\pi/3)$ y mides **1000 shots**. ¿Cuántos `1` saldrán?",
    code: SHOTS("np.pi / 3", 1000),
    tol: 27,
    why: "$P(1)=\\sin^2(\\pi/6)=1/4$: se esperan 250, con un error típico de $\\sqrt{1000\\cdot\\tfrac14\\cdot\\tfrac34}\\approx 14$.",
  },
  {
    id: "kernel-zz",
    de: "q2-kernel",
    p: "Kernel cuántico con `zz_feature_map(2, reps=1)`: ¿cuánto vale $k(x,x')$ para $x=[0.2,\\,0.7]$ y $x'=[0.9,\\,0.1]$? (dos decimales)",
    tol: 0.1,
    code: `from qiskit.circuit.library import zz_feature_map
from qiskit.quantum_info import Statevector
m = zz_feature_map(2, reps=1)
e = lambda x: Statevector(m.assign_parameters(x))
print(round(abs(e([0.9, 0.1]).inner(e([0.2, 0.7]))) ** 2, 4))`,
    why: "Los puntos están lejos, así que el solapamiento es bajo; el RBF con $\\gamma=0.5$ daría 0.65 para el mismo par.",
  },
];
