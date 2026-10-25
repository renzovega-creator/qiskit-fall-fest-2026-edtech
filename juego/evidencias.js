// Convierte una evidencia guardada (misión, variante, parámetros y resultados) en un texto que
// entienda alguien que no conoce el juego: qué problema resolvió, qué hizo y con qué ayuda, qué
// conceptos aplicó, qué obtuvo y cómo reproducirlo.
import { MISIONES } from "./datos.js";
import { fmt, pct } from "./dom.js";
import { habilidad } from "./estado.js";
import { BACKEND, codigo } from "./qiskit.js";

const variante = (e) => MISIONES.find((m) => m.id === e.m).variantes[e.v] ?? {};

const TEXTOS = {
  m1: (e, v) => ({
    titulo: `Preparó un qubit que da 1 con probabilidad ${pct(v.objetivo)}`,
    problema: `Fabricar una «moneda cargada» cuántica: un qubit que, al medirlo, dé 1 el ${pct(v.objetivo)} de las veces.`,
    hizo: `Eligió el ángulo θ = ${e.p.theta}° para la rotación R_Y${e.pred == null ? "" : ` y, antes de medir, predijo ${e.pred} unos en ${e.p.shots} shots`}.`,
    resultado: `Probabilidad teórica P(1) = ${fmt(e.r.p1, 3)} (objetivo ${fmt(v.objetivo, 2)} ± 0,02). Frecuencia observada: ${e.r.unos} unos de ${e.p.shots} shots (${pct(e.r.unos / e.p.shots, 1)}).`,
  }),
  m2: (e, v) => ({
    titulo: `Eligió cuántos shots necesita una estimación con error típico ≤ ${fmt(v.tol, 3)}`,
    problema: `Estimar la probabilidad P(1) = 0,25 de un qubit con un error típico de como mucho ${fmt(v.tol, 3)}, sin pasar de ${v.presupuesto} shots por estimación.`,
    hizo: `Eligió N = ${e.p.shots} shots${e.pred == null ? "" : ` (había predicho ${e.pred})`} y comprobó la dispersión con ${e.p.reps} estimaciones independientes.`,
    resultado: `Error típico teórico √(p(1−p)/N) = ${fmt(e.r.sigmaTeo, 4)}; dispersión observada en Qiskit = ${fmt(e.r.sigmaObs, 4)}; media de las estimaciones = ${fmt(e.r.media, 3)}.`,
  }),
  m3: (e, v) => ({
    titulo: `Resolvió un reto de clasificación con un kernel cuántico (${e.r.aciertos} de 8 aciertos)`,
    problema: `Clasificar 8 puntos nuevos de dos «lunas» comparándolos con 12 puntos conocidos, con un kernel cuántico basado en el feature map ZZ. Meta: ${v.meta} de 8.`,
    hizo: `Ajustó la escala de los datos a ${fmt(e.p.escala, 2)} (el equivalente de γ en un kernel RBF) con un feature map de ${e.p.reps} ${e.p.reps === 1 ? "capa" : "capas"}.`,
    resultado: `${e.r.aciertos} de 8 puntos de prueba bien clasificados; contraste medio entre clases ${fmt(e.r.contraste, 3)}. Un kernel RBF clásico acierta 8 de 8 en estos datos: no hay ventaja cuántica.`,
  }),
  t1: (e) => ({
    titulo:
      "Calculó los shots necesarios para estimar un kernel cuántico con 95 % de fiabilidad",
    problema:
      "Reto de transferencia: en hardware, el kernel se estima contando shots. Elegir cuántos shots pagar para que un punto se clasifique bien al menos el 95 % de las veces, con un presupuesto de 500.",
    hizo: `Combinó el error de Monte Carlo con el kernel cuántico y eligió N = ${e.p.shots} shots por estimación${e.pred == null ? "" : ` (había predicho ${e.pred})`}.`,
    resultado: `Kernels exactos k_A = ${fmt(e.r.ka, 3)} y k_B = ${fmt(e.r.kb, 3)}; fiabilidad teórica ${pct(e.r.fiab, 1)}; en ${e.p.reps} repeticiones simuladas acertó ${e.r.aciertos}.`,
  }),
};

export function describir(e) {
  const m = MISIONES.find((x) => x.id === e.m);
  const t = TEXTOS[e.m](e, variante(e));
  return {
    ...t,
    mision: m,
    fecha: e.at,
    ayuda:
      e.h > 0
        ? `Lo resolvió con ${e.h} ${e.h === 1 ? "pista" : "pistas"} del juego.`
        : "Lo resolvió sin pistas.",
    conceptos: m.demuestra.map((id) => habilidad(id).nombre),
    ejecucion: e.demo
      ? "Demostración: resultado precomputado con Qiskit. Se consultaron datos de ejemplo; no se ejecutó código nuevo ni hardware cuántico."
      : `${BACKEND}. No se ejecutó en hardware cuántico.`,
    codigo: codigo[e.m](e.p),
  };
}
