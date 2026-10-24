// Contenido de la constelación: habilidades, misiones, insignias y el perfil de demostración.
// Las posiciones del mapa son fijas para que el progreso no mueva nada.

export const GRUPOS = [
  { id: "clasico", nombre: "Estadística y ML clásico", y: 130 },
  { id: "cuantico", nombre: "Computación cuántica", y: 370 },
  { id: "puentes", nombre: "Retos y siguiente nivel", y: 590 },
];

// requiere: habilidades previas (flechas del mapa). puente: la flecha une un concepto clásico
// con su par cuántico.
export const HABILIDADES = [
  {
    id: "c-prob",
    nombre: "Probabilidad y frecuencia",
    corto: "Probabilidad",
    grupo: "clasico",
    x: 450,
    y: 130,
    requiere: [],
    desc: "Distinguir la probabilidad de un resultado de la frecuencia con que aparece en un número finito de intentos.",
    leccion: "q1-montecarlo",
  },
  {
    id: "c-mc",
    nombre: "Monte Carlo y error 1/√N",
    corto: "Monte Carlo",
    grupo: "clasico",
    x: 150,
    y: 130,
    requiere: ["c-prob"],
    desc: "Estimar una probabilidad contando muestras y saber cuánto se equivoca la estimación: σ = √(p(1−p)/N).",
    leccion: "q1-montecarlo",
  },
  {
    id: "c-rbf",
    nombre: "Similitud con kernel RBF",
    corto: "Kernel RBF",
    grupo: "clasico",
    x: 750,
    y: 130,
    requiere: ["c-prob"],
    desc: "Medir qué tan parecidos son dos puntos con e^(−γ‖x−x′‖²) y clasificar un punto nuevo por su parecido con los conocidos.",
    leccion: "q2-kernel",
  },
  {
    id: "q-born",
    nombre: "Regla de Born",
    corto: "Regla de Born",
    grupo: "cuantico",
    x: 450,
    y: 370,
    requiere: ["c-prob"],
    puente: { "c-prob": "distribución → amplitudes" },
    desc: "Preparar un qubit con una probabilidad de medir 1 elegida: P(1) = sin²(θ/2) tras una rotación R_Y(θ).",
    leccion: "q1-montecarlo",
  },
  {
    id: "q-shots",
    nombre: "Shots como muestras",
    corto: "Shots",
    grupo: "cuantico",
    x: 150,
    y: 370,
    requiere: ["c-mc", "q-born"],
    puente: { "c-mc": "Monte Carlo → shots" },
    desc: "Elegir cuántos shots pedir a un circuito según la precisión que necesitas: el ruido de disparo es error de Monte Carlo.",
    leccion: "q1-montecarlo",
  },
  {
    id: "q-kernel",
    nombre: "Kernel cuántico",
    corto: "Kernel cuántico",
    grupo: "cuantico",
    x: 750,
    y: 370,
    requiere: ["c-rbf", "q-born"],
    puente: { "c-rbf": "RBF → solapamiento" },
    desc: "Usar k(x, x′) = |⟨φ(x′)|φ(x)⟩|² de un feature map para clasificar, y ajustar la escala de los datos como un hiperparámetro.",
    leccion: "q2-kernel",
  },
  {
    id: "t-kshots",
    nombre: "Estimar un kernel con shots",
    corto: "Kernel con shots",
    grupo: "puentes",
    x: 450,
    y: 590,
    requiere: ["q-shots", "q-kernel"],
    desc: "Combinar los dos pares: decidir cuántos shots hacen falta para que un kernel estimado clasifique bien con alta fiabilidad.",
  },
  {
    id: "g-grad",
    nombre: "Gradiente ↔ parameter-shift",
    corto: "Gradientes",
    grupo: "puentes",
    x: 750,
    y: 590,
    requiere: ["t-kshots"],
    proximamente: true,
    desc: "Nivel 3 del curso, en preparación: descenso de gradiente y la regla de parameter-shift para circuitos variacionales.",
  },
];

export const ESTADOS = {
  bloqueada: { nombre: "Bloqueada", marca: "🔒" },
  disponible: { nombre: "Disponible", marca: "○" },
  explorando: { nombre: "En exploración", marca: "◐" },
  practicada: { nombre: "Practicada", marca: "●" },
  demostrada: { nombre: "Demostrada en un reto", marca: "★" },
  proximamente: { nombre: "Próximamente", marca: "…" },
};

