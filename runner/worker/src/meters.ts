import { DurableObject } from "cloudflare:workers";

export type Verdict = { ok: true } | { ok: false; scope: "minute" | "day"; retryAfter: number };

const MINUTE_MS = 60_000;

// Un objeto por IP y día, nombrado con un HMAC de la IP en index.ts. Borra su
// estado cuando termina el día.
export class RateLimiter extends DurableObject {
  async take(now: number, perMinute: number, perDay: number, dayEnd: number): Promise<Verdict> {
    const stored = await this.ctx.storage.get<{ minute: number; inMinute: number; inDay: number }>(
      "count",
    );
    const minute = Math.floor(now / MINUTE_MS);
    const count = {
      minute,
      inMinute: stored?.minute === minute ? stored.inMinute : 0,
      inDay: stored?.inDay ?? 0,
    };
    if (count.inDay >= perDay) {
      return { ok: false, scope: "day", retryAfter: Math.max(1, Math.ceil((dayEnd - now) / 1000)) };
    }
    if (count.inMinute >= perMinute) {
      const next = (minute + 1) * MINUTE_MS;
      return {
        ok: false,
        scope: "minute",
        retryAfter: Math.max(1, Math.ceil((next - now) / 1000)),
      };
    }
    count.inMinute += 1;
    count.inDay += 1;
    await this.ctx.storage.put("count", count);
    await this.ctx.storage.setAlarm(dayEnd + MINUTE_MS);
    return { ok: true };
  }

  async alarm(): Promise<void> {
    await this.ctx.storage.deleteAll();
  }
}

// Guarda el gasto estimado del mes en nanodólares y descarta los meses anteriores.
// El objeto atiende una llamada a la vez, y `reserve` y `settle` no esperan nada
// salvo su propio almacenamiento, así que comprobar y apartar es una sola
// operación.
export class Budget extends DurableObject {
  private async total(month: string): Promise<number> {
    const stored = await this.ctx.storage.get<{ month: string; nano: number }>("spent");
    return stored?.month === month ? stored.nano : 0;
  }

  // Aparta `nano` si el mes sigue dentro de `budget` y dice si lo apartó.
  async reserve(month: string, nano: number, budget: number): Promise<boolean> {
    const total = await this.total(month);
    if (total + nano > budget) return false;
    await this.ctx.storage.put("spent", { month, nano: total + nano });
    return true;
  }

  // Cambia lo apartado por el coste medido, que nunca pasa de lo apartado: así el
  // total del mes no supera el presupuesto aunque una ejecución haya durado más.
  // Si el mes ya cambió, el total nuevo no incluía la reserva y no hay nada que
  // ajustar.
  async settle(month: string, reserved: number, actual: number): Promise<void> {
    const stored = await this.ctx.storage.get<{ month: string; nano: number }>("spent");
    if (stored?.month !== month) return;
    await this.ctx.storage.put("spent", {
      month,
      nano: Math.max(0, stored.nano - reserved + Math.min(actual, reserved)),
    });
  }
}
