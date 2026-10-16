-- Esquema de la base D1 (binding DB). No hay migraciones: para cambiarlo se
-- borra la base, se crea otra y se aplica este archivo. D1 hace cumplir las
-- claves foráneas, así que borrar una fila de users borra todo lo suyo.
-- No se guarda correo, nombre, avatar ni contraseña.
-- Tiempos: *_day son días desde la época; exercise_state.updated_at son
-- milisegundos (el `at` que manda la página); los demás, segundos Unix.

CREATE TABLE users (
  id          TEXT PRIMARY KEY,
  created_day INTEGER NOT NULL,
  seen_day    INTEGER NOT NULL,
  -- Sube con cada escritura de progreso. Una escritura solo vale si la versión
  -- sigue siendo la que leyó (ver mergeProgress).
  progress_version INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE identities (
  provider TEXT NOT NULL CHECK (provider IN ('google', 'github')),
  subject  TEXT NOT NULL,
  user_id  TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  PRIMARY KEY (provider, subject)
) WITHOUT ROWID;

CREATE TABLE sessions (
  token_hash TEXT PRIMARY KEY,
  user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires_at INTEGER NOT NULL
) WITHOUT ROWID;

CREATE TABLE lesson_done (
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  lesson  TEXT NOT NULL,
  done_at INTEGER NOT NULL,
  PRIMARY KEY (user_id, lesson)
) WITHOUT ROWID;

CREATE TABLE exercise_state (
  user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  exercise   TEXT NOT NULL,
  code       TEXT,
  hints      INTEGER NOT NULL DEFAULT 0,
  checks     INTEGER NOT NULL DEFAULT 0,
  passed     INTEGER NOT NULL DEFAULT 0,
  updated_at INTEGER NOT NULL,
  PRIMARY KEY (user_id, exercise)
) WITHOUT ROWID;

CREATE TABLE kv (
  user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  key        TEXT NOT NULL,
  value      TEXT NOT NULL,
  updated_at INTEGER NOT NULL,
  PRIMARY KEY (user_id, key)
) WITHOUT ROWID;

CREATE TABLE attempts (
  id         INTEGER PRIMARY KEY,
  at         INTEGER NOT NULL,
  user_id    TEXT REFERENCES users(id) ON DELETE CASCADE,
  exercise   TEXT NOT NULL CHECK (exercise GLOB '[a-z0-9-]*/[a-z0-9-]*'),
  mode       TEXT NOT NULL CHECK (mode IN ('run', 'check')),
  outcome    TEXT NOT NULL CHECK (outcome IN ('pass', 'fail', 'error', 'timeout')),
  failed     TEXT NOT NULL DEFAULT '[]',
  error_kind TEXT,
  hints      INTEGER NOT NULL DEFAULT 0,
  ms         INTEGER NOT NULL,
  code_bytes INTEGER NOT NULL
);

CREATE INDEX attempts_exercise ON attempts (exercise, at);
CREATE INDEX attempts_user ON attempts (user_id);
CREATE INDEX attempts_at ON attempts (at);