export const LECCIONES = {
  "q1-montecarlo": "1.1 · Monte Carlo ↔ shots",
  "q2-kernel": "2.1 · SVM con kernel RBF ↔ kernel cuántico",
};

// Cada misión declara su diseño (qué consigue el jugador, qué decide, qué ve, qué aprende y qué
// desbloquea) antes de su lógica, que vive en misiones.js.
export const MISIONES = [
  {
    id: "m1",
    titulo: "La moneda cuántica",
    puente: "Distribución de probabilidad → regla de Born",
    demuestra: ["c-prob", "q-born"],
    requiere: [],
    leccion: "q1-montecarlo",
    minutos: 3,
    diseno: {
      objetivo:
        "Fabricar con un qubit una moneda cargada que salga 1 con la probabilidad que te piden.",
      decision:
        "El ángulo θ de la rotación y cuántos 1 crees que saldrán antes de medir.",
      visual:
        "El qubit se inclina, los 200 shots caen uno a uno en sus columnas y la barra teórica se compara con la observada.",
      aprende:
        "P(1) = sin²(θ/2) es una probabilidad; la frecuencia medida oscila a su alrededor.",
      desbloquea:
        "«Cazar el ruido» y «Detector de parecidos»: eliges por dónde seguir.",
    },
    variantes: [
      { objetivo: 0.25, nombre: "moneda del 25 %" },
      { objetivo: 0.75, nombre: "moneda del 75 %" },
      { objetivo: 0.1, nombre: "moneda del 10 %" },
      { objetivo: 0.9, nombre: "moneda del 90 %" },
    ],
  },
  {
    id: "m2",
    titulo: "Cazar el ruido",
    puente: "Monte Carlo → shots",
    demuestra: ["c-mc", "q-shots"],
    requiere: ["m1"],
    leccion: "q1-montecarlo",
    minutos: 4,
    diseno: {
      objetivo:
        "Estimar la probabilidad de tu moneda con un error típico pequeño sin pasarte del presupuesto de shots.",
      decision: "Cuántos shots pedir por estimación: más precisión cuesta más.",
      visual:
        "30 estimaciones repetidas se dispersan alrededor del valor real y cada ejecución añade un punto a la curva del error.",
      aprende:
        "El error cae como 1/√N: dividirlo entre 2 exige 4 veces más shots.",
      desbloquea:
        "La mitad del reto de transferencia (la otra mitad es «Detector de parecidos»).",
    },
    variantes: [
      { tol: 0.02, presupuesto: 600, nombre: "error ≤ 0,02 con 600 shots" },
      { tol: 0.03, presupuesto: 300, nombre: "error ≤ 0,03 con 300 shots" },
      { tol: 0.015, presupuesto: 1000, nombre: "error ≤ 0,015 con 1000 shots" },
    ],
  },
  {
    id: "m3",
    titulo: "Detector de parecidos",
    puente: "SVM con kernel RBF → kernel cuántico",
    demuestra: ["c-rbf", "q-kernel"],
    requiere: ["m1"],
    leccion: "q2-kernel",
    minutos: 4,
    diseno: {
      objetivo:
        "Clasificar 8 puntos nuevos de dos lunas comparándolos con 12 puntos conocidos mediante un kernel cuántico.",
      decision:
        "La escala con la que entran los datos al circuito, que hace el papel de γ en el RBF, y cuántas capas tiene el feature map.",
      visual:
        "El plano se colorea con la clase que predice el kernel y cada punto de prueba muestra si acertó.",
      aprende:
        "Un kernel cuántico mide parecido entre estados; su escala es un hiperparámetro y no garantiza ganar al clásico.",
      desbloquea:
        "La mitad del reto de transferencia (la otra mitad es «Cazar el ruido»).",
    },
    // Con reps = 2 ninguna escala llega a 7 de 8: queda como opción para explorar, no como variante.
    variantes: [
      { meta: 7, nombre: "acierta 7 de 8" },
      { meta: 8, nombre: "acierta los 8" },
    ],
  },
  {
    id: "t1",
    titulo: "Reto: el kernel con ruido",
    puente: "Monte Carlo + kernel cuántico",
    demuestra: ["t-kshots"],
    requiere: ["m2", "m3"],
    reto: true,
    minutos: 4,
    diseno: {
      objetivo:
        "En hardware el kernel se estima contando shots. Decide cuántos pagar para que un punto se clasifique bien el 95 % de las veces.",
      decision: "Los shots por estimación, con un presupuesto de 500.",
      visual:
        "Dos nubes de 20 estimaciones del kernel y una fila de 20 aciertos o fallos.",
      aprende:
        "El error de Monte Carlo también afecta a un kernel estimado: la diferencia entre similitudes debe superar su ruido.",
      desbloquea: "La insignia «Puente completo» y el adelanto del nivel 3.",
    },
    variantes: [{ presupuesto: 500, nombre: "presupuesto de 500 shots" }],
  },
];

