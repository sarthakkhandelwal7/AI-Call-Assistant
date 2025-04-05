# AI Call Assistant Stress Testing Framework

This directory contains a comprehensive stress testing framework for the AI Call Assistant backend. These tests are designed to evaluate the system's performance, resilience, and stability under various load conditions.

## Overview

The stress testing framework provides several specialized test types designed to evaluate different aspects of the system:

1. **HTTP Basic Test** - Verifies basic HTTP connectivity
2. **Throughput Test** - Measures audio streaming throughput
3. **Resilience Test** - Tests the system's ability to handle errors
4. **Load Test** - Evaluates performance with gradually increasing load
5. **High Concurrency Test** - Tests the system with many simultaneous calls
6. **Wave Pattern Test** - Simulates realistic call volume patterns
7. **Burst Pattern Test** - Evaluates handling of sudden traffic spikes
8. **Stability Test** - Tests system stability over extended periods
9. **Resource Monitoring Test** - Identifies specific system bottlenecks

## Running Tests

Tests can be run using the `run_tests.py` script, which provides a convenient wrapper around the underlying `run_server_tests.py` implementation.

Basic usage:

```bash
python tests/stress_tests/run_tests.py --test-type [test_type] [options]
```

### Common Options

-   `--test-type` - Type of test to run (default: "throughput" on Linux/macOS, "http_basic" on Windows)
-   `--verbose, -v` - Enable verbose output
-   `--num-calls, -n` - Number of concurrent calls (default: 3)
-   `--duration, -d` - Duration of each call in seconds (default: 5)
-   `--chunk-size, -c` - Size of each audio chunk in KB (default: 2)
-   `--output, -o` - File to save test results in JSON format

## Detailed Test Descriptions

### HTTP Basic Test

**Purpose**: Verifies basic HTTP connectivity without WebSockets. Useful for initial connectivity checks and for testing on Windows systems that might have issues with WebSockets.

**Parameters**:

-   No specific parameters (uses HTTP GET requests to `/healthcheck`)

**Example**:

```bash
python tests/stress_tests/run_tests.py --test-type http_basic -v
```

**Results Interpretation**:

-   Success rate: Percentage of successful HTTP requests
-   Total requests: Number of HTTP requests made (default: 10)
-   Docs accessible: Whether the `/docs` endpoint is accessible
-   Total test duration: Time taken to complete the test

### Throughput Test

**Purpose**: Measures the system's ability to handle audio streaming throughput by simulating concurrent calls sending audio data.

**Parameters**:

-   `--num-calls, -n` - Number of concurrent calls (default: 3)
-   `--duration, -d` - Duration of each call in seconds (default: 5)
-   `--chunk-size, -c` - Size of each audio chunk in KB (default: 2)
-   `--interval` - Interval between chunks in milliseconds (default: 200)

**Example**:

```bash
python tests/stress_tests/run_tests.py --test-type throughput --num-calls 5 --duration 10 -v
```

**Results Interpretation**:

-   Success rate: Percentage of calls that completed successfully
-   Total data sent: Amount of audio data transferred in MB
-   Total chunks sent: Number of audio chunks sent
-   Total test duration: Time taken to complete the test

### Resilience Test

**Purpose**: Tests the system's ability to handle and recover from errors by deliberately introducing faults during audio streaming.

**Parameters**:

-   `--num-calls, -n` - Number of concurrent calls (default: 3)
-   `--duration, -d` - Duration of each call in seconds (default: 5)
-   `--error-rate` - Probability of simulated errors (0.0-1.0, default: 0.2)

**Example**:

```bash
python tests/stress_tests/run_tests.py --test-type resilience --error-rate 0.3 -v
```

**Results Interpretation**:

-   Success rate: Percentage of calls that completed successfully despite errors
-   Total simulated errors: Number of errors introduced during the test
-   Total test duration: Time taken to complete the test

### Load Test

**Purpose**: Evaluates system performance with gradually increasing load to identify the maximum capacity.

**Parameters**:

-   `--max-batch` - Maximum number of concurrent calls (default: 10)
-   `--increment` - Number of calls to add in each batch (default: 2)
-   `--duration, -d` - Duration of each call in seconds (default: 5)

**Example**:

