import { unixSeconds } from "./account.ts";
import { EXERCISE } from "./contract.ts";

// El progreso de un alumno, con la forma que la página manda y recibe. Las claves
// de `kv` son las de localStorage; `done` es `qiskit:done` y `exercises` son los
// `qiskit:exercise:<id>`. Lo que no está aquí (preferencias, `reflect`) no sale del
// navegador.
export interface ExerciseState {
  // Solo el alumno que lo permite manda su código.
  code?: string | null;
  hints: number;
  checks: number;
  passed: boolean;
  // Milisegundos Unix de la última edición: gana el código más reciente.
  at: number;
}

export interface Progress {
  done: string[];
  exercises: Record<string, ExerciseState>;
  kv: Record<string, unknown>;
}

export const MAX_CODE_BYTES = 20_000;
const MAX_DONE = 500;
const MAX_EXERCISES = 100;
const MAX_KV_KEYS = 2000;
const MAX_KV_BYTES = 64_000;
const MAX_ITEMS = 1000;

const LESSON = /^[a-z0-9][a-z0-9-]{0,59}$/;

const isInt = (value: unknown): value is number =>
  typeof value === "number" && Number.isSafeInteger(value) && value >= 0;
const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);
const list = (value: unknown, accepts: (item: unknown) => boolean): value is unknown[] =>
  Array.isArray(value) && value.length <= MAX_ITEMS && value.every(accepts);

// Cada familia de claves de `kv`: qué forma tiene su valor y cómo se juntan el
// guardado y el que llega. La unión y el máximo no dependen del orden, así que dos
// pestañas que se sincronizan acaban en el mismo estado.
interface Family {
  key: RegExp;
  valid(value: unknown): boolean;
  merge(stored: unknown, incoming: unknown): unknown;
}

const union = (stored: unknown, incoming: unknown) =>
  [...new Set([...(stored as unknown[]), ...(incoming as unknown[])])].sort((a, b) =>
    typeof a === "number" && typeof b === "number" ? a - b : String(a).localeCompare(String(b)),
  );

const isBox = (value: unknown) =>
  isRecord(value) &&
  isInt(value.box) &&
  value.box <= 20 &&
  typeof value.due === "number" &&
  Number.isFinite(value.due);

const FAMILIES: Family[] = [
  {
    key: /^qiskit:heard:[a-z0-9-]{1,60}$/,
    valid: (value) => list(value, isInt),
    merge: union,
  },
  {
    key: /^qiskit:hitos$/,
    valid: (value) => list(value, isInt),
    merge: union,
  },
  {
    key: /^qiskit:misiones$/,
    valid: (value) =>
      list(value, (item) => typeof item === "string" && /^[A-Za-z0-9_./-]{1,100}$/.test(item)),
    merge: union,
  },
  {
    key: /^qiskit:pos:[a-z0-9-]{1,60}$/,
    valid: isInt,
    merge: (stored, incoming) => Math.max(stored as number, incoming as number),
  },
  {
    // Una apuesta no se cambia: la primera que se guarda es la que vale.
    key: /^qiskit:predict:[a-z0-9-]{1,60}:[A-Za-z0-9_-]{1,60}$/,
    valid: isInt,
    merge: (stored) => stored,
  },
  {
    key: /^qiskit:repaso$/,
    valid: (value) =>
      isRecord(value) &&
      Object.keys(value).length <= MAX_ITEMS &&
      Object.entries(value).every(
        ([id, item]) => /^[A-Za-z0-9_.:-]{1,100}$/.test(id) && isBox(item),
      ),
    // Por pregunta, la caja más alta; con la misma caja, la que vence antes.
    merge: (stored, incoming) => {
      const merged = { ...(stored as Record<string, { box: number; due: number }>) };
      for (const [id, item] of Object.entries(incoming as typeof merged)) {
        const old = merged[id];
        if (!old || item.box > old.box || (item.box === old.box && item.due < old.due)) {
          merged[id] = { box: item.box, due: item.due };
        }
      }
      return merged;
    },
  },
];

const familyOf = (key: string) => FAMILIES.find((family) => family.key.test(key));

const utf8Length = (text: string) => new TextEncoder().encode(text).length;

