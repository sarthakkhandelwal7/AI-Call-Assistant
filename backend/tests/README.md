# Testing Documentation

This directory contains all test files and utilities for the AI Call Assistant. All testing code should remain in this directory and should not be included or referenced in the main application code.

## Directory Structure

-   `data/` - Test data files and database setup scripts
-   `stress_tests/` - Stress and load testing utilities
-   `unit/` - Unit tests for individual components

## Setting Up The Test Environment

To set up a dedicated test environment:

```bash
# From project root
./switch-env.sh test

# Initialize test database
docker exec -it ai-call-assistant-backend-1 python tests/data/init_test_db.py
```

## Running Tests

### Stress Tests

Stress tests help evaluate performance under various load conditions:

```bash
docker exec -it ai-call-assistant-backend-1 python tests/stress_tests/run_tests.py --test-type [test_type] [options]
```

Available test types:

-   `http_basic` - Basic HTTP endpoint tests (no WebSockets)
-   `throughput` - Audio streaming throughput tests
-   `resilience` - Error handling tests
-   `load` - Increasing load tests
-   `high_concurrency` - High concurrent user tests
-   `wave_pattern` - Variable load pattern tests
-   `burst_pattern` - Sudden burst tests
-   `stability` - Long-duration stability tests
-   `resource_monitoring` - System resource monitoring tests

Example:

```bash
docker exec -it ai-call-assistant-backend-1 python tests/stress_tests/run_tests.py --test-type load --max-batch 30 --increment 10 --verbose
```

## Important Notes

1. Test code should NEVER be executed in production.
2. Tests use dedicated test users with UUIDs that should not be hardcoded in production code.
3. All test-specific environment variables should only be set in the `.env.test` file.
4. Test phone numbers (starting with +15550...) are not real numbers and will not work in production.
