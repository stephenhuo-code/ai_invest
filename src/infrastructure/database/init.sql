-- Initialize database with pgvector extension and basic setup
-- This file is run automatically when the PostgreSQL container starts

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable other useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For better text search

-- Create database if it doesn't exist (though it should be created by POSTGRES_DB)
-- Note: This is mainly for documentation, as the database is created by the container

-- Set default timezone
SET timezone = 'UTC';

-- Create updated_at trigger function for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create vector norm calculation function for performance optimization
CREATE OR REPLACE FUNCTION calculate_vector_norm()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.embedding IS NOT NULL THEN
        NEW.norm = sqrt((NEW.embedding <#> NEW.embedding));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'AI Invest database initialized successfully with pgvector extension';
END
$$;