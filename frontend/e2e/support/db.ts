import { execFileSync } from 'node:child_process'

/** Connection defaults mirror the backend (`spd.core.config`). */
const PG_ENV = {
  PGHOST: process.env.PGHOST ?? 'localhost',
  PGPORT: process.env.PGPORT ?? '5432',
  PGUSER: process.env.PGUSER ?? 'spd',
  PGPASSWORD: process.env.PGPASSWORD ?? 'spd',
  PGDATABASE: process.env.PGDATABASE ?? 'spd_dev',
}

/**
 * Insert a fresh activity event straight into the database. The API is
 * read-only, so this is the only way to give the SSE stream something to
 * deliver *while a page is open*.
 */
export function emitActivity(login: string, kind = 'commit'): number {
  const sql = `
    INSERT INTO activity_events (user_id, kind, day, xp_delta, occurred_at, payload)
    SELECT id, '${kind}', CURRENT_DATE, 200, now(), '{}'::jsonb
    FROM users
    WHERE login = '${login}'
    RETURNING id;
  `
  const out = execFileSync('psql', ['-v', 'ON_ERROR_STOP=1', '-tAc', sql], {
    env: { ...process.env, ...PG_ENV },
    encoding: 'utf8',
  })
  const id = Number.parseInt(out.trim(), 10)
  if (Number.isNaN(id)) {
    throw new Error(`failed to emit activity event: ${out}`)
  }
  return id
}
