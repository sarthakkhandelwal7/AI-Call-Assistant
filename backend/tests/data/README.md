# Test Data and Utilities

This directory contains files used for testing purposes ONLY. These files should NOT be used in production code.

## Files

-   `init_test_db.py` - Script to initialize a test database with sample data
-   `setup_test_db.sh` - Shell script to set up test database tables
-   `populate_test_db.sql` - SQL script with sample user data for testing

## Using Test Data

To set up a test database for development or testing:

```bash
# From project root directory
cd backend/tests/data
python init_test_db.py
```

Or to run with docker:

```bash
docker exec -it ai-call-assistant-backend-1 python tests/data/init_test_db.py
```

## Important Notes

1. The test data contains synthetic users with test phone numbers that do not work in production.
2. Never import or use these testing utilities in production code.
3. Test data should only be used in test databases, never in production databases.
4. The test user IDs and credentials are not secure and should not be used outside of testing.

## Running Stress Tests

To run stress tests that require test data:

```bash
cd backend/tests/stress_tests
python run_tests.py --test-type [test_type]
```

See the stress tests documentation for more details on available test types and parameters.
