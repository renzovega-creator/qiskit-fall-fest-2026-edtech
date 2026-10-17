import { DAY_MS, unixSeconds } from "./account.ts";
import type { Limits } from "./limits.ts";

// La limpieza diaria (cron). Los intentos y las cuentas sin visitas se borran al
// pasar su plazo; una cuenta borrada arrastra su progreso y sus intentos por las
// claves foráneas.
export async function purge(
  db: D1Database,
  limits: Limits,
  now: number,
): Promise<void> {
  await db.batch([
    db
      .prepare("DELETE FROM attempts WHERE at < ?1")
      .bind(unixSeconds(now - limits.attemptRetentionMs)),
    db
      .prepare("DELETE FROM sessions WHERE expires_at < ?1")
      .bind(unixSeconds(now)),
    db
      .prepare("DELETE FROM users WHERE seen_day < ?1")
      .bind(Math.floor((now - limits.accountRetentionMs) / DAY_MS)),
  ]);
}
