#!/usr/bin/env python
"""
Script to initialize the test database with required tables and test data.
"""
import asyncio
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Ensure the app directory is in the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

async def init_test_db():
    # Default to localhost for direct script execution, db for container environment
    db_host = os.environ.get("DB_HOST", "db")
    db_url = f"postgresql+asyncpg://postgres:postgres@{db_host}:5432/postgres"
    
    print(f"Connecting to database at {db_url}")
    engine = create_async_engine(db_url, echo=True)
    
    async with engine.begin() as conn:
        # Create test database if it doesn't exist
        try:
            await conn.execute(text("CREATE DATABASE ai_secretary_test WITH OWNER postgres;"))
            print("Test database created successfully")
        except Exception as e:
            print(f"Note: {e}")
            print("Database may already exist, continuing...")
    
    # Connect to the test database
    test_db_url = f"postgresql+asyncpg://postgres:postgres@{db_host}:5432/ai_secretary_test"
    test_engine = create_async_engine(test_db_url, echo=True)
    
    async with test_engine.begin() as conn:
        # Create users table
        await conn.execute(text("""
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
        );
        """))
        print("Users table created successfully")
        
        # Insert test user
        await conn.execute(text("""
        INSERT INTO users (id, email, google_id, full_name, twilio_number, user_number, is_active, calendar_connected, timezone)
        VALUES ('a2d7200a-e061-460a-b5a2-afc47344caa9', 'test_user_1@example.com', 'google_id_1', 'Test User 1', '+15550000001', '+15551110001', TRUE, FALSE, 'UTC')
        ON CONFLICT (id) DO NOTHING;
        """))
        print("Test user inserted successfully")
    
    print("Test database setup complete!")

if __name__ == "__main__":
    asyncio.run(init_test_db()) 