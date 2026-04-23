-- SCEIN Fellowship Data Tracker - Supabase Schema
-- Updated rerunnable version for Supabase SQL Editor

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- ==================================
-- MAIN TABLE
-- ==================================

CREATE TABLE IF NOT EXISTS permits_data (
    id BIGSERIAL PRIMARY KEY,
    url TEXT NOT NULL,

    -- Category (permit, incentive, regulation) — from Excel sheet name
    data_type TEXT CHECK (data_type IN ('permit', 'incentive', 'regulation')) NOT NULL,

    -- Excel columns
    parameter_name TEXT,          -- Col 5: Dataset Name
    description TEXT,             -- Col 1: Description
    source_accreditation TEXT,    -- Col 7: Source Accreditation
    data_age TEXT,                -- Col 9: Data Age
    owner_class TEXT,             -- Col 11: Owner Class (Federal/State/Local)
    item_type TEXT,               -- Col 19: Permit/Incentive/Regulation Type
    applicable_system_types TEXT, -- Col 20: Applicable System Types
    min_system_size_mw NUMERIC(10, 4),  -- Col 22
    max_system_size_mw NUMERIC(10, 4),  -- Col 23
    excel_sheet TEXT NOT NULL,
    excel_row INTEGER NOT NULL,

    -- Location data
    county TEXT,
    state TEXT,

    -- Scraped metadata
    source_html_title TEXT,
    full_text TEXT,
    requirements TEXT,

    -- Dates
    effective_date TEXT,
    expiry_date TEXT,
    last_updated TEXT,

    -- Financial
    cost NUMERIC(12, 2),

    -- Timeline
    timeframe_days INTEGER,

    -- Status
    status TEXT CHECK (status IN ('active', 'expired', 'pending', 'amended', 'error', 'unknown')) DEFAULT 'unknown',
    error_message TEXT,

    -- Geospatial
    location GEOGRAPHY(POINT, 4326),

    -- Timestamps
    scraped_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add the composite unique constraint conditionally
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'unique_permit_row'
    ) THEN
        ALTER TABLE permits_data 
        ADD CONSTRAINT unique_permit_row 
        UNIQUE (url, data_type, excel_sheet, excel_row);
    END IF;
END $$;

-- ==================================
-- ALTER TABLE: add new columns to existing table
-- ==================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'permits_data' AND column_name = 'source_accreditation'
    ) THEN
        ALTER TABLE permits_data ADD COLUMN source_accreditation TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'permits_data' AND column_name = 'data_age'
    ) THEN
        ALTER TABLE permits_data ADD COLUMN data_age TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'permits_data' AND column_name = 'owner_class'
    ) THEN
        ALTER TABLE permits_data ADD COLUMN owner_class TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'permits_data' AND column_name = 'item_type'
    ) THEN
        ALTER TABLE permits_data ADD COLUMN item_type TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'permits_data' AND column_name = 'applicable_system_types'
    ) THEN
        ALTER TABLE permits_data ADD COLUMN applicable_system_types TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'permits_data' AND column_name = 'min_system_size_mw'
    ) THEN
        ALTER TABLE permits_data ADD COLUMN min_system_size_mw NUMERIC(10, 4);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'permits_data' AND column_name = 'max_system_size_mw'
    ) THEN
        ALTER TABLE permits_data ADD COLUMN max_system_size_mw NUMERIC(10, 4);
    END IF;
END $$;

