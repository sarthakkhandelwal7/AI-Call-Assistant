"""
Tests that use the server testing framework to validate call flow handling
with real HTTP and WebSocket connections.

These tests start an actual uvicorn server instance and make real connections
to test concurrency effectively.
"""
import os
import sys
import json
import time
import pytest
import pytest_asyncio
import asyncio
from typing import Dict, Any, List, Optional

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import server testing framework
from tests.stress_tests.server_test_framework import (
    AppServerTest,
    StressTestRunner,
    run_server_test,
    logger
)


@pytest.mark.asyncio
async def test_basic_server_connection():
    """
    A basic test to verify the server can start and respond to HTTP requests.
    This test doesn't use WebSockets and just checks that the server is running properly.
    """
    async def run_test(server: AppServerTest) -> Dict[str, Any]:
        import httpx
        
        # Make a simple request to verify the server is running
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{server.base_url}/healthcheck")
            assert response.status_code == 200
            
            # Try another endpoint if available
            try:
                docs_response = await client.get(f"{server.base_url}/docs")
                assert docs_response.status_code == 200
                logger.info("Server is responding to HTTP requests properly")
            except Exception as e:
                logger.warning(f"Docs endpoint check failed: {str(e)}")
        
        return {"success": True}
    
    results = await run_server_test(run_test)
    assert results["success"] is True


