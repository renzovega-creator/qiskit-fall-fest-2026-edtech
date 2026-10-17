def tiempo_de_validez(tiempos, referencia, medida, tol):
    for t, ref, med in zip(tiempos, referencia, medida):
        if abs(med - ref) > tol:
            return float(t)
    return None


print(tiempo_de_validez([0, 1, 2, 3], [1, 1, 1, 1], [1, 0.95, 0.8, 0.5], 0.1))