-- ==================================
-- INDEXES
-- ==================================
CREATE INDEX IF NOT EXISTS idx_permits_data_type ON permits_data(data_type);
CREATE INDEX IF NOT EXISTS idx_permits_county ON permits_data(county);
CREATE INDEX IF NOT EXISTS idx_permits_state ON permits_data(state);
CREATE INDEX IF NOT EXISTS idx_permits_status ON permits_data(status);
CREATE INDEX IF NOT EXISTS idx_permits_scraped_at ON permits_data(scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_permits_parameter_name ON permits_data(parameter_name);

-- Full text search index
CREATE INDEX IF NOT EXISTS idx_permits_full_text_search
ON permits_data
USING gin (
    to_tsvector(
        'english',
        COALESCE(parameter_name, '') || ' ' ||
        COALESCE(description, '') || ' ' ||
        COALESCE(full_text, '')
    )
);

-- Spatial index
CREATE INDEX IF NOT EXISTS idx_permits_location ON permits_data USING GIST(location);

-- ==================================
-- UPDATED_AT TRIGGER
-- ==================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_permits_data_updated_at ON permits_data;

CREATE TRIGGER update_permits_data_updated_at
    BEFORE UPDATE ON permits_data
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==================================
-- ROW LEVEL SECURITY
-- ==================================
ALTER TABLE permits_data ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'permits_data'
          AND policyname = 'Public read access'
    ) THEN
        CREATE POLICY "Public read access"
            ON permits_data
            FOR SELECT
            TO anon, authenticated
            USING (true);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'permits_data'
          AND policyname = 'Service role full access'
    ) THEN
        CREATE POLICY "Service role full access"
            ON permits_data
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);
    END IF;
END $$;

-- ==================================
-- VIEWS FOR ANALYSIS
-- ==================================

CREATE OR REPLACE VIEW active_permits AS
SELECT *
FROM permits_data
WHERE status = 'active'
  AND data_type = 'permit';

CREATE OR REPLACE VIEW active_incentives AS
SELECT *
FROM permits_data
WHERE status = 'active'
  AND data_type = 'incentive';

CREATE OR REPLACE VIEW active_regulations AS
SELECT *
FROM permits_data
WHERE status = 'active'
  AND data_type = 'regulation';

CREATE OR REPLACE VIEW expiring_soon AS
SELECT *
FROM permits_data
WHERE status = 'active'
  AND expiry_date IS NOT NULL
  AND expiry_date != '';

CREATE OR REPLACE VIEW california_county_stats AS
SELECT
    county,
    data_type,
    status,
    COUNT(*) AS count,
    AVG(cost) AS avg_cost,
    AVG(timeframe_days) AS avg_timeframe_days,
    MAX(scraped_at) AS last_scraped
FROM permits_data
WHERE state = 'CA'
  AND county IS NOT NULL
GROUP BY county, data_type, status
ORDER BY county, data_type;

CREATE OR REPLACE VIEW state_summary AS
SELECT
    state,
    data_type,
    status,
    COUNT(*) AS total_records,
    COUNT(CASE WHEN cost IS NOT NULL THEN 1 END) AS records_with_cost,
    COUNT(CASE WHEN timeframe_days IS NOT NULL THEN 1 END) AS records_with_timeframe,
    AVG(cost) AS avg_cost,
    AVG(timeframe_days) AS avg_timeframe_days,
    MAX(scraped_at) AS last_scraped
FROM permits_data
GROUP BY state, data_type, status
ORDER BY state, data_type;

CREATE OR REPLACE VIEW scraping_health AS
SELECT
    data_type,
    status,
    COUNT(*) AS count,
    MIN(scraped_at) AS oldest_scrape,
    MAX(scraped_at) AS newest_scrape,
    COUNT(CASE WHEN error_message IS NOT NULL THEN 1 END) AS error_count
FROM permits_data
GROUP BY data_type, status;

-- ==================================
-- HELPER FUNCTIONS
-- ==================================