// Devuelve el progreso validado o el motivo por el que no vale. No acepta campos
// que el servidor no entiende: un error de la página se ve en vez de perderse.
export function parseProgress(input: unknown): Progress | string {
  if (!isRecord(input)) return "El cuerpo debe ser un objeto JSON.";
  const unknown = Object.keys(input).find((key) => !["done", "exercises", "kv"].includes(key));
  if (unknown) return `Campo desconocido: ${unknown.slice(0, 40)}.`;
  const progress: Progress = { done: [], exercises: {}, kv: {} };

  if (input.done !== undefined) {
    const { done } = input;
    if (!Array.isArray(done) || done.length > MAX_DONE) return "done debe ser una lista corta.";
    if (!done.every((id) => typeof id === "string" && LESSON.test(id))) {
      return "done lleva un id de lección inválido.";
    }
    progress.done = [...new Set(done as string[])];
  }

  if (input.exercises !== undefined) {
    const { exercises } = input;
    if (!isRecord(exercises) || Object.keys(exercises).length > MAX_EXERCISES) {
      return "exercises debe ser un objeto corto.";
    }
    for (const [id, item] of Object.entries(exercises)) {
      if (!EXERCISE.test(id) || !isRecord(item)) return "exercises lleva un ejercicio inválido.";
      const { code, hints, checks, passed, at } = item;
      const codeOk =
        code === undefined ||
        code === null ||
        (typeof code === "string" && utf8Length(code) <= MAX_CODE_BYTES);
      if (!codeOk || !isInt(hints) || !isInt(checks) || typeof passed !== "boolean" || !isInt(at)) {
        return `El ejercicio ${id} tiene campos inválidos.`;
      }
      progress.exercises[id] = { code, hints, checks, passed, at };
    }
  }

  if (input.kv !== undefined) {
    const { kv } = input;
    if (!isRecord(kv) || Object.keys(kv).length > MAX_KV_KEYS) return "kv debe ser un objeto.";
    for (const [key, value] of Object.entries(kv)) {
      const family = familyOf(key);
      if (!family?.valid(value) || utf8Length(JSON.stringify(value)) > MAX_KV_BYTES) {
        return `kv lleva una clave o un valor inválido: ${key.slice(0, 60)}.`;
      }
      progress.kv[key] = value;
    }
  }
  return progress;
}

// El progreso guardado y la versión con que se leyó, o null si el usuario ya no
// existe. Los cuatro SELECT van en un lote: ven el mismo estado.
async function readState(
  db: D1Database,
  userId: string,
): Promise<{ progress: Progress; version: number } | null> {
  const [done, exercises, kv, user] = await db.batch<Record<string, unknown>>([
    db.prepare("SELECT lesson FROM lesson_done WHERE user_id = ?1 ORDER BY lesson").bind(userId),
    db
      .prepare(
        "SELECT exercise, code, hints, checks, passed, updated_at FROM exercise_state WHERE user_id = ?1",
      )
      .bind(userId),
    db.prepare("SELECT key, value FROM kv WHERE user_id = ?1").bind(userId),
    db.prepare("SELECT progress_version AS version FROM users WHERE id = ?1").bind(userId),
  ]);
  if (user.results.length === 0) return null;
  const progress: Progress = { done: [], exercises: {}, kv: {} };
  for (const row of done.results) progress.done.push(row.lesson as string);
  for (const row of exercises.results) {
    progress.exercises[row.exercise as string] = {
      ...(row.code === null ? {} : { code: row.code as string }),
      hints: row.hints as number,
      checks: row.checks as number,
      passed: row.passed === 1,
      at: row.updated_at as number,
    };
  }
  for (const row of kv.results) progress.kv[row.key as string] = JSON.parse(row.value as string);
  return { progress, version: user.results[0].version as number };
}

export async function readProgress(db: D1Database, userId: string): Promise<Progress | null> {
  return (await readState(db, userId))?.progress ?? null;
}

function mergeExercise(stored: ExerciseState | undefined, incoming: ExerciseState): ExerciseState {
  if (!stored) return incoming;
  const newer = incoming.at > stored.at;
  // Sin código (`undefined` o null) la página no lo manda: no borra el guardado.
  const code = newer && typeof incoming.code === "string" ? incoming.code : stored.code;
  return {
    ...(code === undefined || code === null ? {} : { code }),
    hints: Math.max(stored.hints, incoming.hints),
    checks: Math.max(stored.checks, incoming.checks),
    passed: stored.passed || incoming.passed,
    at: Math.max(stored.at, incoming.at),
  };
}

export class TooMuch extends Error {}
// El usuario se borró (DELETE /api/me o la limpieza) mientras corría la petición.
export class Gone extends Error {}
// Otras escrituras del mismo usuario ganaron todas las veces.
export class Contended extends Error {}

const MAX_TRIES = 10;

