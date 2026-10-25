"""Nivel 2 · Kernels: SVM con kernel RBF ↔ kernel cuántico."""

from lib import (
    A,
    Box,
    Circ,
    Code,
    Exercise,
    G,
    KernelMap,
    M,
    Out,
    Row,
    T,
    Table,
    beat,
    choice,
    lesson,
    predict,
    task,
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

# Los 60 puntos de make_moons(n_samples=60, noise=0.15, random_state=0) llevados a [0, 1]², como en
# CLASICO, con su clase. Los dibuja el mapa de kernels de la lección.
LUNAS = [
    [0.0, 0.466, 0], [0.364, 0.231, 1], [0.977, 0.659, 1], [0.066, 0.41, 0], [0.413, 0.843, 0], [0.718, 0.392, 0],
    [0.297, 0.454, 1], [0.986, 0.507, 1], [0.52, 0.171, 1], [0.03, 0.81, 0], [0.744, 0.515, 0], [0.554, 0.695, 0],
    [0.395, 0.538, 1], [0.552, 0.153, 1], [0.362, 0.509, 1], [0.608, 0.043, 1], [0.811, 0.118, 1], [0.575, 0.688, 0],
    [0.455, 0.827, 0], [0.368, 0.374, 1], [0.844, 0.258, 1], [0.015, 0.307, 0], [0.626, 0.138, 1], [0.906, 0.217, 1],
    [0.168, 0.821, 0], [0.918, 0.402, 1], [0.116, 0.492, 0], [0.301, 0.712, 0], [0.59, 0.706, 0], [0.36, 0.596, 1],
    [0.308, 0.889, 0], [0.889, 0.203, 1], [0.18, 0.723, 0], [0.978, 0.178, 1], [0.512, 0.639, 0], [0.4, 0.87, 0],
    [0.076, 0.707, 0], [0.406, 0.14, 1], [0.236, 1.0, 0], [0.767, 0.069, 1], [0.742, 0.01, 1], [1.0, 0.508, 1],
    [0.492, 0.052, 1], [0.61, 0.341, 0], [0.318, 0.95, 0], [0.702, 0.037, 1], [0.13, 0.59, 0], [0.537, 0.646, 0],
    [0.113, 0.67, 0], [0.359, 0.266, 1], [0.082, 0.582, 0], [0.188, 0.747, 0], [0.486, 0.847, 0], [0.383, 0.163, 1],
    [0.933, 0.348, 1], [0.697, 0.492, 0], [0.67, 0.383, 0], [0.982, 0.32, 1], [0.718, 0.105, 1], [0.689, 0.0, 1],
]

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
                    Code(
                        CLASICO,
                        id="c",
                        # Necesita scikit-learn y Qiskit Machine Learning, que no son dependencias del
                        # proyecto: verify.py no lo ejecuta. Las cifras salen de numeros.py.
                        norun=True,
                        size=19,
                        notes={
                            6: "Dos medias lunas entrelazadas: 60 puntos con ruido que ninguna recta separa.",
                            7: "Lleva cada coordenada a $[0, 1]$. Esta escala importa: en el lado cuántico, los datos entran como ángulos.",
                            8: "45 puntos para entrenar y 15 para probar (`test_size=0.25`).",
                            10: "`SVC` con kernel RBF. `gamma` queda en su valor por defecto, `'scale'`, que lo ajusta a la varianza de los datos.",
                            11: "`score` da la exactitud: la fracción de puntos de prueba bien clasificados.",
                        },
                    ),
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
                "explora",
                ("", "Explora los dos kernels"),
                """Ahora explora tú los dos kernels sobre las lunas. [[clic]]Haz clic en cualquier lugar: el círculo rojo se mueve allí, y cada mapa pinta qué tan parecido es cada punto del cuadrado a ese lugar, más intenso cuanto más parecido.
                 [[lados]]A la izquierda, el kernel RBF; a la derecha, el kernel cuántico del feature map que acabas de ver.
                 [[escala]]Después mueve la escala de los datos y mira qué le pasa al mapa cuántico.""",
                [KernelMap(LUNAS, gamma=5, scale=1, reps=1, ref=[0.3, 0.6], id="k")],
                ask=task(
                    "Haz clic en **tres lugares** de los mapas. Luego sube la **escala de los datos** a 3 o más.",
                    "k",
                    dict(clicks=3, scale=[3, 100]),
                    "Con la escala grande, el mapa cuántico se vuelve un mosaico: puntos vecinos dejan de parecerse y la SVM ya no ve la forma de las lunas. La escala de los datos es un hiperparámetro, como $\\gamma$ en el RBF.",
                    hint="Los deslizadores están debajo de los mapas. Arrastra «escala de los datos» hacia la derecha.",
                ),
            ),
            beat(
                "predice",
                ("", "Antes de comparar"),
                """Mismo dataset, mismos cuarenta y cinco puntos de entrenamiento, misma SVM. Solo cambiamos el kernel. [[quien]]¿Quién crees que clasifica mejor los quince puntos de prueba?""",
                [
                    Code(
                        CUANTICO,
                        id="c",
                        # Necesita scikit-learn y Qiskit Machine Learning, que no son dependencias del
                        # proyecto: verify.py no lo ejecuta. Las cifras salen de numeros.py.
                        norun=True,
                        size=20,
                        notes={
                            5: "El feature map del paso anterior: 2 qubits, uno por coordenada, y una sola repetición.",
                            6: "Calcula $|\\langle\\varphi(x')|\\varphi(x)\\rangle|^2$ con el vector de estado exacto, sin shots.",
                            8: "La misma SVM de scikit-learn, con otro kernel. `Xtr` e `ytr` son los del código clásico.",
                        },
                    )
                ],
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