```bash
python tests/stress_tests/run_tests.py --test-type load --max-batch 20 --increment 5 -v
```

**Results Interpretation**:

-   Overall success rate: Percentage of all calls that completed successfully
-   Maximum acceptable batch size: Largest batch size with ≥80% success rate
-   Batch results: Success rate for each batch size tested
-   Total test duration: Time taken to complete the test

### High Concurrency Test

**Purpose**: Tests the system's ability to handle a large number of simultaneous calls by running batches of concurrent calls.

**Parameters**:

-   `--num-calls, -n` - Total number of concurrent calls (default: 3)
-   `--duration, -d` - Duration of each call in seconds (default: 5)
-   `--chunk-size, -c` - Size of each audio chunk in KB (default: 2)
-   `--interval` - Interval between chunks in milliseconds (default: 200)

**Example**:

```bash
python tests/stress_tests/run_tests.py --test-type high_concurrency --num-calls 50 -v
```

**Results Interpretation**:

-   Success rate: Percentage of calls that completed successfully
-   Total data sent: Amount of audio data transferred in MB
-   Total chunks sent: Number of audio chunks sent
-   Total test duration: Time taken to complete the test

### Wave Pattern Test

**Purpose**: Simulates realistic call volume patterns with alternating peaks and valleys to evaluate system performance under varying load conditions.

**Parameters**:

-   `--peak-calls` - Maximum number of concurrent calls at peak (default: 10)
-   `--num-waves` - Number of waves to simulate (default: 3)
-   `--wave-duration` - Duration of each wave in seconds (default: 10)
-   `--chunk-size, -c` - Size of each audio chunk in KB (default: 2)
-   `--interval` - Interval between chunks in milliseconds (default: 200)

**Example**:

```bash
python tests/stress_tests/run_tests.py --test-type wave_pattern --peak-calls 15 --num-waves 5 -v
```

**Results Interpretation**:

-   Overall success rate: Percentage of all calls that completed successfully
-   Wave results: Success rate for each wave (peak and valley)
-   Total calls: Total number of calls across all waves
-   Total test duration: Time taken to complete the test

### Burst Pattern Test

**Purpose**: Evaluates the system's ability to handle sudden spikes in traffic by simulating bursts of calls with short ramp-up periods.

**Parameters**:

-   `--burst-size` - Number of calls in each burst (default: 10)
-   `--num-bursts` - Number of bursts to simulate (default: 3)
-   `--ramp-up-ms` - How quickly to ramp up the burst in milliseconds (default: 500)
-   `--rest-seconds` - Seconds to rest between bursts (default: 5)
-   `--duration, -d` - Duration of each call in seconds (default: 5)

**Example**:

```bash
python tests/stress_tests/run_tests.py --test-type burst_pattern --burst-size 20 --ramp-up-ms 200 -v
```

**Results Interpretation**:

-   Overall success rate: Percentage of all calls that completed successfully
-   Burst results: Success rate for each burst
-   Total calls: Total number of calls across all bursts
-   Total test duration: Time taken to complete the test

### Stability Test

**Purpose**: Tests system stability over extended periods with varying loads to evaluate long-term performance and resource usage.

**Parameters**:

-   `--test-duration-minutes` - Total test duration in minutes (default: 5)
-   `--base-calls` - Baseline number of concurrent calls (default: 3)
-   `--peak-calls` - Peak number of concurrent calls (default: 10)
-   `--chunk-size, -c` - Size of each audio chunk in KB (default: 2)
-   `--interval` - Interval between chunks in milliseconds (default: 200)

**Example**:

```bash
python tests/stress_tests/run_tests.py --test-type stability --test-duration-minutes 30 --base-calls 5 --peak-calls 15 -v
```

**Results Interpretation**:

-   Overall success rate: Percentage of all calls that completed successfully
-   Phase results: Success rate for each phase (base and peak)
-   Memory usage: Memory consumption at the end of the test
-   Total test duration: Time taken to complete the test

### Resource Monitoring Test

**Purpose**: Identifies specific system bottlenecks by monitoring detailed resource utilization metrics during load testing. This helps pinpoint the exact resource limitations causing performance degradation.

**Parameters**:

