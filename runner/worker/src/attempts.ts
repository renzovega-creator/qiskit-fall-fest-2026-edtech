import { unixSeconds } from "./account.ts";
import { EXERCISE } from "./contract.ts";

// Lo que el Worker anota de una ejecución. Sale del JSON del contenedor, que
// califica el código: la página no puede falsear un resultado. Nunca lleva el
// código, `stdout`, el texto del error ni el `message` de un caso, que pueden
// repetir lo que escribió el alumno.
export interface Attempt {
  exercise: string;
  mode: "run" | "check";
  outcome: "pass" | "fail" | "error" | "timeout";
  failed: string[];
  errorKind: string | null;
  hints: number;
  ms: number;
  codeBytes: number;
}

const MAX_FAILED = 50;
const MAX_CASE_CHARS = 120;
const KILLED = new Set(["time", "memory", "disk", "output", "scan"]);
// El nombre de una excepción de Python; cualquier otro texto de error es «other».
const EXCEPTION = /^([A-Za-z]{1,40}(?:Error|Exception))\b/;

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

// `request` es lo que la página mandó (solo `mode` y `exercise` se usan) y `result`
// el cuerpo con que respondió el contenedor. Devuelve null si no hay nada que anotar.
export function toAttempt(
  request: { mode?: unknown; exercise?: unknown },
  codeBytes: number,
  hintsHeader: string | null,
  result: unknown,
): Attempt | null {
  const { mode, exercise } = request;
  if (mode !== "run" && mode !== "check") return null;
  if (typeof exercise !== "string" || !EXERCISE.test(exercise)) return null;
  if (!isRecord(result) || typeof result.passed !== "boolean") return null;

  const killed =
    typeof result.killed === "string" && KILLED.has(result.killed)
      ? result.killed
      : null;
  let outcome: Attempt["outcome"] = result.passed ? "pass" : "fail";
  let errorKind: string | null = null;
  if (killed === "time") {
    outcome = "timeout";
  } else if (killed) {
    outcome = "error";
    errorKind = `killed_${killed}`;
  } else if (typeof result.error === "string") {
    outcome = "error";
    errorKind = EXCEPTION.exec(result.error)?.[1] ?? "other";
  }

  const failed = Array.isArray(result.tests)
    ? result.tests
        .filter(
          (test) =>
            isRecord(test) &&
            test.passed === false &&
            typeof test.name === "string",
        )
        .slice(0, MAX_FAILED)
        .map((test) => (test.name as string).slice(0, MAX_CASE_CHARS))
    : [];
  const hints = /^[0-9]$/.test(hintsHeader ?? "") ? Number(hintsHeader) : 0;
  const ms =
    typeof result.ms === "number" && Number.isFinite(result.ms)
      ? Math.max(0, Math.round(result.ms))
      : 0;
  return { exercise, mode, outcome, failed, errorKind, hints, ms, codeBytes };
}

export async function recordAttempt(
  db: D1Database,
  userId: string | null,
  attempt: Attempt,
  now: number,
): Promise<void> {
  await db
    .prepare(
      `INSERT INTO attempts (at, user_id, exercise, mode, outcome, failed, error_kind, hints, ms, code_bytes)
       VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)`,
    )
    .bind(
      unixSeconds(now),
      userId,
      attempt.exercise,
      attempt.mode,
      attempt.outcome,
      JSON.stringify(attempt.failed),
      attempt.errorKind,
      attempt.hints,
      attempt.ms,
      attempt.codeBytes,
    )
    .run();
}
