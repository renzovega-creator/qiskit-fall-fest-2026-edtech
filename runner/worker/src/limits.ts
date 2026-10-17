export interface Env {
  TURNSTILE_SECRET: string;
  // La página recibe la clave pública en la respuesta `turnstile_missing`.
  TURNSTILE_SITE_KEY: string;
  RATE_PER_MINUTE: string;
  RATE_PER_DAY: string;
  MAX_CODE_BYTES: string;
  MONTHLY_BUDGET_USD: string;
  USD_PER_BUSY_SECOND: string;
  RESERVED_BUSY_SECONDS: string;
  SESSION_HOURS: string;
  AUTH_PER_MINUTE: string;
  AUTH_SESSION_DAYS: string;
  SIGNED_IN_IP_FACTOR: string;
  ATTEMPT_RETENTION_DAYS: string;
  ACCOUNT_RETENTION_DAYS: string;
  DB: D1Database;
  // Secretos de los clientes OAuth. Un proveedor sin ellos responde 503.
  GOOGLE_CLIENT_ID?: string;
  GOOGLE_CLIENT_SECRET?: string;
  GITHUB_CLIENT_ID?: string;
  GITHUB_CLIENT_SECRET?: string;
}

type NumericVar =
  | "RATE_PER_MINUTE"
  | "RATE_PER_DAY"
  | "MAX_CODE_BYTES"
  | "MONTHLY_BUDGET_USD"
  | "USD_PER_BUSY_SECOND"
  | "RESERVED_BUSY_SECONDS"
  | "SESSION_HOURS"
  | "AUTH_PER_MINUTE"
  | "AUTH_SESSION_DAYS"
  | "SIGNED_IN_IP_FACTOR"
  | "ATTEMPT_RETENTION_DAYS"
  | "ACCOUNT_RETENTION_DAYS";

export interface Limits {
  perMinute: number;
  perDay: number;
  maxCodeBytes: number;
  // El cuerpo admite seis veces el código más la envoltura JSON de 1024 bytes.
  // Es el mismo tope que runner/server.py.
  maxBodyBytes: number;
  budgetNano: number;
  nanoPerBusySecond: number;
  // Lo que una ejecución aparta del presupuesto antes de empezar, y el tiempo de
  // contenedor que cubre. Es un tope: al llegar a `reserveMs` se detiene la
  // instancia y nunca se cobra más de `reserveNano`.
  reserveNano: number;
  reserveMs: number;
  sessionMs: number;
  // Peticiones por minuto y por IP a /auth/*.
  authPerMinute: number;
  authSessionMs: number;
  // El tope por IP de quien tiene cuenta es este múltiplo del anónimo.
  signedInIpFactor: number;
  attemptRetentionMs: number;
  accountRetentionMs: number;
}

const NANO = 1e9;
const DAY_MS = 86_400_000;

export class ConfigError extends Error {
  override name = "ConfigError";
}

function positive(env: Env, name: NumericVar, integer: boolean): number {
  const n = Number(env[name]);
  if (!Number.isFinite(n) || n <= 0 || (integer && !Number.isInteger(n))) {
    throw new ConfigError(
      `${name} debe ser un número positivo${integer ? " entero" : ""}`,
    );
  }
  return n;
}

// Todos los valores salen de `env` (cloudflare.config.ts); un valor ausente o
// inválido es un error de configuración, no un valor por defecto.
export function loadLimits(env: Env): Limits {
  const maxCodeBytes = positive(env, "MAX_CODE_BYTES", true);
  const nanoPerBusySecond = positive(env, "USD_PER_BUSY_SECOND", false) * NANO;
  const reserveSeconds = positive(env, "RESERVED_BUSY_SECONDS", false);
  return {
    perMinute: positive(env, "RATE_PER_MINUTE", true),
    perDay: positive(env, "RATE_PER_DAY", true),
    maxCodeBytes,
    maxBodyBytes: 6 * maxCodeBytes + 1024,
    budgetNano: Math.round(positive(env, "MONTHLY_BUDGET_USD", false) * NANO),
    nanoPerBusySecond,
    reserveNano: Math.round(reserveSeconds * nanoPerBusySecond),
    reserveMs: reserveSeconds * 1000,
    sessionMs: positive(env, "SESSION_HOURS", false) * 3_600_000,
    authPerMinute: positive(env, "AUTH_PER_MINUTE", true),
    authSessionMs: positive(env, "AUTH_SESSION_DAYS", false) * DAY_MS,
    signedInIpFactor: positive(env, "SIGNED_IN_IP_FACTOR", true),
    attemptRetentionMs: positive(env, "ATTEMPT_RETENTION_DAYS", false) * DAY_MS,
    accountRetentionMs: positive(env, "ACCOUNT_RETENTION_DAYS", false) * DAY_MS,
  };
}
