from qiskit.circuit.library import n_local

ansatz = n_local(3, "rx", "cz")

prediccion = None   # ✏️ tu apuesta: ¿cuántos parámetros tiene ansatz?
# compruébalo con print(ansatz.num_parameters); ansatz.decompose().draw("mpl") lo dibuja
