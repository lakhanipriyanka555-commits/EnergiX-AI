-- ═══════════════════════════════════════════════════════════════════
-- EnergiX AI – Supabase Setup Script
-- Run this ONCE in your Supabase SQL Editor:
--   Dashboard → SQL Editor → New Query → paste & Run
-- ═══════════════════════════════════════════════════════════════════

-- ── 1. Tables ────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS consumers (
    id            BIGSERIAL PRIMARY KEY,
    consumer_id   TEXT        UNIQUE NOT NULL,
    name          TEXT        NOT NULL,
    city          TEXT        NOT NULL,
    device_type   TEXT        NOT NULL,
    contract_kw   REAL        NOT NULL,
    tariff_rate   REAL        NOT NULL,
    latitude      REAL,
    longitude     REAL,
    registered_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS energy_readings (
    id            BIGSERIAL PRIMARY KEY,
    consumer_id   TEXT        NOT NULL,
    timestamp     TIMESTAMPTZ NOT NULL,
    energy_kwh    REAL        NOT NULL,
    voltage       REAL        NOT NULL,
    current_a     REAL        NOT NULL,
    power_factor  REAL        NOT NULL,
    temperature   REAL        NOT NULL,
    city          TEXT        NOT NULL,
    device_type   TEXT        NOT NULL,
    cost_usd      REAL        NOT NULL
);

CREATE TABLE IF NOT EXISTS predictions (
    id              BIGSERIAL PRIMARY KEY,
    prediction_date DATE        NOT NULL,
    hour            INTEGER     NOT NULL,
    predicted_kwh   REAL        NOT NULL,
    confidence      REAL        NOT NULL,
    model_version   TEXT        DEFAULT 'v2.1',
    city            TEXT        NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS anomalies (
    id            BIGSERIAL PRIMARY KEY,
    consumer_id   TEXT        NOT NULL,
    detected_at   TIMESTAMPTZ NOT NULL,
    anomaly_type  TEXT        NOT NULL,
    risk_score    REAL        NOT NULL,
    description   TEXT,
    status        TEXT        DEFAULT 'Open',
    city          TEXT        NOT NULL
);

CREATE TABLE IF NOT EXISTS smart_meters (
    id               BIGSERIAL PRIMARY KEY,
    meter_id         TEXT        UNIQUE NOT NULL,
    consumer_id      TEXT        NOT NULL,
    city             TEXT        NOT NULL,
    status           TEXT        DEFAULT 'Active',
    firmware_version TEXT        DEFAULT 'v3.2.1',
    last_ping        TIMESTAMPTZ,
    battery_pct      REAL        DEFAULT 100.0
);

CREATE TABLE IF NOT EXISTS users (
    id         BIGSERIAL PRIMARY KEY,
    email      TEXT        UNIQUE NOT NULL,
    name       TEXT        NOT NULL,
    role       TEXT        NOT NULL,
    last_login TIMESTAMPTZ,
    is_active  BOOLEAN     DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── 2. Indexes (for performance) ─────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_readings_timestamp   ON energy_readings (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_readings_consumer     ON energy_readings (consumer_id);
CREATE INDEX IF NOT EXISTS idx_anomalies_detected    ON anomalies (detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_anomalies_risk        ON anomalies (risk_score DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_date      ON predictions (prediction_date DESC);

-- ── 3. Disable RLS (demo app – re-enable + add policies in production) ─

ALTER TABLE consumers      DISABLE ROW LEVEL SECURITY;
ALTER TABLE energy_readings DISABLE ROW LEVEL SECURITY;
ALTER TABLE predictions    DISABLE ROW LEVEL SECURITY;
ALTER TABLE anomalies      DISABLE ROW LEVEL SECURITY;
ALTER TABLE smart_meters   DISABLE ROW LEVEL SECURITY;
ALTER TABLE users          DISABLE ROW LEVEL SECURITY;

-- ── 4. run_sql() – Powers the SQL Explorer page ──────────────────────
-- This function executes arbitrary SELECT queries and returns JSON.
-- It runs with SECURITY DEFINER so PostgREST can call it via RPC.

CREATE OR REPLACE FUNCTION run_sql(query text)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    result jsonb;
BEGIN
    EXECUTE format(
        'SELECT COALESCE(json_agg(row_to_json(t)), ''[]''::json) FROM (%s) t',
        query
    ) INTO result;
    RETURN result;
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object('error', SQLERRM, 'detail', SQLSTATE)::jsonb;
END;
$$;

-- Grant RPC access to anon and authenticated roles
GRANT EXECUTE ON FUNCTION run_sql(text) TO anon;
GRANT EXECUTE ON FUNCTION run_sql(text) TO authenticated;

-- ── 5. Verify ────────────────────────────────────────────────────────
-- After running, you should see 6 tables in your Table Editor.
-- Test the function: SELECT run_sql('SELECT 1 AS ok');
