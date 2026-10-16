import type { RateLimiter, Verdict } from "./meters.ts";
import { mac } from "./session.ts";

const DAY_MS = 86_400_000;

// Cuenta una petición en el contador de `key` bajo `label`. El nombre del objeto es
// un HMAC del día y de la clave (una IP o un usuario), así que no se puede volver
// a ellos sin el secreto. Las etiquetas separan los contadores de una misma clave.
export async function take(
  limiters: DurableObjectNamespace<RateLimiter>,
  secret: string,
  label: string,
  key: string,
  now: number,
  perMinute: number,
  perDay: number,
): Promise<Verdict> {
  const dayStart = Math.floor(now / DAY_MS) * DAY_MS;
  const name = await mac(secret, label, `${dayStart}|${key}`);
  const limiter = limiters.get(limiters.idFromName(name));
  return limiter.take(now, perMinute, perDay, dayStart + DAY_MS);
}
