#!/usr/bin/env python
"""
Command-line script to run server-based stress tests.

This script provides a convenient way to run stress tests
that use a real server instance rather than TestClient.
"""

import os
import sys
import asyncio
import argparse
import time
import json
import traceback
import platform
from typing import Dict, Any, List, Optional
import logging
import psutil
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("server_tests")

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from tests.stress_tests.server_test_framework import (
        AppServerTest,
        StressTestRunner,
        logger as framework_logger
    )
except ImportError as e:
    logger.error(f"Failed to import server test framework: {str(e)}")
    logger.error(f"Python path: {sys.path}")
    traceback.print_exc()
    sys.exit(1)

# Test database configuration
DEFAULT_DB_URL = os.environ.get(
    "TEST_DATABASE_URL", 
    "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_secretary_test"
)


async def run_http_basic_test(
    database_url: str
) -> Dict[str, Any]:
    """
    Run a simple HTTP-only test to verify server connectivity.
    This is useful for Windows systems that might have issues with WebSockets.
    
    Args:
        database_url: PostgreSQL connection URL for the test database
        
    Returns:
        Dictionary with test results
    """
    logger.info(f"Starting basic HTTP connectivity test")
    
    try:
        with AppServerTest(database_url=database_url) as server:
            logger.info(f"Server started at {server.base_url}")
            
            import httpx
            
            start_time = time.time()
            success_count = 0
            total_requests = 10
            
            # Make several HTTP requests to verify server is functioning
            async with httpx.AsyncClient() as client:
                for i in range(total_requests):
                    try:
                        response = await client.get(f"{server.base_url}/healthcheck")
                        if response.status_code == 200:
                            success_count += 1
                            logger.info(f"Request {i+1}/{total_requests}: Success")
                        else:
                            logger.warning(f"Request {i+1}/{total_requests}: Failed with status {response.status_code}")
                    except Exception as e:
                        logger.error(f"Request {i+1}/{total_requests}: Error - {str(e)}")
                    
                    # Add a small delay between requests
                    await asyncio.sleep(0.1)
            
            total_duration = time.time() - start_time
            success_rate = success_count / total_requests
            
            logger.info(f"HTTP test completed: {success_count}/{total_requests} requests successful "
                       f"({success_rate*100:.1f}%)")
            
            summary = {
                "test_type": "http_basic",
                "total_requests": total_requests,
                "success_count": success_count,
                "success_rate": success_rate,
                "total_test_duration": total_duration
            }
            
            # Try to access the docs page as an additional test
            try:
                docs_response = await client.get(f"{server.base_url}/docs")
                summary["docs_accessible"] = (docs_response.status_code == 200)
                logger.info(f"Docs page {'accessible' if summary['docs_accessible'] else 'not accessible'}")
            except Exception as e:
                logger.warning(f"Could not access docs page: {str(e)}")
                summary["docs_accessible"] = False
            
            return summary
    except Exception as e:
        logger.error(f"Error in HTTP basic test: {str(e)}")
        traceback.print_exc()
        return {
            "test_type": "http_basic",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


async def run_throughput_test(
    database_url: str,
    num_calls: int,
    duration: int,
    chunk_size: int,
    interval: int
) -> Dict[str, Any]:
    """
    Run a throughput test with the specified parameters.
    
    Args:
        database_url: PostgreSQL connection URL for the test database
        num_calls: Number of concurrent calls to simulate
        duration: Duration of each call in seconds
        chunk_size: Size of each audio chunk in KB
        interval: Interval between chunks in milliseconds
        
    Returns:
        Dictionary with test results
    """
    logger.info(f"Starting throughput test with {num_calls} concurrent calls, "
               f"{duration}s duration, {chunk_size}KB chunks every {interval}ms")
    
    try:
        with AppServerTest(database_url=database_url) as server:
            logger.info(f"Server started at {server.base_url}")
            
            runner = StressTestRunner(server)
            start_time = time.time()
            
            results = await runner.run_concurrent_calls(
                num_calls=num_calls,
                duration_seconds=duration,
                chunk_size_kb=chunk_size,
                chunk_interval_ms=interval
            )
            
            total_duration = time.time() - start_time
            success_count = sum(1 for r in results if r.get("completed", False))
            success_rate = success_count / num_calls if num_calls > 0 else 0
            
            total_chunks = sum(r.get("chunks_sent", 0) for r in results if not isinstance(r, Exception))
            total_bytes = sum(r.get("bytes_sent", 0) for r in results if not isinstance(r, Exception))
            
            logger.info(f"Throughput test completed: {success_count}/{num_calls} calls successful "
                       f"({success_rate*100:.1f}%), sent {total_chunks} chunks, "
                       f"{total_bytes/(1024*1024):.2f}MB of data")
            
            summary = {
                "test_type": "throughput",
                "num_calls": num_calls,
                "duration_seconds": duration,
                "chunk_size_kb": chunk_size,
                "interval_ms": interval,
                "total_test_duration": total_duration,
                "success_count": success_count,
                "success_rate": success_rate,
                "total_chunks_sent": total_chunks,
                "total_data_sent_mb": total_bytes / (1024 * 1024),
                "individual_results": results
            }
            
            return summary
    except Exception as e:
        logger.error(f"Error in throughput test: {str(e)}")
        traceback.print_exc()
        return {
            "test_type": "throughput",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


async def run_resilience_test(
    database_url: str,
    num_calls: int,
    duration: int,
    error_rate: float
) -> Dict[str, Any]:
    """
    Run a resilience test with the specified parameters.
    
    Args:
        database_url: PostgreSQL connection URL for the test database
        num_calls: Number of concurrent calls to simulate
        duration: Duration of each call in seconds
        error_rate: Probability of simulated errors (0.0-1.0)
        
    Returns:
        Dictionary with test results
    """
    logger.info(f"Starting resilience test with {num_calls} concurrent calls, "
               f"{duration}s duration, {error_rate*100:.1f}% error rate")
    
    try:
        with AppServerTest(database_url=database_url) as server:
            logger.info(f"Server started at {server.base_url}")
            
            runner = StressTestRunner(server)
            start_time = time.time()
            
            results = await runner.run_concurrent_calls(
                num_calls=num_calls,
                duration_seconds=duration,
                chunk_size_kb=2,  # Fixed size for resilience tests
                chunk_interval_ms=200,  # Fixed interval for resilience tests
                error_rate=error_rate
            )
            
            total_duration = time.time() - start_time
            success_count = sum(1 for r in results if r.get("completed", False))
            success_rate = success_count / num_calls if num_calls > 0 else 0
            
            total_errors = sum(r.get("errors", 0) for r in results if not isinstance(r, Exception))
            
            logger.info(f"Resilience test completed: {success_count}/{num_calls} calls successful "
                      f"({success_rate*100:.1f}%), simulated {total_errors} errors")
            
            summary = {
                "test_type": "resilience",
                "num_calls": num_calls,
                "duration_seconds": duration,
                "error_rate": error_rate,
                "total_test_duration": total_duration,
                "success_count": success_count,
                "success_rate": success_rate,
                "total_simulated_errors": total_errors,
                "individual_results": results
            }
            
            return summary
    except Exception as e:
        logger.error(f"Error in resilience test: {str(e)}")
        traceback.print_exc()
        return {
            "test_type": "resilience",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


async def run_load_test(
    database_url: str,
    max_batch_size: int,
    increment: int,
    duration: int
) -> Dict[str, Any]:
    """
    Run a load test that gradually increases call volume.
    
    Args:
        database_url: PostgreSQL connection URL for the test database
        max_batch_size: Maximum number of concurrent calls
        increment: How many calls to add in each batch
        duration: Duration of each call in seconds
        
    Returns:
        Dictionary with test results
    """
    logger.info(f"Starting load test with max batch size {max_batch_size}, "
               f"increments of {increment}, {duration}s duration per batch")
    
    try:
        with AppServerTest(database_url=database_url) as server:
            logger.info(f"Server started at {server.base_url}")
            
            runner = StressTestRunner(server)
            start_time = time.time()
            
            summary = {
                "test_type": "load",
                "max_batch_size": max_batch_size,
                "increment": increment,
                "duration_seconds": duration,
                "total_calls": 0,
                "successful_calls": 0,
                "batches": []
            }
            
            # Start with increment and increase by increment until max_batch_size
            for batch_size in range(increment, max_batch_size + 1, increment):
                logger.info(f"Testing batch size: {batch_size}")
                
                # Run a batch of concurrent calls
                results = await runner.run_concurrent_calls(
                    num_calls=batch_size,
                    duration_seconds=duration,
                    chunk_size_kb=1,
                    chunk_interval_ms=200
                )
                
                # Analyze results
                success_count = sum(1 for r in results if r.get("completed", False))
                success_rate = success_count / batch_size
                
                batch_summary = {
                    "batch_size": batch_size,
                    "success_count": success_count,
                    "success_rate": success_rate
                }
                
                summary["batches"].append(batch_summary)
                summary["total_calls"] += batch_size
                summary["successful_calls"] += success_count
                
                logger.info(f"Batch size {batch_size}: {success_rate * 100:.1f}% success rate")
                
                # Allow system to recover between batches
                await asyncio.sleep(3)
                
                # Stop increasing if success rate drops too low
                if success_rate < 0.7:
                    logger.warning(f"Success rate dropped below 70% at batch size {batch_size}, stopping test")
                    break
            
            total_duration = time.time() - start_time
            overall_success_rate = summary["successful_calls"] / summary["total_calls"] if summary["total_calls"] > 0 else 0
            
            summary["total_test_duration"] = total_duration
            summary["overall_success_rate"] = overall_success_rate
            
            # Find the maximum batch size with acceptable success rate
            acceptable_batches = [b for b in summary["batches"] if b["success_rate"] >= 0.8]
            max_acceptable = max(acceptable_batches, key=lambda b: b["batch_size"]) if acceptable_batches else None
            
            if max_acceptable:
                logger.info(f"Maximum batch size with ≥80% success rate: {max_acceptable['batch_size']}")
                summary["max_acceptable_batch"] = max_acceptable["batch_size"]
            else:
                logger.warning("No batch size achieved ≥80% success rate")
                summary["max_acceptable_batch"] = 0
            
            return summary
    except Exception as e:
        logger.error(f"Error in load test: {str(e)}")
        traceback.print_exc()
        return {
            "test_type": "load",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


async def run_high_concurrency_test(
    database_url: str,
    num_calls: int,
    duration: int,
    chunk_size: int,
    interval: int
) -> Dict[str, Any]:
    """
    Run a high concurrency test with a large number of simultaneous calls.
    
    Args:
        database_url: PostgreSQL connection URL for the test database
        num_calls: Number of concurrent calls to simulate (can be very high)
        duration: Duration of each call in seconds
        chunk_size: Size of each audio chunk in KB
        interval: Interval between chunks in milliseconds
        
    Returns:
        Dictionary with test results
    """
    logger.info(f"Starting high concurrency test with {num_calls} concurrent calls, "
               f"{duration}s duration, {chunk_size}KB chunks every {interval}ms")
    
    try:
        with AppServerTest(database_url=database_url) as server:
            logger.info(f"Server started at {server.base_url}")
            
            runner = StressTestRunner(server)
            start_time = time.time()
            
            # Split the calls into batches to avoid overwhelming the system all at once
            batch_size = 20  # Process 20 calls at a time
            results = []
            
            for batch_start in range(0, num_calls, batch_size):
                batch_end = min(batch_start + batch_size, num_calls)
                batch_count = batch_end - batch_start
                
                logger.info(f"Running batch {batch_start//batch_size + 1}: calls {batch_start+1}-{batch_end} "
                           f"({batch_count} calls)")
                
                # Start this batch with a small delay from previous batch
                if batch_start > 0:
                    await asyncio.sleep(1)
                
                batch_results = await runner.run_concurrent_calls(
                    num_calls=batch_count,
                    duration_seconds=duration,
                    chunk_size_kb=chunk_size,
                    chunk_interval_ms=interval
                )
                
                results.extend(batch_results)
            
            total_duration = time.time() - start_time
            success_count = sum(1 for r in results if r.get("completed", False))
            success_rate = success_count / num_calls if num_calls > 0 else 0
            
            total_chunks = sum(r.get("chunks_sent", 0) for r in results if not isinstance(r, Exception))
            total_bytes = sum(r.get("bytes_sent", 0) for r in results if not isinstance(r, Exception))
            
            logger.info(f"High concurrency test completed: {success_count}/{num_calls} calls successful "
                       f"({success_rate*100:.1f}%), sent {total_chunks} chunks, "
                       f"{total_bytes/(1024*1024):.2f}MB of data")
            
            summary = {
                "test_type": "high_concurrency",
                "num_calls": num_calls,
                "duration_seconds": duration,
                "chunk_size_kb": chunk_size,
                "interval_ms": interval,
                "total_test_duration": total_duration,
                "success_count": success_count,
                "success_rate": success_rate,
                "total_chunks_sent": total_chunks,
                "total_data_sent_mb": total_bytes / (1024 * 1024),
                "individual_results": results
            }
            
            return summary
    except Exception as e:
        logger.error(f"Error in high concurrency test: {str(e)}")
        traceback.print_exc()
        return {
            "test_type": "high_concurrency",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


async def run_wave_pattern_test(
    database_url: str,
    peak_calls: int,
    num_waves: int,
    wave_duration: int,
    chunk_size: int,
    interval: int
) -> Dict[str, Any]:
    """
    Run a wave pattern test that simulates realistic call volume patterns.
    
    Args:
        database_url: PostgreSQL connection URL for the test database
        peak_calls: Maximum number of concurrent calls at peak
        num_waves: Number of waves to simulate
        wave_duration: Duration of each wave in seconds
        chunk_size: Size of each audio chunk in KB
        interval: Interval between chunks in milliseconds
        
    Returns:
        Dictionary with test results
    """
    logger.info(f"Starting wave pattern test with peak of {peak_calls} calls, "
               f"{num_waves} waves of {wave_duration}s each")
    
    try:
        with AppServerTest(database_url=database_url) as server:
            logger.info(f"Server started at {server.base_url}")
            
            runner = StressTestRunner(server)
            start_time = time.time()
            all_results = []
            wave_summaries = []
            
            for wave in range(1, num_waves + 1):
                # Calculate calls for this wave - alternating between peak and half-peak
                current_calls = peak_calls if wave % 2 == 1 else peak_calls // 2
                
                logger.info(f"Wave {wave}/{num_waves}: Starting with {current_calls} concurrent calls")
                
                wave_start = time.time()
                results = await runner.run_concurrent_calls(
                    num_calls=current_calls,
                    duration_seconds=wave_duration,
                    chunk_size_kb=chunk_size,
                    chunk_interval_ms=interval
                )
                wave_duration_actual = time.time() - wave_start
                
                success_count = sum(1 for r in results if r.get("completed", False))
                success_rate = success_count / current_calls if current_calls > 0 else 0
                
                wave_summary = {
                    "wave": wave,
                    "num_calls": current_calls,
                    "success_count": success_count,
                    "success_rate": success_rate,
                    "duration": wave_duration_actual
                }
                wave_summaries.append(wave_summary)
                all_results.extend(results)
                
                logger.info(f"Wave {wave} completed: {success_rate*100:.1f}% success rate")
                
                # Brief pause between waves
                if wave < num_waves:
                    await asyncio.sleep(2)
            
            total_duration = time.time() - start_time
            total_calls = sum(wave["num_calls"] for wave in wave_summaries)
            total_success = sum(wave["success_count"] for wave in wave_summaries)
            overall_success_rate = total_success / total_calls if total_calls > 0 else 0
            
            total_chunks = sum(r.get("chunks_sent", 0) for r in all_results if not isinstance(r, Exception))
            total_bytes = sum(r.get("bytes_sent", 0) for r in all_results if not isinstance(r, Exception))
            
            logger.info(f"Wave pattern test completed: {total_success}/{total_calls} calls successful "
                       f"({overall_success_rate*100:.1f}%), sent {total_chunks} chunks, "
                       f"{total_bytes/(1024*1024):.2f}MB of data")
            
            summary = {
                "test_type": "wave_pattern",
                "peak_calls": peak_calls,
                "num_waves": num_waves,
                "wave_duration": wave_duration,
                "total_calls": total_calls,
                "total_success": total_success,
                "overall_success_rate": overall_success_rate,
                "total_test_duration": total_duration,
                "total_chunks_sent": total_chunks,
                "total_data_sent_mb": total_bytes / (1024 * 1024),
                "wave_summaries": wave_summaries,
                "individual_results": all_results
            }
            
            return summary
    except Exception as e:
        logger.error(f"Error in wave pattern test: {str(e)}")
        traceback.print_exc()
        return {
            "test_type": "wave_pattern",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


async def run_burst_pattern_test(
    database_url: str,
    burst_size: int,
    num_bursts: int,
    ramp_up_ms: int,
    rest_seconds: int,
    call_duration: int,
    chunk_size: int,
    interval: int
) -> Dict[str, Any]:
    """
    Run a burst pattern test that simulates sudden spikes in call volume.
    
    Args:
        database_url: PostgreSQL connection URL for the test database
        burst_size: Number of calls in each burst
        num_bursts: Number of bursts to simulate
        ramp_up_ms: How quickly to ramp up the burst (in milliseconds)
        rest_seconds: Seconds to rest between bursts
        call_duration: Duration of each call in seconds
        chunk_size: Size of each audio chunk in KB
        interval: Interval between chunks in milliseconds
        
    Returns:
        Dictionary with test results
    """
    logger.info(f"Starting burst pattern test with {burst_size} calls per burst, "
               f"{num_bursts} bursts, {ramp_up_ms}ms ramp-up")
    
    try:
        with AppServerTest(database_url=database_url) as server:
            logger.info(f"Server started at {server.base_url}")
            
            runner = StressTestRunner(server)
            start_time = time.time()
            all_results = []
            burst_summaries = []
            
            for burst in range(1, num_bursts + 1):
                logger.info(f"Burst {burst}/{num_bursts}: Starting with {burst_size} calls "
                           f"ramping up over {ramp_up_ms}ms")
                
                # For the burst pattern, we'll use the sequential load test with a short ramp-up
                burst_start = time.time()
                results = await runner.run_sequential_load_test(
                    num_calls=burst_size,
                    ramp_up_seconds=ramp_up_ms / 1000,  # Convert to seconds
                    duration_seconds=call_duration,
                    chunk_size_kb=chunk_size,
                    chunk_interval_ms=interval
                )
                burst_duration_actual = time.time() - burst_start
                
                success_count = sum(1 for r in results if r.get("completed", False))
                success_rate = success_count / burst_size if burst_size > 0 else 0
                
                burst_summary = {
                    "burst": burst,
                    "num_calls": burst_size,
                    "success_count": success_count,
                    "success_rate": success_rate,
                    "duration": burst_duration_actual
                }
                burst_summaries.append(burst_summary)
                all_results.extend(results)
                
                logger.info(f"Burst {burst} completed in {burst_duration_actual:.2f}s: "
                           f"{success_rate*100:.1f}% success rate")
                
                # Rest between bursts
                if burst < num_bursts:
                    logger.info(f"Resting for {rest_seconds}s before next burst")
                    await asyncio.sleep(rest_seconds)
            
            total_duration = time.time() - start_time
            total_calls = sum(burst["num_calls"] for burst in burst_summaries)
            total_success = sum(burst["success_count"] for burst in burst_summaries)
            overall_success_rate = total_success / total_calls if total_calls > 0 else 0
            
            total_chunks = sum(r.get("chunks_sent", 0) for r in all_results if not isinstance(r, Exception))
            total_bytes = sum(r.get("bytes_sent", 0) for r in all_results if not isinstance(r, Exception))
            
            logger.info(f"Burst pattern test completed: {total_success}/{total_calls} calls successful "
                       f"({overall_success_rate*100:.1f}%), sent {total_chunks} chunks, "
                       f"{total_bytes/(1024*1024):.2f}MB of data")
            
            summary = {
                "test_type": "burst_pattern",
                "burst_size": burst_size,
                "num_bursts": num_bursts,
                "ramp_up_ms": ramp_up_ms,
                "rest_seconds": rest_seconds,
                "call_duration": call_duration,
                "total_calls": total_calls,
                "total_success": total_success,
                "overall_success_rate": overall_success_rate,
                "total_test_duration": total_duration,
                "total_chunks_sent": total_chunks,
                "total_data_sent_mb": total_bytes / (1024 * 1024),
                "burst_summaries": burst_summaries,
                "individual_results": all_results
            }
            
            return summary
    except Exception as e:
        logger.error(f"Error in burst pattern test: {str(e)}")
        traceback.print_exc()
        return {
            "test_type": "burst_pattern",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


async def run_stability_test(
    database_url: str,
    test_duration_minutes: int,
    base_calls: int,
    peak_calls: int,
    chunk_size: int,
    interval: int
) -> Dict[str, Any]:
    """
    Run a stability test that exercises the system over a longer period with varying loads.
    
    Args:
        database_url: PostgreSQL connection URL for the test database
        test_duration_minutes: Total test duration in minutes
        base_calls: Baseline number of concurrent calls
        peak_calls: Peak number of concurrent calls during high load periods
        chunk_size: Size of each audio chunk in KB
        interval: Interval between chunks in milliseconds
        
    Returns:
        Dictionary with test results
    """
    logger.info(f"Starting stability test for {test_duration_minutes} minutes with "
               f"baseline of {base_calls} calls and peaks of {peak_calls} calls")
    
    try:
        with AppServerTest(database_url=database_url) as server:
            logger.info(f"Server started at {server.base_url}")
            
            runner = StressTestRunner(server)
            start_time = time.time()
            all_results = []
            phase_summaries = []
            
            # Calculate total number of phases - each phase is 1 minute
            total_phases = test_duration_minutes
            
            for phase in range(1, total_phases + 1):
                # Every third phase has peak load, others have base load
                current_calls = peak_calls if phase % 3 == 0 else base_calls
                phase_type = "peak" if phase % 3 == 0 else "base"
                
                logger.info(f"Phase {phase}/{total_phases} ({phase_type}): Starting with {current_calls} concurrent calls")
                
                phase_start = time.time()
                
                # For each phase, make calls with 30-second duration
                results = await runner.run_concurrent_calls(
                    num_calls=current_calls,
                    duration_seconds=30,
                    chunk_size_kb=chunk_size,
                    chunk_interval_ms=interval
                )
                
                # Rest for remaining time to complete the 1-minute phase
                phase_elapsed = time.time() - phase_start
                remaining_time = 60 - phase_elapsed  # Each phase should be 1 minute
                if remaining_time > 0:
                    logger.info(f"Waiting {remaining_time:.2f}s to complete the 1-minute phase")
                    await asyncio.sleep(remaining_time)
                
                phase_duration_actual = time.time() - phase_start
                
                success_count = sum(1 for r in results if r.get("completed", False))
                success_rate = success_count / current_calls if current_calls > 0 else 0
                
                phase_summary = {
                    "phase": phase,
                    "type": phase_type,
                    "num_calls": current_calls,
                    "success_count": success_count,
                    "success_rate": success_rate,
                    "duration": phase_duration_actual
                }
                phase_summaries.append(phase_summary)
                all_results.extend(results)
                
                # Check memory and log
                memory_info = psutil.Process().memory_info()
                logger.info(f"Phase {phase} completed: {success_rate*100:.1f}% success rate, "
                          f"Memory usage: {memory_info.rss / (1024*1024):.1f} MB")
                
                # Log a heartbeat message at the end of each phase
                elapsed_time = time.time() - start_time
                logger.info(f"Stability test running for {elapsed_time/60:.1f} minutes "
                          f"({phase}/{total_phases} phases complete)")
            
            total_duration = time.time() - start_time
            total_calls = sum(phase["num_calls"] for phase in phase_summaries)
            total_success = sum(phase["success_count"] for phase in phase_summaries)
            overall_success_rate = total_success / total_calls if total_calls > 0 else 0
            
            total_chunks = sum(r.get("chunks_sent", 0) for r in all_results if not isinstance(r, Exception))
            total_bytes = sum(r.get("bytes_sent", 0) for r in all_results if not isinstance(r, Exception))
            
            logger.info(f"Stability test completed: {total_success}/{total_calls} calls successful "
                       f"({overall_success_rate*100:.1f}%), sent {total_chunks} chunks, "
                       f"{total_bytes/(1024*1024):.2f}MB of data")
            
            summary = {
                "test_type": "stability",
                "test_duration_minutes": test_duration_minutes,
                "base_calls": base_calls,
                "peak_calls": peak_calls,
                "total_calls": total_calls,
                "total_success": total_success,
                "overall_success_rate": overall_success_rate,
                "total_test_duration": total_duration,
                "total_chunks_sent": total_chunks,
                "total_data_sent_mb": total_bytes / (1024 * 1024),
                "phase_summaries": phase_summaries,
                "memory_usage_mb": psutil.Process().memory_info().rss / (1024*1024)
            }
            
            return summary
    except Exception as e:
        logger.error(f"Error in stability test: {str(e)}")
        traceback.print_exc()
        return {
            "test_type": "stability",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


async def run_resource_monitoring_test(
    database_url: str,
    num_calls: int,
    duration: int,
    chunk_size: int,
    interval: int,
    monitor_interval_seconds: int = 1
) -> Dict[str, Any]:
    """
    Run a test that monitors system resources while under load to identify bottlenecks.
    
    Args:
        database_url: PostgreSQL connection URL for the test database
        num_calls: Number of concurrent calls to simulate
        duration: Duration of each call in seconds
        chunk_size: Size of each audio chunk in KB
        interval: Interval between chunks in milliseconds
        monitor_interval_seconds: How often to sample resource metrics in seconds
        
    Returns:
        Dictionary with test results and resource usage metrics
    """
    logger.info(f"Starting resource monitoring test with {num_calls} concurrent calls")
    
    # Initialize resource metrics storage
    metrics = {
        "timestamps": [],
        "cpu_percent": [],
        "memory_percent": [],
        "memory_mb": [],
        "network_io_sent_kb": [],
        "network_io_received_kb": [],
        "disk_io_read_kb": [],
        "disk_io_write_kb": [],
        "open_files": [],
        "thread_count": []
    }
    
    # Get initial network and disk IO counters
    initial_net_io = psutil.net_io_counters()
    initial_disk_io = psutil.disk_io_counters()
    
    # Resource monitoring task
    async def monitor_resources():
        nonlocal initial_net_io, initial_disk_io
        start_time = time.time()
        process = psutil.Process()
        last_net_io = initial_net_io
        last_disk_io = initial_disk_io
        
        while True:
            current_time = time.time() - start_time
            metrics["timestamps"].append(current_time)
            
            # CPU and memory usage
            metrics["cpu_percent"].append(process.cpu_percent(interval=0.1))
            memory_info = process.memory_info()
            metrics["memory_mb"].append(memory_info.rss / (1024 * 1024))
            metrics["memory_percent"].append(process.memory_percent())
            
            # Network IO
            net_io = psutil.net_io_counters()
            metrics["network_io_sent_kb"].append((net_io.bytes_sent - last_net_io.bytes_sent) / 1024)
            metrics["network_io_received_kb"].append((net_io.bytes_recv - last_net_io.bytes_recv) / 1024)
            last_net_io = net_io
            
            # Disk IO
            disk_io = psutil.disk_io_counters()
            metrics["disk_io_read_kb"].append((disk_io.read_bytes - last_disk_io.read_bytes) / 1024)
            metrics["disk_io_write_kb"].append((disk_io.write_bytes - last_disk_io.write_bytes) / 1024)
            last_disk_io = disk_io
            
            # Open files and threads
            metrics["open_files"].append(len(process.open_files()))
            metrics["thread_count"].append(process.num_threads())
            
            # Log current resource usage
            logger.debug(f"T+{current_time:.1f}s - CPU: {metrics['cpu_percent'][-1]:.1f}%, " +
                       f"Memory: {metrics['memory_mb'][-1]:.1f}MB, " +
                       f"Threads: {metrics['thread_count'][-1]}")
            
            await asyncio.sleep(monitor_interval_seconds)
    
    try:
        with AppServerTest(database_url=database_url) as server:
            logger.info(f"Server started at {server.base_url}")
            
            # Start resource monitoring
            monitoring_task = asyncio.create_task(monitor_resources())
            runner = StressTestRunner(server)
            start_time = time.time()
            
            # Run the load test
            results = await runner.run_concurrent_calls(
                num_calls=num_calls,
                duration_seconds=duration,
                chunk_size_kb=chunk_size,
                chunk_interval_ms=interval
            )
            
            # Stop resource monitoring
            monitoring_task.cancel()
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass
            
            # Calculate test statistics
            total_duration = time.time() - start_time
            success_count = sum(1 for r in results if r.get("completed", False))
            success_rate = success_count / num_calls if num_calls > 0 else 0
            
            # Calculate resource usage statistics
            resource_stats = {
                "peak_cpu_percent": max(metrics["cpu_percent"]) if metrics["cpu_percent"] else 0,
                "peak_memory_mb": max(metrics["memory_mb"]) if metrics["memory_mb"] else 0,
                "peak_thread_count": max(metrics["thread_count"]) if metrics["thread_count"] else 0,
                "peak_open_files": max(metrics["open_files"]) if metrics["open_files"] else 0,
                "total_network_sent_mb": sum(metrics["network_io_sent_kb"]) / 1024 if metrics["network_io_sent_kb"] else 0,
                "total_network_received_mb": sum(metrics["network_io_received_kb"]) / 1024 if metrics["network_io_received_kb"] else 0
            }
            
            # Determine likely bottlenecks
            bottlenecks = []
            if resource_stats["peak_cpu_percent"] > 80:
                bottlenecks.append("CPU usage exceeded 80%")
            if resource_stats["peak_memory_mb"] > 1024:  # 1GB
                bottlenecks.append("Memory usage exceeded 1GB")
            if resource_stats["peak_thread_count"] > 100:
                bottlenecks.append("Thread count exceeded 100")
            if resource_stats["peak_open_files"] > 500:
                bottlenecks.append("Open file count exceeded 500")
            
            logger.info(f"Resource monitoring test completed: {success_count}/{num_calls} calls successful "
                       f"({success_rate*100:.1f}%)")
            logger.info(f"Peak CPU: {resource_stats['peak_cpu_percent']:.1f}%, "
                       f"Peak Memory: {resource_stats['peak_memory_mb']:.1f}MB, "
                       f"Peak Threads: {resource_stats['peak_thread_count']}")
            if bottlenecks:
                logger.warning(f"Detected bottlenecks: {', '.join(bottlenecks)}")
            
            summary = {
                "test_type": "resource_monitoring",
                "num_calls": num_calls,
                "duration_seconds": duration,
                "success_count": success_count,
                "success_rate": success_rate,
                "total_test_duration": total_duration,
                "resource_metrics": metrics,
                "resource_stats": resource_stats,
                "bottlenecks": bottlenecks
            }
            
            return summary
    except Exception as e:
        logger.error(f"Error in resource monitoring test: {str(e)}")
        traceback.print_exc()
        return {
            "test_type": "resource_monitoring",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


async def main():
    """Parse command-line arguments and run the appropriate test."""
    parser = argparse.ArgumentParser(description="Run server-based stress tests for call flow")
    
    parser.add_argument(
        "--test-type",
        choices=["http_basic", "throughput", "resilience", "load", "high_concurrency", 
                "wave_pattern", "burst_pattern", "stability", "resource_monitoring"],
        default="throughput",
        help="Type of stress test to run"
    )
    
    parser.add_argument(
        "--database-url",
        default=DEFAULT_DB_URL,
        help="PostgreSQL connection URL for the test database"
    )
    
    parser.add_argument(
        "--num-calls",
        type=int,
        default=3,
        help="Number of concurrent calls to simulate"
    )
    
    parser.add_argument(
        "--duration",
        type=int,
        default=5,
        help="Duration of each call in seconds"
    )
    
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=2,
        help="Size of each audio chunk in KB"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=200,
        help="Interval between chunks in milliseconds"
    )
    
    parser.add_argument(
        "--error-rate",
        type=float,
        default=0.2,
        help="Probability of simulated errors (0.0-1.0)"
    )
    
    parser.add_argument(
        "--max-batch",
        type=int,
        default=10,
        help="Maximum batch size for load tests"
    )
    
    parser.add_argument(
        "--increment",
        type=int,
        default=2,
        help="Batch size increment for load tests"
    )
    
    parser.add_argument(
        "--output",
        help="File to save test results (JSON format)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--peak-calls",
        type=int,
        default=10,
        help="Peak number of calls for wave pattern test"
    )
    
    parser.add_argument(
        "--num-waves",
        type=int,
        default=3,
        help="Number of waves for wave pattern test"
    )
    
    parser.add_argument(
        "--wave-duration",
        type=int,
        default=10,
        help="Duration of each wave in seconds"
    )
    
    parser.add_argument(
        "--burst-size",
        type=int,
        default=10,
        help="Number of calls in each burst"
    )
    
    parser.add_argument(
        "--num-bursts",
        type=int,
        default=3,
        help="Number of bursts to simulate"
    )
    
    parser.add_argument(
        "--ramp-up-ms",
        type=int,
        default=500,
        help="How quickly to ramp up the burst (in milliseconds)"
    )
    
    parser.add_argument(
        "--rest-seconds",
        type=int,
        default=5,
        help="Seconds to rest between bursts"
    )
    
    parser.add_argument(
        "--test-duration-minutes",
        type=int,
        default=5,
        help="Total test duration in minutes for stability test"
    )
    
    parser.add_argument(
        "--base-calls",
        type=int,
        default=3,
        help="Baseline number of concurrent calls for stability test"
    )
    
    parser.add_argument(
        "--monitor-interval",
        type=int,
        default=1,
        help="Interval in seconds for resource monitoring test"
    )

    args = parser.parse_args()
    
    # Configure logging level based on debug flag
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        framework_logger.setLevel(logging.DEBUG)
    
    logger.info(f"Starting server-based stress tests: {args.test_type}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current directory: {os.getcwd()}")
    logger.info(f"Database URL: {args.database_url}")
    logger.info(f"Running on platform: {platform.system()}")
    
    # For Windows, suggest using http_basic test if another test type is selected
    if platform.system() == "Windows" and args.test_type != "http_basic":
        logger.warning("Running on Windows. If you encounter WebSocket issues, try the 'http_basic' test type.")
    
    try:
        # Run the appropriate test type
        if args.test_type == "http_basic":
            results = await run_http_basic_test(
                database_url=args.database_url
            )
        elif args.test_type == "throughput":
            results = await run_throughput_test(
                database_url=args.database_url,
                num_calls=args.num_calls,
                duration=args.duration,
                chunk_size=args.chunk_size,
                interval=args.interval
            )
        elif args.test_type == "resilience":
            results = await run_resilience_test(
                database_url=args.database_url,
                num_calls=args.num_calls,
                duration=args.duration,
                error_rate=args.error_rate
            )
        elif args.test_type == "load":
            results = await run_load_test(
                database_url=args.database_url,
                max_batch_size=args.max_batch,
                increment=args.increment,
                duration=args.duration
            )
        elif args.test_type == "high_concurrency":
            results = await run_high_concurrency_test(
                database_url=args.database_url,
                num_calls=args.num_calls,
                duration=args.duration,
                chunk_size=args.chunk_size,
                interval=args.interval
            )
        elif args.test_type == "wave_pattern":
            results = await run_wave_pattern_test(
                database_url=args.database_url,
                peak_calls=args.peak_calls,
                num_waves=args.num_waves,
                wave_duration=args.wave_duration,
                chunk_size=args.chunk_size,
                interval=args.interval
            )
        elif args.test_type == "burst_pattern":
            results = await run_burst_pattern_test(
                database_url=args.database_url,
                burst_size=args.burst_size,
                num_bursts=args.num_bursts,
                ramp_up_ms=args.ramp_up_ms,
                rest_seconds=args.rest_seconds,
                call_duration=args.duration,
                chunk_size=args.chunk_size,
                interval=args.interval
            )
        elif args.test_type == "stability":
            results = await run_stability_test(
                database_url=args.database_url,
                test_duration_minutes=args.test_duration_minutes,
                base_calls=args.base_calls,
                peak_calls=args.peak_calls,
                chunk_size=args.chunk_size,
                interval=args.interval
            )
        elif args.test_type == "resource_monitoring":
            results = await run_resource_monitoring_test(
                database_url=args.database_url,
                num_calls=args.num_calls,
                duration=args.duration,
                chunk_size=args.chunk_size,
                interval=args.interval,
                monitor_interval_seconds=args.monitor_interval
            )
        else:
            logger.error(f"Unknown test type: {args.test_type}")
            return 1
        
        # Save results to file if requested
        if args.output:
            try:
                with open(args.output, "w") as f:
                    json.dump(results, f, indent=2)
                logger.info(f"Results saved to {args.output}")
            except Exception as e:
                logger.error(f"Failed to save results: {str(e)}")
        
        # Print summary to console
        print("\nTest Summary:")
        print(f"Test type: {results['test_type']}")
        
        if "error" in results:
            print(f"Test failed with error: {results['error']}")
            return 1
        
        if results["test_type"] == "http_basic":
            print(f"Total requests: {results['total_requests']}")
            print(f"Success rate: {results['success_rate']*100:.1f}%")
            print(f"Docs accessible: {results['docs_accessible']}")
            print(f"Total test duration: {results['total_test_duration']:.2f} seconds")
        elif results["test_type"] == "throughput":
            print(f"Concurrent calls: {results['num_calls']}")
            print(f"Success rate: {results['success_rate']*100:.1f}%")
            print(f"Total data sent: {results['total_data_sent_mb']:.2f} MB")
            print(f"Total test duration: {results['total_test_duration']:.2f} seconds")
        elif results["test_type"] == "resilience":
            print(f"Concurrent calls: {results['num_calls']}")
            print(f"Error rate: {results['error_rate']*100:.1f}%")
            print(f"Success rate: {results['success_rate']*100:.1f}%")
            print(f"Total simulated errors: {results['total_simulated_errors']}")
        elif results["test_type"] == "load":
            print(f"Total calls: {results['total_calls']}")
            print(f"Overall success rate: {results['overall_success_rate']*100:.1f}%")
            if "max_acceptable_batch" in results:
                print(f"Maximum acceptable batch size: {results['max_acceptable_batch']}")
            print("\nBatch results:")
            for batch in results["batches"]:
                print(f"  Batch size {batch['batch_size']}: {batch['success_rate']*100:.1f}% success rate")
        elif results["test_type"] == "high_concurrency":
            print(f"Concurrent calls: {results['num_calls']}")
            print(f"Success rate: {results['success_rate']*100:.1f}%")
            print(f"Total data sent: {results['total_data_sent_mb']:.2f} MB")
            print(f"Total test duration: {results['total_test_duration']:.2f} seconds")
        elif results["test_type"] == "wave_pattern":
            print(f"Peak calls: {results['peak_calls']}")
            print(f"Number of waves: {results['num_waves']}")
            print(f"Total calls: {results['total_calls']}")
            print(f"Overall success rate: {results['overall_success_rate']*100:.1f}%")
            print("\nWave results:")
            for wave in results["wave_summaries"]:
                print(f"  Wave {wave['wave']}: {wave['num_calls']} calls, "
                      f"{wave['success_rate']*100:.1f}% success rate")
            print(f"Total test duration: {results['total_test_duration']:.2f} seconds")
        elif results["test_type"] == "burst_pattern":
            print(f"Burst size: {results['burst_size']}")
            print(f"Number of bursts: {results['num_bursts']}")
            print(f"Total calls: {results['total_calls']}")
            print(f"Overall success rate: {results['overall_success_rate']*100:.1f}%")
            print("\nBurst results:")
            for burst in results["burst_summaries"]:
                print(f"  Burst {burst['burst']}: {burst['num_calls']} calls, "
                      f"{burst['success_rate']*100:.1f}% success rate, {burst['duration']:.2f}s")
            print(f"Total test duration: {results['total_test_duration']:.2f} seconds")
        elif results["test_type"] == "stability":
            print(f"Test duration: {results['test_duration_minutes']} minutes")
            print(f"Base/Peak calls: {results['base_calls']}/{results['peak_calls']} calls")
            print(f"Total calls: {results['total_calls']}")
            print(f"Overall success rate: {results['overall_success_rate']*100:.1f}%")
            print(f"Memory usage at end: {results['memory_usage_mb']:.1f} MB")
            print("\nPhase results:")
            for phase in results["phase_summaries"]:
                print(f"  Phase {phase['phase']} ({phase['type']}): {phase['num_calls']} calls, "
                      f"{phase['success_rate']*100:.1f}% success rate")
            print(f"Total test duration: {results['total_test_duration']:.2f} seconds")
        elif results["test_type"] == "resource_monitoring":
            print(f"Total calls: {results['num_calls']}")
            print(f"Success rate: {results['success_rate']*100:.1f}%")
            print(f"\nResource usage:")
            print(f"  Peak CPU: {results['resource_stats']['peak_cpu_percent']:.1f}%")
            print(f"  Peak Memory: {results['resource_stats']['peak_memory_mb']:.1f} MB")
            print(f"  Peak Thread Count: {results['resource_stats']['peak_thread_count']}")
            print(f"  Peak Open Files: {results['resource_stats']['peak_open_files']}")
            print(f"  Total Network I/O: {results['resource_stats']['total_network_sent_mb']:.2f} MB sent, "
                  f"{results['resource_stats']['total_network_received_mb']:.2f} MB received")
            
            if results.get('bottlenecks'):
                print(f"\nDetected bottlenecks:")
                for bottleneck in results['bottlenecks']:
                    print(f"  - {bottleneck}")
            else:
                print("\nNo resource bottlenecks detected")
                
            print(f"\nTotal test duration: {results['total_test_duration']:.2f} seconds")
        
        return 0 if results.get("success_rate", 0) > 0.5 else 1
        
    except Exception as e:
        logger.error(f"Unhandled exception in main: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Set up asyncio for Windows if needed
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        result = asyncio.run(main())
        sys.exit(result)
    except KeyboardInterrupt:
        logger.warning("Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        traceback.print_exc()
        sys.exit(1) 