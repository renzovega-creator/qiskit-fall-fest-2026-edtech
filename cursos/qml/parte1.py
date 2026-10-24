"""Nivel 1 · Probabilidad y muestreo: Monte Carlo ↔ shots."""

from lib import (
    A,
    Box,
    Circ,
    Code,
    Exercise,
    G,
    Hist,
    M,
    Out,
    Row,
    T,
    Table,
    beat,
    choice,
    lesson,
    numeric,
    predict,
)

MONEDA = """
import numpy as np

rng = np.random.default_rng(7)
p = 0.25                       # probabilidad de «cara»
for n in (10, 100, 1000, 10000):
    caras = rng.random(n) < p  # n lanzamientos simulados
    print(n, caras.mean())
"""

QUBIT = """
import numpy as np
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

qc = QuantumCircuit(1)
qc.ry(np.pi / 3, 0)            # P(1) = sin²(π/6) = 0.25
qc.measure_all()

res = StatevectorSampler(seed=7).run([qc], shots=100).result()
print(res[0].data.meas.get_counts())
"""

LESSONS = [
    lesson(
        "q1-montecarlo",
        "Monte Carlo ↔ shots",
        "Estimar una probabilidad lanzando una moneda y midiendo un qubit es el mismo método: Monte Carlo.",
        [
            "estimar una probabilidad con N muestras y su error típico $\\sqrt{p(1-p)/N}$",
            "leer la regla de Born $P(1)=\\sin^2(\\theta/2)$ como una distribución de probabilidad",
            "reconocer que los shots de un circuito son muestras de Monte Carlo y su error cae como $1/\\sqrt{N}$",
        ],
        [
            beat(
                "intro",
                ("", "Par 1 de Del ML al QML"),
                """En machine learning y en estadística estimas probabilidades contando muestras: eso es Monte Carlo.
                 [[q]]En un computador cuántico pasa lo mismo cada vez que mides: [[par]]cada shot es una muestra. Hoy vas a ver que son el mismo método.""",
                [
                    T("Monte Carlo ↔ shots", "title"),
                    Row(
                        Box("def", "Clásico", T("lanzar una moneda N veces y contar caras", "body")),
                        Box("def", "Cuántico", T("medir un qubit N veces y contar unos", "body")),
                        id="par",
                        hidden=True,
                        gap=30,
                    ),
                    T("el mismo estimador, el mismo error", "subtitle", id="s", hidden=True),
                ],
                [A("show", "par", at="q"), A("show", "s", at="par")],
            ),
            beat(
                "recuerda",
                ("", "Recuerda: Monte Carlo"),
                """Una moneda cargada sale cara con probabilidad p igual a un cuarto. [[sim]]Si la lanzas N veces y divides las caras entre N, obtienes una estimación de p.
                 [[err]]Esa estimación no es exacta: su error típico es la raíz de p por uno menos p, sobre N. [[cien]]Para tener la mitad de error necesitas cuatro veces más muestras.""",
                [
                    Code(MONEDA, id="c", size=22),
                    Out("10 0.2\n100 0.26\n1000 0.257\n10000 0.2489", id="o", hidden=True),
                    M(r"\hat p=\frac{k}{N},\qquad \sigma_{\hat p}=\sqrt{\frac{p(1-p)}{N}}", id="m", hidden=True, size=34),
                ],
                [A("show", "o", at="sim"), A("show", "m", at="err"), A("emph", "m", at="cien")],
                ask=numeric(
                    "Con $p = 0.25$ y $N = 100$ muestras, ¿cuál es el error típico $\\sigma_{\\hat p}$? (tres decimales)",
                    0.043,
                    "Correcto: $\\sqrt{0.25\\cdot 0.75/100}=\\sqrt{0.001875}\\approx 0.043$.",
                    tol=0.002,
                    hint="Calcula $p(1-p)/N$ y luego saca la raíz cuadrada.",
                ),
            ),
            beat(
                "born",
                ("", "El gemelo cuántico: la regla de Born"),
                """Ahora el qubit. Empieza en cero. [[ry]]Una rotación R Y de ángulo theta lo inclina en la esfera de Bloch.
                 [[born]]Al medirlo, la regla de Born dice que sale uno con probabilidad seno cuadrado de theta medios. Es una distribución de Bernoulli, igual que la moneda.
                 [[pi3]]Con theta igual a pi tercios, esa probabilidad vale exactamente un cuarto: hemos construido una moneda cargada cuántica.""",
                [
                    Circ(1, [G("ry", 0, p="π/3"), G("measure", 0, c=0)], clbits=1, id="q", maxw=420),
                    M(r"P(1)=\sin^2\!\big(\tfrac{\theta}{2}\big)", id="m", hidden=True, size=40),
                    M(r"\theta=\tfrac{\pi}{3}\ \Rightarrow\ P(1)=\sin^2\!\big(\tfrac{\pi}{6}\big)=\tfrac14", id="m2", hidden=True, size=34),
                ],
                [A("gate", "q", at="ry", i=0), A("show", "m", at="born"), A("show", "m2", at="pi3")],
                ask=choice(
                    "¿Con qué ángulo $\\theta$ el qubit es una moneda justa, $P(1)=1/2$?",
                    ["$\\theta=\\pi/4$", "$\\theta=\\pi/2$", "$\\theta=\\pi$", "$\\theta=2\\pi$"],
                    1,
                    "Correcto: $\\sin^2(\\pi/4)=1/2$. Es la misma superposición que produce una Hadamard.",
                    hint="Busca el ángulo para el que $\\sin^2(\\theta/2)=1/2$.",
                ),
            ),
            beat(
                "predice",
                ("", "Antes de medir"),
                """Antes de ejecutarlo, apuesta. Vamos a medir este qubit cien veces. [[cuantos]]¿Cuántos unos crees que saldrán?""",
                [Circ(1, [G("ry", 0, p="π/3"), G("measure", 0, c=0)], clbits=1, maxw=420)],
                ask=predict(
                    "Con $\\theta=\\pi/3$ y 100 shots, ¿cuántos `1` esperas?",
                    ["exactamente 25", "alrededor de 25, pero no exacto", "alrededor de 50", "alrededor de 75"],
                    "Anotado. Ahora midamos.",
                ),
            ),
            beat(
                "medir",
                ("", "Medir es muestrear"),
                """Ejecutamos con StatevectorSampler, con cien shots. [[res]]Salen veinticuatro unos y setenta y seis ceros. No veinticinco: veinticuatro.
                 [[mc]]Ese uno de diferencia no es un error del simulador. Es el error de Monte Carlo: con cien muestras, el error típico es de cuatro centésimas.""",
                [
                    Code(QUBIT, id="c", size=21),
                    Out("{'0': 76, '1': 24}", id="o", hidden=True),
                    Hist([["0", 76], ["1", 24]], id="h", grow=True, ymax=100, color="blue", hidden=True),
                ],
                [A("show", "o", at="res"), A("show", "h", at="res"), A("grow", "h", at="res", dur=1.2)],
            ),
            beat(
                "error",
                ("", "El error cae como 1/√N"),
                """Repetimos con más shots, veinte veces cada uno, y promediamos el error. [[tabla]]Con diez shots nos equivocamos en doce centésimas; con diez mil, en menos de cuatro milésimas.
                 [[ley]]La columna de la derecha es la fórmula de la moneda. Coinciden: el ruido de disparo de un computador cuántico es el error de Monte Carlo.""",
                [
                    Table(
                        ["shots N", "error medio medido", "$\\sqrt{p(1-p)/N}$"],
                        [
                            ["10", "0.120", "0.137"],
                            ["100", "0.043", "0.043"],
                            ["1000", "0.015", "0.014"],
                            ["10000", "0.004", "0.004"],
                        ],
                        id="t",
                        hidden=True,
                    ),
                    T("20 repeticiones por fila, $\\theta=\\pi/3$, StatevectorSampler", "note", id="n", hidden=True),
                ],
                [A("show", "t", at="tabla"), A("show", "n", at="tabla"), A("emph", "t", at="ley")],
                ask=choice(
                    "Quieres reducir a la mitad el error de muestreo de un circuito. ¿Cuántos shots necesitas?",
                    ["el doble", "cuatro veces más", "$\\sqrt2$ veces más", "diez veces más"],
                    1,
                    "Correcto: el error va como $1/\\sqrt N$, así que dividirlo entre 2 exige multiplicar $N$ por 4.",
                    hint="El error es proporcional a $1/\\sqrt N$.",
                ),
            ),
            beat(
                "mapa",
                ("", "El mapa del par"),
                """Resumamos el par en una tabla. [[fila]]Cada idea de Monte Carlo tiene su gemelo en el circuito. Guárdala: en el repaso de mañana te preguntaremos por ella.""",
                [
                    Table(
                        ["Monte Carlo (clásico)", "Circuito (cuántico)"],
                        [
                            ["una muestra aleatoria", "un shot"],
                            ["$N$ muestras", "`shots=N`"],
                            ["frecuencia $k/N$", "`counts['1'] / shots`"],
                            ["distribución de Bernoulli", "regla de Born, $\\sin^2(\\theta/2)$"],
                            ["error $\\sqrt{p(1-p)/N}$", "ruido de disparo (*shot noise*)"],
                        ],
                        id="t",
                        hidden=True,
                    )
                ],
                [A("show", "t", at="fila")],
            ),
            beat(
                "mision",
                ("", "Tu turno"),
                """Ahora te toca a ti. [[e1]]Completa dos funciones: una que prepara la moneda cuántica y otra que estima su probabilidad contando shots.
                 [[check]]Pulsa Comprobar: el código corre con Qiskit de verdad y los casos te dicen si acertaste.""",
                [
                    Exercise(
                        "q1-montecarlo/estimar-p",
                        "Completa `circuito(theta)`, que debe dar $P(1)=\\sin^2(\\theta/2)$, y `estimar_p(theta, shots)`, que devuelve la frecuencia de `1` en los conteos.",
                        level=2,
                        id="e1",
                        hidden=True,
                        hints=[
                            "La rotación que buscas es `qc.ry(theta, 0)`, antes de `measure_all()`.",
                            "Los conteos son un diccionario como `{'0': 76, '1': 24}`. Usa `conteos.get('1', 0)` por si no salió ningún `1`, y divide entre `shots`.",
                        ],
                    )
                ],
                [A("show", "e1", at="e1")],
            ),
        ],
        practice=[
            "Cambia la semilla de `StatevectorSampler` y comprueba que la frecuencia cambia, pero el error típico no.",
        ],
    )
]
