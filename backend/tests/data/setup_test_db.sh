#!/bin/bash
set -e

# Create the test database
echo "Creating AI Secretary test database..."
psql -U postgres -c "CREATE DATABASE ai_secretary_test WITH OWNER postgres;" || true

# Create users table in test database
echo "Creating users table in test database..."
psql -U postgres -d ai_secretary_test -c "
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    google_id VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    profile_picture TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    refresh_token TEXT,
    calendar_connected BOOLEAN DEFAULT FALSE,
    calendar_url TEXT,
    timezone VARCHAR(50) DEFAULT 'UTC',
    twilio_number VARCHAR(20),
    user_number VARCHAR(20)
);"

# Add test user
echo "Adding test user to database..."
psql -U postgres -d ai_secretary_test -c "
INSERT INTO users (id, email, google_id, full_name, twilio_number, user_number, is_active, calendar_connected, timezone)
VALUES ('a2d7200a-e061-460a-b5a2-afc47344caa9', 'test_user_1@example.com', 'google_id_1', 'Test User 1', '+15550000001', '+15551110001', TRUE, FALSE, 'UTC')
ON CONFLICT (id) DO NOTHING;"

echo "Test database setup complete!" 