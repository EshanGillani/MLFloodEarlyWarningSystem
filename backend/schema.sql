-- Karachi Flood Early Warning System — Database Schema
-- The backend auto-creates these tables on startup, but you can also run this manually.

-- 1. Predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data_hour_utc TIMESTAMPTZ NOT NULL,
    data_hour_pk TIMESTAMPTZ NOT NULL,
    pressure DOUBLE PRECISION NOT NULL,
    precipitation DOUBLE PRECISION NOT NULL,
    humidity DOUBLE PRECISION NOT NULL,
    pressure_trend DOUBLE PRECISION NOT NULL,
    prediction INTEGER NOT NULL,         -- 0, 1, or 2
    status TEXT NOT NULL,                -- NORMAL, FLOOD WATCH, EMERGENCY WARNING
    color TEXT NOT NULL,                 -- GREEN, YELLOW, RED
    confidence DOUBLE PRECISION NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions (created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_predictions_data_hour ON predictions (data_hour_utc);

-- 2. Weather observations time-series table
CREATE TABLE IF NOT EXISTS weather_observations (
    id BIGSERIAL PRIMARY KEY,
    observed_at TIMESTAMPTZ NOT NULL,
    surface_pressure DOUBLE PRECISION,
    precipitation DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    temperature DOUBLE PRECISION,
    source TEXT NOT NULL DEFAULT 'open-meteo',
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Derived features (computed via SQL window functions)
    pressure_trend_3h DOUBLE PRECISION,
    precip_rolling_6h DOUBLE PRECISION,
    precip_rolling_24h DOUBLE PRECISION,
    pressure_rolling_12h DOUBLE PRECISION,
    humidity_rolling_6h DOUBLE PRECISION,
    flood_label INTEGER                  -- 0=NORMAL, 1=FLOOD WATCH, 2=EMERGENCY
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_weather_obs_observed_at ON weather_observations (observed_at);
CREATE INDEX IF NOT EXISTS idx_weather_obs_time_range ON weather_observations (observed_at DESC);

-- 3. Model training log
CREATE TABLE IF NOT EXISTS model_training_log (
    id BIGSERIAL PRIMARY KEY,
    trained_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    training_samples INTEGER NOT NULL,
    accuracy DOUBLE PRECISION NOT NULL,
    feature_importances JSONB,
    obs_date_start TIMESTAMPTZ,
    obs_date_end TIMESTAMPTZ,
    trigger TEXT NOT NULL DEFAULT 'scheduled'  -- scheduled, startup, manual
);
