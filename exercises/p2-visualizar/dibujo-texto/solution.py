from qiskit import QuantumCircuit

circuito = QuantumCircuit(3, 3)
circuito.x(1)
circuito.h(range(3))
circuito.cx(0, 1)
circuito.barrier()
circuito.measure(range(3), range(3))

dibujo = circuito.draw("text", reverse_bits=True, plot_barriers=False)
print(dibujo)
