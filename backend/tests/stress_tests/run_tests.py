#!/usr/bin/env python
"""
Stress Test Runner Script

This script provides a convenient way to run the server-based stress tests.
It uses Python's subprocess to run the run_server_tests.py script with appropriate parameters.
"""

import os
import sys
import argparse
import subprocess
import time
import platform

def main():
    """Run server-based stress tests with command line arguments."""
    parser = argparse.ArgumentParser(description="Run call flow server-based stress tests")
    
    parser.add_argument(
        "--test-type", 
        choices=["all", "http_basic", "throughput", "resilience", "load", "high_concurrency", "wave_pattern", "burst_pattern", "stability", "resource_monitoring"],
        default=None,  # We'll set a default based on platform
        help="Type of stress test to run"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--num-calls", "-n",
        type=int,
        default=3,
        help="Number of concurrent calls to simulate"
    )
    
    parser.add_argument(
        "--duration", "-d",
        type=int,
        default=5,
        help="Duration of each call in seconds"
    )
    
    parser.add_argument(
        "--chunk-size", "-c",
        type=int,
        default=2,
        help="Size of each audio chunk in KB"
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
        "--output", "-o",
        help="File to save test results (JSON format)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout in seconds for the subprocess"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output"
    )
    
    parser.add_argument(
        "--monitor-interval",
        type=int,
        default=1,
        help="Interval in seconds for resource monitoring test"
    )
    
    args = parser.parse_args()
    
    # Determine test type based on platform if not specified
    if args.test_type is None:
        if platform.system() == "Windows":
            args.test_type = "http_basic"
            print("Running on Windows: Using 'http_basic' test type by default.")
            print("This tests basic HTTP endpoints without WebSockets.")
            print("For full WebSocket tests, specify --test-type explicitly.")
        else:
            args.test_type = "throughput"
            print(f"Running on {platform.system()}: Using 'throughput' test type by default.")
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_script_path = os.path.join(script_dir, "run_server_tests.py")
    
    # Build command arguments - don't pass timeout to the subprocess
    cmd = [sys.executable, server_script_path]
    
    if args.test_type != "all":
        cmd.extend(["--test-type", args.test_type])
    
    cmd.extend(["--num-calls", str(args.num_calls)])
    cmd.extend(["--duration", str(args.duration)])
    cmd.extend(["--chunk-size", str(args.chunk_size)])
    
    if args.max_batch:
        cmd.extend(["--max-batch", str(args.max_batch)])
    
    if args.increment:
        cmd.extend(["--increment", str(args.increment)])
    
    if args.output:
        cmd.extend(["--output", args.output])
    
    if args.debug:
        cmd.append("--debug")
        
    if args.monitor_interval and args.test_type == "resource_monitoring":
        cmd.extend(["--monitor-interval", str(args.monitor_interval)])
    
    # Create environment for the subprocess
    env = os.environ.copy()
    
    # Add project root to Python path to ensure imports work
    project_root = os.path.abspath(os.path.join(script_dir, "../.."))
    print(f"Adding project root to Python path: {project_root}")
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{project_root}{os.pathsep}{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = project_root
    
    print(f"Running server-based stress tests: {args.test_type}")
    print(f"Command: {' '.join(cmd)}")
    
    # Record start time
    start_time = time.time()
    
    try:
        # Run the server tests as a subprocess with timeout - use timeout here but don't pass to cmd
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE if not args.verbose else None,
            stderr=subprocess.PIPE if not args.verbose else None,
            text=True,
            bufsize=1  # Line buffered
        )
        
        # If in verbose mode, let output go directly to console
        # Otherwise, capture output and print at the end
        stdout_data = []
        stderr_data = []
        
        if not args.verbose and process.stdout and process.stderr:
            # Platform-specific handling for reading output
            is_windows = platform.system() == "Windows"
            
            # Read output while process is running, with timeout
            timeout_time = start_time + args.timeout
            
            # Windows implementation (using simple readline)
            if is_windows:
                while process.poll() is None and time.time() < timeout_time:
                    # Windows select only works with sockets, not pipes
                    # Use a simple readline with a small timeout
                    if process.stdout:
                        line = process.stdout.readline()
                        if line:
                            stdout_data.append(line)
                            print(line, end='') if args.verbose else None
                    
                    if process.stderr:
                        line = process.stderr.readline()
                        if line:
                            stderr_data.append(line)
                            print(line, end='', file=sys.stderr) if args.verbose else None
                    
                    # Sleep to avoid high CPU usage
                    time.sleep(0.1)
            
            # Unix implementation (using select.poll)
            else:
                import select
                
                # Set up polling to read output without blocking
                poll_obj = select.poll()
                poll_obj.register(process.stdout, select.POLLIN)
                poll_obj.register(process.stderr, select.POLLIN)
                
                while process.poll() is None and time.time() < timeout_time:
                    for fd, event in poll_obj.poll(0.1):
                        if fd == process.stdout.fileno() and event & select.POLLIN:
                            line = process.stdout.readline()
                            if line:
                                stdout_data.append(line)
                                print(line, end='') if args.verbose else None
                        if fd == process.stderr.fileno() and event & select.POLLIN:
                            line = process.stderr.readline()
                            if line:
                                stderr_data.append(line)
                                print(line, end='', file=sys.stderr) if args.verbose else None
                    
                    # Sleep to avoid high CPU usage
                    time.sleep(0.1)
            
            # Check if we timed out
            if process.poll() is None:
                print(f"\nTest execution timed out after {args.timeout} seconds")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                return 1
            
            # Read any remaining output after process exits
            if process.stdout:
                for line in process.stdout:
                    stdout_data.append(line)
            
            if process.stderr:
                for line in process.stderr:
                    stderr_data.append(line)
        
        # Wait for process to finish
        return_code = process.wait()
        
        # Report test duration
        duration = time.time() - start_time
        print(f"\nTests completed in {duration:.2f} seconds")
        
        # Print captured output if not verbose mode
        if not args.verbose and stdout_data:
            print("\nStandard output:")
            for line in stdout_data:
                print(line, end='')
        
        if not args.verbose and stderr_data:
            print("\nStandard error:")
            for line in stderr_data:
                print(line, end='')
        
        # Platform-specific advice
        if return_code != 0 and platform.system() == "Windows" and args.test_type != "http_basic":
            print("\nNote: WebSocket tests may be unreliable on Windows.")
            print("Try running with --test-type http_basic for a simpler HTTP-only test.")
        
        return return_code
    except subprocess.CalledProcessError as e:
        print(f"\nError running tests: return code {e.returncode}")
        if not args.verbose and e.stdout:
            print("\nStandard output:")
            print(e.stdout)
        if not args.verbose and e.stderr:
            print("\nStandard error:")
            print(e.stderr)
        return e.returncode
    except Exception as e:
        print(f"\nError running tests: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 