// Junta `incoming` con lo guardado y devuelve el estado resultante. Lee, calcula y
// escribe en un lote cuyas sentencias solo actúan si `progress_version` sigue siendo
// la leída; la última la sube. D1 ejecuta el lote sin intercalar otras escrituras,
// así que si otra petición del mismo usuario escribió en medio, la última sentencia
// no cambia ninguna fila y se vuelve a leer. Ninguna escritura pisa a otra.
export async function mergeProgress(
  db: D1Database,
  userId: string,
  incoming: Progress,
  now: number,
): Promise<Progress> {
  for (let attempt = 0; attempt < MAX_TRIES; attempt++) {
    const state = await readState(db, userId);
    if (!state) throw new Gone();
    const { merged, statements } = plan(db, userId, state, incoming, now);
    if (statements.length === 0) return merged;
    statements.push(
      db
        .prepare(
          "UPDATE users SET progress_version = progress_version + 1 WHERE id = ?1 AND progress_version = ?2",
        )
        .bind(userId, state.version),
    );
    const results = await db.batch(statements);
    if (results[results.length - 1].meta.changes === 1) return merged;
  }
  throw new Contended();
}

function plan(
  db: D1Database,
  userId: string,
  { progress: stored, version }: { progress: Progress; version: number },
  incoming: Progress,
  now: number,
): { merged: Progress; statements: D1PreparedStatement[] } {
  const merged: Progress = {
    done: [...stored.done],
    exercises: { ...stored.exercises },
    kv: { ...stored.kv },
  };

  const newDone = incoming.done.filter((lesson) => !stored.done.includes(lesson));
  merged.done = [...merged.done, ...newDone].sort();

  const exerciseRows: unknown[] = [];
  for (const [id, item] of Object.entries(incoming.exercises)) {
    const next = mergeExercise(stored.exercises[id], item);
    if (JSON.stringify(next) === JSON.stringify(stored.exercises[id])) continue;
    merged.exercises[id] = next;
    exerciseRows.push({
      exercise: id,
      code: next.code ?? null,
      hints: next.hints,
      checks: next.checks,
      passed: next.passed ? 1 : 0,
      at: next.at,
    });
  }

  const kvRows: unknown[] = [];
  for (const [key, value] of Object.entries(incoming.kv)) {
    const old = stored.kv[key];
    const next = old === undefined ? value : familyOf(key)!.merge(old, value);
    if (JSON.stringify(next) === JSON.stringify(old)) continue;
    merged.kv[key] = next;
    kvRows.push({ key, value: JSON.stringify(next) });
  }

  if (
    merged.done.length > MAX_DONE ||
    Object.keys(merged.exercises).length > MAX_EXERCISES ||
    Object.keys(merged.kv).length > MAX_KV_KEYS
  ) {
    throw new TooMuch();
  }

  // Una sola sentencia por tabla: json_each reparte el arreglo en filas. El WHERE
  // es la guarda de versión (?4 en todas).
  const current = "(SELECT progress_version FROM users WHERE id = ?1) = ?4";
  const statements: D1PreparedStatement[] = [];
  const seconds = unixSeconds(now);
  if (newDone.length) {
    statements.push(
      db
        .prepare(
          `INSERT INTO lesson_done (user_id, lesson, done_at)
           SELECT ?1, value, ?3 FROM json_each(?2) WHERE ${current}
           ON CONFLICT DO NOTHING`,
        )
        .bind(userId, JSON.stringify(newDone), seconds, version),
    );
  }
  if (exerciseRows.length) {
    statements.push(
      db
        .prepare(
          `INSERT INTO exercise_state (user_id, exercise, code, hints, checks, passed, updated_at)
           SELECT ?1, value ->> '$.exercise', value ->> '$.code', value ->> '$.hints',
                  value ->> '$.checks', value ->> '$.passed', value ->> '$.at'
           FROM json_each(?2) WHERE ${current}
           ON CONFLICT (user_id, exercise) DO UPDATE SET
             code = excluded.code, hints = excluded.hints, checks = excluded.checks,
             passed = excluded.passed, updated_at = excluded.updated_at`,
        )
        .bind(userId, JSON.stringify(exerciseRows), seconds, version),
    );
  }
  if (kvRows.length) {
    statements.push(
      db
        .prepare(
          `INSERT INTO kv (user_id, key, value, updated_at)
           SELECT ?1, value ->> '$.key', value ->> '$.value', ?3 FROM json_each(?2) WHERE ${current}
           ON CONFLICT (user_id, key) DO UPDATE SET
             value = excluded.value, updated_at = excluded.updated_at`,
        )
        .bind(userId, JSON.stringify(kvRows), seconds, version),
    );
  }
  return { merged, statements };
}