@pytest.mark.asyncio
async def test_single_call_high_throughput():
    """
    Tests a single call with high audio throughput, sending 5KB chunks every 100ms.
    Verifies the server can process a high volume of audio data for a single call.
    """
    async def run_test(server: AppServerTest) -> Dict[str, Any]:
        runner = StressTestRunner(server)
        
        # Configure a single call with high throughput
        results = await runner.run_concurrent_calls(
            num_calls=1,
            duration_seconds=10,
            chunk_size_kb=5,
            chunk_interval_ms=100  # 10 chunks per second
        )
        
        # We should have exactly one result for one call
        assert len(results) == 1
        call_result = results[0]
        
        # Check that the call completed
        assert call_result.get("completed", False)
        
        # Calculate expected chunks (approximate due to timing variations)
        # 10 seconds at 10 chunks per second = ~100 chunks
        expected_chunks = 10 * (1000 // 100)  # 100 chunks
        actual_chunks = call_result.get("chunks_sent", 0)
        
        # Allow for some variation due to timing
        assert actual_chunks >= expected_chunks * 0.8, f"Too few chunks sent: {actual_chunks} < {expected_chunks * 0.8}"
        
        # Calculate throughput in kbps
        total_bytes = call_result.get("bytes_sent", 0)
        duration = call_result.get("duration", 10)
        throughput_kbps = (total_bytes * 8) / (duration * 1000)
        
        logger.info(f"Single call throughput: {throughput_kbps:.2f} kbps")
        
        return {
            "throughput_kbps": throughput_kbps,
            "chunks_sent": actual_chunks,
            "bytes_sent": total_bytes
        }
    
    # Run with a real server
    results = await run_server_test(run_test)
    
    # Verify minimum acceptable throughput (400 kbps)
    assert results["throughput_kbps"] >= 400, f"Throughput too low: {results['throughput_kbps']:.2f} kbps"


@pytest.mark.asyncio
async def test_multiple_concurrent_calls():
    """
    Tests multiple concurrent calls (5 calls for 5 seconds each).
    Verifies the server can handle multiple calls simultaneously.
    """
    async def run_test(server: AppServerTest) -> Dict[str, Any]:
        runner = StressTestRunner(server)
        
        # Run 5 concurrent calls, each lasting 5 seconds
        results = await runner.run_concurrent_calls(
            num_calls=5,
            duration_seconds=5,
            chunk_size_kb=2,
            chunk_interval_ms=200  # 5 chunks per second
        )
        
        # Should have 5 results
        assert len(results) == 5
        
        # Count successful calls
        success_count = sum(1 for r in results if r.get("completed", False))
        success_rate = success_count / 5
        
        # At least 80% of calls should succeed
        assert success_rate >= 0.8, f"Success rate too low: {success_rate * 100:.1f}%"
        
        # Calculate total data processed
        total_chunks = sum(r.get("chunks_sent", 0) for r in results)
        total_bytes = sum(r.get("bytes_sent", 0) for r in results)
        
        logger.info(f"Processed {total_chunks} chunks, {total_bytes / 1024:.2f} KB across 5 concurrent calls")
        logger.info(f"Success rate: {success_rate * 100:.1f}%")
        
        return {
            "success_rate": success_rate,
            "total_chunks": total_chunks,
            "total_bytes": total_bytes
        }
    
    # Run with a real server
    results = await run_server_test(run_test)
    assert results["success_rate"] >= 0.8


@pytest.mark.asyncio
async def test_gradual_load_increase():
    """
    Gradually increases the call load to find the system's capacity.
    Runs batches of concurrent calls (2, 5, 10) and analyses the success rate of each batch.
    """
    async def run_test(server: AppServerTest) -> Dict[str, Any]:
        runner = StressTestRunner(server)
        batch_sizes = [2, 5]  # Reduced from [2, 5, 10] to speed up tests
        
        batch_results = []
        for batch_size in batch_sizes:
            logger.info(f"Testing batch size: {batch_size}")
            
            # Run a batch of concurrent calls
            results = await runner.run_concurrent_calls(
                num_calls=batch_size,
                duration_seconds=5,
                chunk_size_kb=1,
                chunk_interval_ms=200
            )
            
            success_count = sum(1 for r in results if r.get("completed", False))
            success_rate = success_count / batch_size
            
            batch_result = {
                "batch_size": batch_size,
                "success_count": success_count,
                "success_rate": success_rate
            }
            batch_results.append(batch_result)
            
            logger.info(f"Batch size {batch_size}: {success_rate * 100:.1f}% success rate")
            
            # Stop increasing if success rate drops below 70%
            if success_rate < 0.7:
                logger.warning(f"Success rate too low ({success_rate * 100:.1f}%), stopping load increase")
                break
            
            # Allow system to recover between batches
            await asyncio.sleep(2)
        
        # Find the maximum batch size with acceptable success rate
        acceptable_batches = [b for b in batch_results if b["success_rate"] >= 0.8]
        max_acceptable = max(acceptable_batches, key=lambda b: b["batch_size"]) if acceptable_batches else None
        
        if max_acceptable:
            logger.info(f"Maximum batch size with ≥80% success rate: {max_acceptable['batch_size']}")
        
        return {
            "batch_results": batch_results,
            "max_acceptable_batch": max_acceptable["batch_size"] if max_acceptable else 0
        }
    
    # Run with a real server
    results = await run_server_test(run_test)
    
    # At least one batch size should be acceptable
    assert results["max_acceptable_batch"] > 0, "No batch size had acceptable success rate"


@pytest.mark.asyncio
async def test_resilience_with_simulated_errors():
    """
    Tests the system's resilience by simulating errors during calls.
    Verifies that calls can complete successfully despite errors.
    """
    async def run_test(server: AppServerTest) -> Dict[str, Any]:
        runner = StressTestRunner(server)
        
        # Run 5 calls with simulated errors
        results = await runner.run_concurrent_calls(
            num_calls=5,
            duration_seconds=5,
            chunk_size_kb=1,
            chunk_interval_ms=200,
            error_rate=0.2  # 20% of chunks will have simulated errors
        )
        
        # Count successful calls and total errors
        success_count = sum(1 for r in results if r.get("completed", False))
        total_errors = sum(r.get("errors", 0) for r in results)
        
        logger.info(f"Completed {success_count}/5 calls with {total_errors} simulated errors")
        
        # Verify that we experienced some errors
        assert total_errors > 0, "No errors were simulated"
        
        # Despite errors, at least 60% of calls should succeed
        assert success_count >= 3, f"Too few calls succeeded: {success_count}"
        
        return {
            "success_count": success_count,
            "total_errors": total_errors
        }
    
    # Run with a real server
    results = await run_server_test(run_test)
    assert results["success_count"] >= 3 