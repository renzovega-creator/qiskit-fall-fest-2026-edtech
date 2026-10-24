"""Calcula las cifras que muestran las lecciones del curso QML (se pegan a mano en parte*.py).

    python cursos/qml/numeros.py
"""

import time

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import zz_feature_map
from qiskit.primitives import StatevectorSampler
from qiskit_machine_learning.algorithms import QSVC
from qiskit_machine_learning.kernels import FidelityQuantumKernel
from sklearn.datasets import make_moons
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.svm import SVC

# Par 1: Monte Carlo ↔ shots
theta = np.pi / 3
qc = QuantumCircuit(1)
qc.ry(theta, 0)
qc.measure_all()
c = StatevectorSampler(seed=7).run([qc], shots=100).result()[0].data.meas.get_counts()
print("RY(pi/3), 100 shots:", c, "P(1) exacta =", round(np.sin(theta / 2) ** 2, 4))

for n in (10, 100, 1000, 10000):
    errs = []
    for s in range(20):
        k = StatevectorSampler(seed=s).run([qc], shots=n).result()[0].data.meas.get_counts().get("1", 0)
        errs.append(abs(k / n - 0.25))
    print(f"shots={n:>5}  error medio={np.mean(errs):.4f}  sqrt(p(1-p)/N)={np.sqrt(0.25 * 0.75 / n):.4f}")

rng = np.random.default_rng(7)
for n in (10, 100, 1000, 10000):
    print(f"moneda N={n:>5}  frecuencia={np.mean(rng.random(n) < 0.25):.4f}")

# Par 2: SVM ↔ kernel cuántico
X, y = make_moons(n_samples=80, noise=0.2, random_state=0)
X = MinMaxScaler((0, np.pi)).fit_transform(X)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=0)
t = time.time()
rbf = SVC(kernel="rbf").fit(Xtr, ytr)
print("SVC rbf  test acc =", round(rbf.score(Xte, yte), 3), f"({time.time() - t:.2f} s)")
fm = zz_feature_map(2, reps=2)
t = time.time()
qsvc = QSVC(quantum_kernel=FidelityQuantumKernel(feature_map=fm)).fit(Xtr, ytr)
print("QSVC zz  test acc =", round(qsvc.score(Xte, yte), 3), f"({time.time() - t:.2f} s)")
kern = FidelityQuantumKernel(feature_map=fm)
print("k(x0,x0) =", round(float(kern.evaluate(Xtr[:1])[0, 0]), 4), " k(x0,x1) =", round(float(kern.evaluate(Xtr[:1], Xtr[1:2])[0, 0]), 4))
print("x0 =", Xtr[0].round(3), " x1 =", Xtr[1].round(3))