CREATE OR REPLACE FUNCTION search_permits(search_query TEXT)
RETURNS TABLE (
    id BIGINT,
    url TEXT,
    data_type TEXT,
    parameter_name TEXT,
    county TEXT,
    state TEXT,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.url,
        p.data_type,
        p.parameter_name,
        p.county,
        p.state,
        ts_rank(
            to_tsvector(
                'english',
                COALESCE(p.parameter_name, '') || ' ' ||
                COALESCE(p.description, '') || ' ' ||
                COALESCE(p.full_text, '')
            ),
            plainto_tsquery('english', search_query)
        ) AS rank
    FROM permits_data p
    WHERE to_tsvector(
            'english',
            COALESCE(p.parameter_name, '') || ' ' ||
            COALESCE(p.description, '') || ' ' ||
            COALESCE(p.full_text, '')
          ) @@ plainto_tsquery('english', search_query)
    ORDER BY rank DESC
    LIMIT 100;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_county_permits(county_name TEXT)
RETURNS SETOF permits_data AS $$
BEGIN
    RETURN QUERY
    SELECT *
    FROM permits_data
    WHERE county ILIKE county_name
    ORDER BY data_type, parameter_name;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION geocode_county_batch()
RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER := 0;
BEGIN
    RAISE NOTICE 'Geocoding not yet implemented. Integrate with geocoding service.';
    RETURN updated_count;
END;
$$ LANGUAGE plpgsql;

-- ==================================
-- CALIFORNIA COUNTY REFERENCE TABLE
-- ==================================
CREATE TABLE IF NOT EXISTS california_counties (
    id SERIAL PRIMARY KEY,
    county_name TEXT UNIQUE NOT NULL,
    fips_code TEXT,
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7),
    location GEOGRAPHY(POINT, 4326),
    population INTEGER,
    area_sq_miles NUMERIC(10, 2)
);

INSERT INTO california_counties (county_name, fips_code, latitude, longitude, location) VALUES
('Alameda', '06001', 37.6463, -121.8852, ST_SetSRID(ST_MakePoint(-121.8852, 37.6463), 4326)),
('Alpine', '06003', 38.5893, -119.8165, ST_SetSRID(ST_MakePoint(-119.8165, 38.5893), 4326)),
('Amador', '06005', 38.3488, -120.5475, ST_SetSRID(ST_MakePoint(-120.5475, 38.3488), 4326)),
('Butte', '06007', 39.6560, -121.5992, ST_SetSRID(ST_MakePoint(-121.5992, 39.6560), 4326)),
('Calaveras', '06009', 38.2083, -120.5405, ST_SetSRID(ST_MakePoint(-120.5405, 38.2083), 4326)),
('Colusa', '06011', 39.1794, -122.2418, ST_SetSRID(ST_MakePoint(-122.2418, 39.1794), 4326)),
('Contra Costa', '06013', 37.9190, -121.9618, ST_SetSRID(ST_MakePoint(-121.9618, 37.9190), 4326)),
('Del Norte', '06015', 41.7427, -123.9902, ST_SetSRID(ST_MakePoint(-123.9902, 41.7427), 4326)),
('El Dorado', '06017', 38.7855, -120.5325, ST_SetSRID(ST_MakePoint(-120.5325, 38.7855), 4326)),
('Fresno', '06019', 36.7378, -119.7871, ST_SetSRID(ST_MakePoint(-119.7871, 36.7378), 4326)),
('Glenn', '06021', 39.5984, -122.3919, ST_SetSRID(ST_MakePoint(-122.3919, 39.5984), 4326)),
('Humboldt', '06023', 40.7450, -123.8695, ST_SetSRID(ST_MakePoint(-123.8695, 40.7450), 4326))
ON CONFLICT (county_name) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_ca_counties_location
ON california_counties USING GIST(location);

-- ==================================
-- COMMENTS
-- ==================================
COMMENT ON TABLE permits_data IS 'Main table storing permits, incentives, and regulations from SCEIN Fellowship tracker';
COMMENT ON COLUMN permits_data.location IS 'Geospatial point for mapping in QGIS (EPSG:4326)';
COMMENT ON VIEW california_county_stats IS 'Summary statistics for California counties';
COMMENT ON FUNCTION search_permits IS 'Full-text search across all permit data';