-   `--num-calls, -n` - Number of concurrent calls (default: 3)
-   `--duration, -d` - Duration of each call in seconds (default: 5)
-   `--chunk-size, -c` - Size of each audio chunk in KB (default: 2)
-   `--interval` - Interval between chunks in milliseconds (default: 200)
-   `--monitor-interval` - How often to sample resource metrics in seconds (default: 1)

**Example**:

```bash
python tests/stress_tests/run_tests.py --test-type resource_monitoring --num-calls 20 --duration 30 -v
```

**Results Interpretation**:

-   Resource statistics:
    -   Peak CPU usage: Maximum CPU utilization percentage
    -   Peak memory usage: Maximum memory consumption in MB
    -   Peak thread count: Maximum number of threads used
    -   Peak open files: Maximum number of file descriptors open
    -   Network I/O: Total network data sent/received in MB
-   Bottleneck detection:
    -   Lists specific resources that exceeded predefined thresholds
    -   CPU usage > 80%
    -   Memory usage > 1GB
    -   Thread count > 100
    -   Open files > 500
-   Success rate: Percentage of calls that completed successfully
-   Total test duration: Time taken to complete the test

## Best Practices for Testing

1. **Start with Basic Tests**: Begin with the HTTP basic test to ensure basic connectivity.
2. **Throughput Testing**: Use throughput tests to establish baseline performance.
3. **Load Testing**: Run load tests to determine maximum capacity.
4. **Error Handling**: Use resilience tests to verify error handling mechanisms.
5. **Real-world Patterns**: Use wave and burst pattern tests to simulate realistic scenarios.
6. **Extended Testing**: Run stability tests for at least 30 minutes before production deployment.
7. **Bottleneck Identification**: Use resource monitoring tests when performance drops to identify the specific limiting factor.

## Database Connection Pool Settings

The AI Call Assistant uses a configurable database connection pool to optimize performance under varying loads. These settings are defined in environment files and can be adjusted based on the environment:

### Settings in Environment Files

Each environment (development, test, production) has its own optimized connection pool settings:

```
# Database Connection Pool Settings
DB_POOL_SIZE=<number>         # Number of connections kept in the pool
DB_MAX_OVERFLOW=<number>      # Maximum extra connections allowed when pool is exhausted
DB_POOL_TIMEOUT=<seconds>     # How long to wait for a connection when pool is exhausted
DB_POOL_RECYCLE=<seconds>     # Recycle connections after this many seconds
```

### Recommended Values

| Environment | Pool Size | Max Overflow | Pool Timeout | Pool Recycle |
| ----------- | --------- | ------------ | ------------ | ------------ |
| Development | 10        | 10           | 30           | 1800         |
| Testing     | 40        | 20           | 30           | 1800         |
| Production  | 50        | 25           | 30           | 1800         |

### Adjusting for Performance

If the load tests show degraded performance with concurrent calls:

1. Check the resource monitoring test results to identify bottlenecks
2. If database connections are the bottleneck, increase `DB_POOL_SIZE` and `DB_MAX_OVERFLOW`
3. Re-run load tests to verify improvements
4. Monitor in production to fine-tune these values

## Interpreting Test Results

-   **Success Rate < 70%**: System is overloaded and cannot handle the current load.
-   **Success Rate 70-80%**: System is reaching capacity; consider scaling.
-   **Success Rate > 80%**: System is handling the load adequately.
-   **Success Rate 100%**: System has excess capacity.

## Example Test Scenarios

### Basic Connectivity Check

```bash
python tests/stress_tests/run_tests.py --test-type http_basic --verbose
```

### Performance Baseline

```bash
python tests/stress_tests/run_tests.py --test-type throughput --num-calls 5 --duration 10 --verbose
```

### Maximum Capacity Test

```bash
python tests/stress_tests/run_tests.py --test-type load --max-batch 30 --increment 5 --verbose
```

### High Volume Test

```bash
python tests/stress_tests/run_tests.py --test-type high_concurrency --num-calls 100 --verbose
```

### Production Readiness Test

```bash
python tests/stress_tests/run_tests.py --test-type stability --test-duration-minutes 60 --base-calls 10 --peak-calls 30 --verbose
```

### Bottleneck Identification

```bash
python tests/stress_tests/run_tests.py --test-type resource_monitoring --num-calls 20 --duration 30 --verbose
```