export const INSIGNIAS = [
  {
    id: "primera-medida",
    nombre: "Primera medida",
    icono: "⚛",
    criterio: "Ejecutaste tu primer circuito en el simulador de Qiskit.",
  },
  {
    id: "prediccion-certera",
    nombre: "Ojo de Monte Carlo",
    icono: "◎",
    criterio:
      "En «La moneda cuántica», tu predicción quedó a menos de un error típico de lo que midió Qiskit.",
  },
  {
    id: "sin-pistas",
    nombre: "Por tu cuenta",
    icono: "✦",
    criterio: "Superaste una misión sin abrir ninguna pista.",
  },
  {
    id: "ahorro",
    nombre: "Ahorro de shots",
    icono: "⌁",
    criterio:
      "En «Cazar el ruido», usaste como mucho un 10 % más de shots que el mínimo necesario.",
  },
  {
    id: "ajuste-fino",
    nombre: "Ajuste fino",
    icono: "◇",
    criterio:
      "En «Detector de parecidos», clasificaste bien los 8 puntos de prueba.",
  },
  {
    id: "puente",
    nombre: "Puente completo",
    icono: "⟷",
    criterio: "Superaste el reto de transferencia.",
  },
];

export const XP = {
  prediccion: 10,
  experimento: 10,
  superada: 50,
  variante: 20,
};

export const AVATARES = ["ψ", "⚛", "∿", "θ", "◎", "✦"];
export const COLORES = ["acc", "acc2", "acc3", "blue", "violet"];

// Datos de las dos lunas (make_moons con ruido 0.08, escaladas a [0, 1]): x, y, clase.
export const LUNAS = {
  train: [
    [0.21, 0.99, 0],
    [0.44, 0.24, 1],
    [0.32, 0.6, 1],
    [0.69, 0.37, 0],
    [0.92, 0.25, 1],
    [0.98, 0.5, 1],
    [0.75, 0.03, 1],
    [0.11, 0.86, 0],
    [0.29, 1.0, 0],
    [0.98, 0.52, 1],
    [0.08, 0.78, 0],
    [0.3, 0.74, 1],
  ],
  test: [
    [0.0, 0.42, 0],
    [0.57, 0.68, 0],
    [0.96, 0.23, 1],
    [0.36, 0.39, 1],
    [0.29, 0.94, 0],
    [0.34, 0.43, 1],
    [0.14, 0.79, 0],
    [0.03, 0.71, 0],
  ],
};

// Reto de transferencia: el punto a clasificar y un representante de cada clase, con escala 1.5.
export const RETO_KERNEL = {
  escala: 1.5,
  punto: [0.57, 0.68],
  claseA: [0.29, 1.0],
  claseB: [0.92, 0.25],
};

// Perfil de ejemplo para enseñar la vista pública sin progreso propio. No es un usuario real.
export const DEMO = {
  demo: true,
  perfil: {
    alias: "Ada (perfil de demostración)",
    avatar: "ψ",
    color: "acc2",
    bio: "Estudiante de 17 años. Me interesa cómo se conectan la estadística y los qubits.",
  },
  insignias: ["primera-medida", "prediccion-certera", "ahorro", "puente"],
  evidencias: [
    {
      m: "m1",
      v: 0,
      at: "2026-10-20",
      h: 0,
      pred: 50,
      p: { theta: 60, shots: 200, seed: 3 },
      r: { p1: 0.25, unos: 52 },
    },
    {
      m: "m2",
      v: 0,
      at: "2026-10-21",
      h: 1,
      pred: 400,
      p: { shots: 500, reps: 30, seed: 100 },
      r: { sigmaTeo: 0.0194, sigmaObs: 0.0201, media: 0.2513 },
    },
    {
      m: "t1",
      v: 0,
      at: "2026-10-22",
      h: 2,
      pred: 300,
      p: { shots: 250, reps: 20 },
      r: { ka: 0.5582, kb: 0.478, fiab: 0.964, aciertos: 19 },
    },
  ],
};
