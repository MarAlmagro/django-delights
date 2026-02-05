-- Django Delights Database Initialization Script
-- This script runs when PostgreSQL container is first created

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant permissions (if using a specific app user)
-- CREATE USER app_user WITH PASSWORD 'secure_password';
-- GRANT ALL PRIVILEGES ON DATABASE django_delights TO app_user;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Django Delights database initialized successfully at %', NOW();
END $$;
