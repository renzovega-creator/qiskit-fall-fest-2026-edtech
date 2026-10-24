"""Nivel 2 · Kernels: SVM con kernel RBF ↔ kernel cuántico."""

from lib import (
    A,
    Box,
    Circ,
    Code,
    Exercise,
    G,
    M,
    Out,
    Row,
    T,
    Table,
    beat,
    choice,
    lesson,
    predict,
)

CLASICO = """
from sklearn.datasets import make_moons
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.svm import SVC

X, y = make_moons(n_samples=60, noise=0.15, random_state=0)
X = MinMaxScaler((0, 1)).fit_transform(X)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=0)

svm = SVC(kernel="rbf").fit(Xtr, ytr)
print(svm.score(Xte, yte))
"""

CUANTICO = """
from qiskit.circuit.library import zz_feature_map
from qiskit_machine_learning.algorithms import QSVC
from qiskit_machine_learning.kernels import FidelityStatevectorKernel

mapa = zz_feature_map(2, reps=1)              # x → |φ(x)⟩, 2 qubits
kernel = FidelityStatevectorKernel(feature_map=mapa)

qsvc = QSVC(quantum_kernel=kernel).fit(Xtr, ytr)
print(qsvc.score(Xte, yte))
"""

LESSONS = [
    lesson(
        "q2-kernel",
        "SVM con kernel RBF ↔ kernel cuántico",
        "Una SVM solo mira similitudes entre puntos; un circuito puede medir esas similitudes como solapamientos de estados.",
        [
            "recordar que una SVM con kernel solo necesita $k(x, x')$ entre pares de puntos",
            "definir el kernel cuántico $k(x,x')=|\\langle\\varphi(x')|\\varphi(x)\\rangle|^2$ con un feature map",
            "comparar con honestidad `SVC` y `QSVC` en el mismo dataset",
        ],
        [
            beat(
                "intro",
                ("", "Par 2 de Del ML al QML"),
                """Una máquina de vectores de soporte con kernel separa clases que no se pueden separar con una recta.
                 [[truco]]Su truco es que nunca mira los puntos directamente: solo necesita qué tan parecidos son entre sí. [[par]]Hoy reemplazamos esa medida de parecido por un circuito.""",
                [
                    T("SVM con kernel ↔ kernel cuántico", "title"),
                    Row(
                        Box("def", "Clásico", T("$k(x,x')=e^{-\\gamma\\|x-x'\\|^2}$ (RBF)", "body")),
                        Box("def", "Cuántico", T("$k(x,x')=|\\langle\\varphi(x')|\\varphi(x)\\rangle|^2$", "body")),
                        id="par",
                        hidden=True,
                        gap=30,
                    ),
                    T("la SVM no cambia: solo cambia quién calcula las similitudes", "subtitle", id="s", hidden=True),
                ],
                [A("show", "s", at="truco"), A("show", "par", at="par")],
            ),
            beat(
                "recuerda",
                ("", "Recuerda: el kernel RBF"),
                """El kernel RBF vale uno cuando dos puntos coinciden y decae con la distancia. [[ej]]Por ejemplo, con gamma un medio, dos puntos muy cercanos dan casi uno, y dos puntos lejanos dan sesenta y cinco centésimas.
                 [[moons]]Con este kernel, una SVM clasifica las dos lunas de scikit-learn: [[acc]]acierta los quince puntos de prueba.""",
                [
                    Code(CLASICO, id="c", size=19),
                    M(r"k_{\rm RBF}(x,x')=e^{-\gamma\|x-x'\|^2}", id="m", size=34),
                    T("con $\\gamma=0.5$: $k([0.2,0.7],[0.25,0.65])=0.998$ y $k([0.2,0.7],[0.9,0.1])=0.654$", "note", id="n", hidden=True),
                    Out("1.0", id="o", hidden=True),
                ],
                [A("show", "n", at="ej"), A("hl", "c", at="moons", lines=[10, 11]), A("show", "o", at="acc")],
            ),
            beat(
                "feature",
                ("", "El gemelo cuántico: un feature map"),
                """En el lado cuántico, un circuito lleva cada punto x a un estado de dos qubits, phi de x. Es un feature map. [[zz]]Aquí usamos el ZZ feature map: Hadamards, rotaciones con los datos y un entrelazamiento entre los dos qubits.
                 [[kern]]El kernel cuántico es el solapamiento al cuadrado entre dos de esos estados. [[mide]]En hardware se estima preparando phi de x, deshaciendo phi de x prima y contando cuántas veces sale cero cero: otra vez, Monte Carlo.""",
                [
                    Circ(
                        2,
                        [
                            G("h", 0),
                            G("h", 1),
                            G("p", 0, p="2x₀"),
                            G("p", 1, p="2x₁"),
                            G("cx", 0, 1),
                            G("p", 1, p="2(π−x₀)(π−x₁)"),
                            G("cx", 0, 1),
                        ],
                        id="q",
                        maxw=640,
                    ),
                    M(r"k(x,x')=\big|\langle\varphi(x')|\varphi(x)\rangle\big|^2", id="m", hidden=True, size=38),
                    T("$k(x,x') = P(00)$ tras $U_\\varphi(x)$ y luego $U_\\varphi(x')^\\dagger$", "note", id="n", hidden=True),
                ],
                [A("emph", "q", at="zz"), A("show", "m", at="kern"), A("show", "n", at="mide")],
                ask=choice(
                    "Para cualquier punto $x$, ¿cuánto vale el kernel cuántico $k(x, x)$?",
                    ["0", "1/2", "1", "depende del feature map"],
                    2,
                    "Correcto: $|\\langle\\varphi(x)|\\varphi(x)\\rangle|^2 = 1$ porque el estado está normalizado. Igual que el RBF en $x = x'$.",
                    hint="Es el solapamiento de un estado normalizado consigo mismo.",
                ),
            ),
            beat(
                "predice",
                ("", "Antes de comparar"),
                """Mismo dataset, mismos cuarenta y cinco puntos de entrenamiento, misma SVM. Solo cambiamos el kernel. [[quien]]¿Quién crees que clasifica mejor los quince puntos de prueba?""",
                [Code(CUANTICO, id="c", size=20)],
                ask=predict(
                    "En las dos lunas, ¿quién acierta más?",
                    ["el kernel cuántico, por mucho", "empatan", "el RBF clásico", "ninguno pasa del 60 %"],
                    "Anotado. Veamos el resultado.",
                ),
            ),
            beat(
                "compara",
                ("", "El resultado, sin maquillaje"),
                """El RBF acierta los quince. El kernel cuántico acierta catorce: noventa y tres por ciento. [[honesto]]En este problema, el clásico gana. Usar un circuito no da ventaja por sí solo.
                 [[escala]]Y hay una trampa: si escalamos los datos entre menos uno y uno y repetimos el feature map dos veces, el kernel cuántico cae a cincuenta y tres por ciento, casi al azar. [[gamma]]La escala de los datos hace el papel de gamma en el RBF: es un hiperparámetro.""",
                [
                    Table(
                        ["modelo", "kernel", "exactitud en prueba (15 puntos)"],
                        [
                            ["`SVC`", "RBF", "1.00"],
                            ["`QSVC`", "ZZ, `reps=1`, datos en [0, 1]", "0.93"],
                            ["`QSVC`", "ZZ, `reps=2`, datos en [−1, 1]", "0.53"],
                        ],
                        id="t",
                    ),
                    T("`make_moons(n_samples=60, noise=0.15, random_state=0)`, simulación exacta del estado", "note", id="n"),
                ],
                [A("emph", "t", at="honesto")],
                ask=choice(
                    "En un `QSVC`, ¿qué parte calcula el circuito cuántico?",
                    [
                        "las similitudes $k(x, x')$ entre pares de puntos",
                        "la optimización que encuentra los vectores de soporte",
                        "ambas",
                        "la predicción final, sin pasar por la SVM",
                    ],
                    0,
                    "Correcto: el circuito solo da la matriz de kernel. La SVM que la usa es la misma de scikit-learn.",
                    hint="`QSVC` hereda de `SVC` de scikit-learn.",
                ),
            ),
            beat(
                "mapa",
                ("", "El mapa del par"),
                """El par completo en una tabla. [[fila]]La SVM es la misma; lo que cambia es el espacio donde medimos el parecido.""",
                [
                    Table(
                        ["SVM con kernel (clásico)", "QSVC (cuántico)"],
                        [
                            ["truco del kernel", "estados en el espacio de Hilbert"],
                            ["$e^{-\\gamma\\|x-x'\\|^2}$", "$|\\langle\\varphi(x')|\\varphi(x)\\rangle|^2$"],
                            ["$\\gamma$ (ancho del kernel)", "escala de los datos y `reps` del feature map"],
                            ["matriz de Gram", "`kernel.evaluate(X)`"],
                            ["`SVC`", "`QSVC` (la misma optimización)"],
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
                """Ahora construye tú el kernel cuántico, sin la biblioteca. [[e1]]Tienes el feature map y una función que da el estado de cada punto. Te falta una línea: el solapamiento al cuadrado.
                 [[check]]Los casos comparan tu kernel con el de Qiskit Machine Learning.""",
                [
                    Exercise(
                        "q2-kernel/kernel-fidelidad",
                        "Completa `kernel(x, y)`: debe devolver $|\\langle\\varphi(y)|\\varphi(x)\\rangle|^2$ usando `estado(x)` y `estado(y)`.",
                        level=2,
                        id="e1",
                        hidden=True,
                        hints=[
                            "`Statevector` tiene el método `inner`: `estado(y).inner(estado(x))` es $\\langle\\varphi(y)|\\varphi(x)\\rangle$, un número complejo.",
                            "Toma el módulo con `abs(...)`, elévalo al cuadrado y conviértelo con `float(...)`.",
                        ],
                    )
                ],
                [A("show", "e1", at="e1")],
            ),
        ],
        practice=[
            "Cambia `reps` del feature map a 2 y 3 y mira cómo cambia la exactitud del `QSVC`.",
        ],
    )
]
