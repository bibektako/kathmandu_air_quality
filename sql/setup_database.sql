-- ============================================================
-- Kathmandu Air Quality – Database Setup
-- ============================================================
-- Run this file ONCE on a fresh PostgreSQL instance to create
-- the database, the application user, and all required tables.
--
-- Usage (as a PostgreSQL superuser / admin):
--   psql -U postgres -f sql/setup_database.sql
-- ============================================================

-- 1. Create the application role (skip if it already exists)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'air_user') THEN
        CREATE ROLE air_user WITH LOGIN PASSWORD 'postgres';
    END IF;
END
$$;

-- 2. Create the database (must be run outside a transaction block,
--    so we check first to avoid an error if it already exists)
SELECT 'CREATE DATABASE air_quality OWNER air_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'air_quality')
\gexec

-- Grant connect privilege
GRANT ALL PRIVILEGES ON DATABASE air_quality TO air_user;

-- 3. Switch into the new database
\connect air_quality

-- Grant schema usage to air_user
GRANT ALL ON SCHEMA public TO air_user;

-- ============================================================
-- 4. Create tables
-- ============================================================

-- Dimension: AQI Category
CREATE TABLE IF NOT EXISTS dim_aqi_category (
    aqi_category_id BIGINT,
    aqi_category    TEXT
);

-- Dimension: Station
CREATE TABLE IF NOT EXISTS dim_station (
    station_id   BIGINT,
    station_name TEXT,
    latitude     DOUBLE PRECISION,
    longitude    DOUBLE PRECISION
);

-- Dimension: Time
CREATE TABLE IF NOT EXISTS dim_time (
    datetime_local TEXT,
    date           TEXT,
    hour           BIGINT,
    day_of_week    TEXT,
    is_weekend     BOOLEAN
);

-- Fact: Air Quality
CREATE TABLE IF NOT EXISTS fact_air_quality (
    station_id      BIGINT,
    station_name    TEXT,
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION,
    datetime_local  TEXT,
    date            TEXT,
    hour            BIGINT,
    day_of_week     TEXT,
    is_weekend      BOOLEAN,
    value           DOUBLE PRECISION,
    unit            TEXT,
    coverage_pct    DOUBLE PRECISION,
    aqi             BIGINT,
    aqi_category_id TEXT
);

-- Transfer ownership so air_user can read/write
ALTER TABLE dim_aqi_category OWNER TO air_user;
ALTER TABLE dim_station      OWNER TO air_user;
ALTER TABLE dim_time         OWNER TO air_user;
ALTER TABLE fact_air_quality OWNER TO air_user;

-- ============================================================
-- Done! Now run the Python loader:
--   python notebooks/load_data_into_db.py
-- ============================================================
