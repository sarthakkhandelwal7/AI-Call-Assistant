"""
Server-based stress testing framework for FastAPI applications.

This framework addresses the limitations of TestClient by:
1. Running a real server instance using uvicorn
2. Using proper connection pooling for database operations
3. Supporting truly concurrent operations via httpx and websockets

Usage:
    with AppServerTest() as server:
        # Run your concurrent tests against server.base_url
"""

import asyncio
import os
import signal
import socket
import subprocess
import time
from typing import Optional, List, Dict, Any, Callable, Awaitable
import uuid
import json
import logging
import sys
import httpx
import websockets
from websockets.client import WebSocketClientProtocol
from contextlib import asynccontextmanager, contextmanager
import nest_asyncio
import random
import base64
import traceback

# Apply nest_asyncio to allow nested event loops (needed for some test runners)
nest_asyncio.apply()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("stress_test")

# Test constants
TEST_DB_TWILIO_NUMBER = "+15550000001"
TEST_DB_USER_ID = "a2d7200a-e061-460a-b5a2-afc47344caa9"
MOCK_CALLER_NUMBER = "+15551112222"

# Add the project root to the Python path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Default test database configuration
DEFAULT_DB_URL = "postgresql+asyncpg://postgres:postgres@db:5432/ai_secretary_test"
DEFAULT_TEST_USER_ID = "a2d7200a-e061-460a-b5a2-afc47344caa9"
DEFAULT_TEST_PHONE = "+15550000001"


def find_free_port() -> int:
    """Find and return a free port number."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        return s.getsockname()[1]


class AppServerTest:
    """
    Test server management class that starts and stops a real uvicorn server.
    
    This allows testing with real HTTP/WebSocket connections, which is important
    for stress testing and concurrency tests where FastAPI's TestClient is insufficient.
    """
    
    def __init__(
        self,
        database_url: str = DEFAULT_DB_URL,
        host: str = "127.0.0.1",
        port: Optional[int] = None,
        debug: bool = False,
        server_ready_timeout: int = 30
    ):
        self.host = host
        self.port = port or find_free_port()
        self.base_url = f"http://{self.host}:{self.port}"
        self.websocket_url = f"ws://{self.host}:{self.port}/audio-stream"
        self.debug = debug
        self.database_url = database_url
        self.server_ready_timeout = server_ready_timeout
        self.server_process = None
        self.server_output_file = None
        self.server_error_file = None
    
    def __enter__(self):
        self._start_server()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stop_server()
    
    def _start_server(self):
        """Start the uvicorn server as a subprocess."""
        logger.info(f"Starting test server on port {self.port}")
        
        # Create unique filenames for server logs
        timestamp = int(time.time())
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        server_output_path = os.path.join(log_dir, f"server_output_{self.port}_{timestamp}.log")
        server_error_path = os.path.join(log_dir, f"server_error_{self.port}_{timestamp}.log")
        
        try:
            self.server_output_file = open(server_output_path, 'w')
            self.server_error_file = open(server_error_path, 'w')
            
            logger.info(f"Server stdout will be saved to: {server_output_path}")
            logger.info(f"Server stderr will be saved to: {server_error_path}")
        except Exception as e:
            logger.error(f"Failed to open log files: {str(e)}")
            if self.server_output_file:
                self.server_output_file.close()
            if self.server_error_file:
                self.server_error_file.close()
            raise RuntimeError(f"Failed to open server log files: {str(e)}") from e
        
        # Set environment variables for the server
        env = os.environ.copy()
        env.update({
            'DATABASE_URL': self.database_url,
            'PYTHONPATH': project_root,
            'TESTING': 'true',
            'DEBUG': str(self.debug).lower(),
            'LOG_LEVEL': 'debug' if self.debug else 'info',
            # Add other necessary environment variables
            'STREAM_URL': self.websocket_url,
            'OPENAI_API_KEY': 'sk-dummy-key-for-testing',
            'TWILIO_ACCOUNT_SID': 'dummy_twilio_sid',
            'TWILIO_AUTH_TOKEN': 'dummy_twilio_token',
            'FRONTEND_URL': 'http://dummy.com',
            'GOOGLE_CLIENT_ID': 'dummy_google_id',
            'GOOGLE_CLIENT_SECRET': 'dummy_google_secret',
            'JWT_SECRET_KEY': 'dummy_jwt_secret',
        })
        
        # Check if we can import the app module before starting the server
        try:
            import importlib
            app_module = importlib.import_module('app.main')
            logger.info("Successfully imported app.main")
        except ImportError as e:
            logger.error(f"Failed to import app.main: {str(e)}")
            logger.error(f"Python path: {sys.path}")
            logger.error(f"Current directory: {os.getcwd()}")
            if self.server_output_file:
                self.server_output_file.close()
            if self.server_error_file:
                self.server_error_file.close()
            raise RuntimeError(f"Cannot start server: {str(e)}") from e
        
        # Command to start uvicorn
        cmd = [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", self.host,
            "--port", str(self.port),
            "--log-level", "debug" if self.debug else "info"
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Start the server process - platform-specific handling
        creation_flags = 0
        if sys.platform == "win32":
            # On Windows, we need to create a new process group to make sure
            # the server process can be terminated independently of the parent
            from subprocess import CREATE_NEW_PROCESS_GROUP
            creation_flags = CREATE_NEW_PROCESS_GROUP
        
        try:
            # Start the process differently depending on platform
            if sys.platform == "win32":
                self.server_process = subprocess.Popen(
                    cmd,
                    env=env,
                    stdout=self.server_output_file,
                    stderr=self.server_error_file,
                    creationflags=creation_flags,
                    bufsize=1,
                    text=True
                )
            else:
                self.server_process = subprocess.Popen(
                    cmd,
                    env=env,
                    stdout=self.server_output_file,
                    stderr=self.server_error_file,
                    preexec_fn=os.setsid,  # Creates a new process group on Unix
                    bufsize=1,
                    universal_newlines=True
                )
        except Exception as e:
            logger.error(f"Failed to start server process: {str(e)}")
            if self.server_output_file:
                self.server_output_file.close()
            if self.server_error_file:
                self.server_error_file.close()
            raise RuntimeError(f"Failed to start server: {str(e)}") from e
        
        # Wait for the server to be ready
        logger.info("Waiting for server to be ready...")
        start_time = time.time()
        ready = False
        
        while time.time() - start_time < self.server_ready_timeout:
            try:
                # Try to connect to the server
                with httpx.Client(timeout=1) as client:
                    response = client.get(f"{self.base_url}/healthcheck")
                    if response.status_code == 200:
                        logger.info(f"Server ready at {self.base_url}")
                        
                        # Call the test setup endpoint to ensure test users exist
                        try:
                            setup_response = client.get(f"{self.base_url}/test/setup")
                            if setup_response.status_code in (200, 201):
                                logger.info(f"Test setup completed: {setup_response.json()}")
                            else:
                                logger.warning(f"Test setup failed: {setup_response.status_code} - {setup_response.text}")
                        except Exception as e:
                            logger.warning(f"Error during test setup: {str(e)}")
                        
                        ready = True
                        break
            except Exception as e:
                # Retry after a short delay
                logger.debug(f"Server not ready yet: {str(e)}")
                
                # Check if the process is still running
                if self.server_process.poll() is not None:
                    logger.error(f"Server process exited with code {self.server_process.returncode}")
                    # Dump server output and error
                    self._dump_server_logs()
                    raise RuntimeError("Server process terminated unexpectedly")
                
                time.sleep(0.5)
        
        if not ready:
            self._stop_server()
            logger.error(f"Server failed to start within {self.server_ready_timeout} seconds")
            self._dump_server_logs()
            raise RuntimeError(f"Server failed to start within {self.server_ready_timeout} seconds")
        
        logger.info(f"Server started successfully at {self.base_url}")
    
    def _dump_server_logs(self):
        """Dump server logs to help diagnose issues."""
        if self.server_output_file:
            self.server_output_file.flush()
            try:
                with open(self.server_output_file.name, 'r') as f:
                    logger.error("Server stdout:")
                    for line in f.readlines():
                        logger.error(f"  {line.strip()}")
            except Exception as e:
                logger.error(f"Failed to read server stdout: {str(e)}")
            self.server_output_file.close()
            self.server_output_file = None
        
        if self.server_error_file:
            self.server_error_file.flush()
            try:
                with open(self.server_error_file.name, 'r') as f:
                    logger.error("Server stderr:")
                    for line in f.readlines():
                        logger.error(f"  {line.strip()}")
            except Exception as e:
                logger.error(f"Failed to read server stderr: {str(e)}")
            self.server_error_file.close()
            self.server_error_file = None
    
    def _stop_server(self):
        """Stop the uvicorn server."""
        if self.server_process:
            logger.info("Stopping server...")
            
            # Close file handles first
            if self.server_output_file:
                self.server_output_file.close()
                self.server_output_file = None
            
            if self.server_error_file:
                self.server_error_file.close()
                self.server_error_file = None
            
            # Different termination approach based on platform
            try:
                if sys.platform == "win32":
                    # On Windows, terminate() should work with CREATE_NEW_PROCESS_GROUP
                    self.server_process.terminate()
                else:
                    # On Unix, we need to kill the entire process group
                    import signal
                    os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
                
                # Wait for process to terminate
                try:
                    self.server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("Server didn't terminate gracefully, killing it forcefully")
                    
                    if sys.platform == "win32":
                        # On Windows, we need to forcefully kill the process
                        subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.server_process.pid)])
                    else:
                        # On Unix, we kill the entire process group with SIGKILL
                        os.killpg(os.getpgid(self.server_process.pid), signal.SIGKILL)
                        self.server_process.wait(timeout=1)
            except Exception as e:
                logger.error(f"Error stopping server: {str(e)}")
                # Try to kill directly as a last resort
                try:
                    self.server_process.kill()
                except Exception:
                    pass
            
            logger.info("Server stopped")
            self.server_process = None


class CallSimulator:
    """
    Simulates Twilio calls with audio streaming for stress testing.
    Uses direct HTTP and WebSocket connections to the server.
    """
    
    def __init__(self, server: AppServerTest):
        self.server = server
        self.base_url = server.base_url
        self.ws_url = server.websocket_url  # This already includes /audio-stream
    
    async def simulate_call(
        self,
        call_id: str,
        from_number: str = MOCK_CALLER_NUMBER,
        to_number: str = TEST_DB_TWILIO_NUMBER,
        user_id: str = TEST_DB_USER_ID,
        duration_seconds: int = 5,
        chunk_size_kb: int = 2,
        chunk_interval_ms: int = 200,
        error_rate: float = 0.0,
        error_handler: Optional[Callable[[Exception], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """
        Simulate a complete call including audio streaming.
        
        Args:
            call_id: Unique identifier for this call
            from_number: Caller phone number
            to_number: Called phone number
            user_id: User ID for the call
            duration_seconds: Call duration in seconds
            chunk_size_kb: Size of each audio chunk in KB
            chunk_interval_ms: Time between chunks in ms
            error_rate: Probability of simulating an error (0.0-1.0)
            error_handler: Optional callback for handling errors
            
        Returns:
            Dict with call statistics
        """
        stats = {
            "call_id": call_id,
            "start_time": time.time(),
            "chunks_sent": 0,
            "bytes_sent": 0,
            "errors": 0,
            "completed": False
        }
        
        try:
            # Step 1: Initiate call via HTTP
            logger.info(f"Call {call_id}: Initiating call from {from_number} to {to_number}")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/calls/inbound",
                    data={"From": from_number, "To": to_number},
                    timeout=10.0
                )
                response.raise_for_status()
                
                # Extract TwiML response (optional validation)
                twiml = response.text
                logger.debug(f"Call {call_id}: Received TwiML: {twiml}")
            
            # Step 2: Connect to WebSocket
            logger.info(f"Call {call_id}: Connecting to WebSocket at {self.ws_url}")
            async with websockets.connect(self.ws_url) as ws:
                # Step 3: Send start event
                stream_sid = f"MZ{uuid.uuid4().hex}"
                call_sid = f"CA{uuid.uuid4().hex}"
                
                await self._send_start_event(ws, call_sid, stream_sid, user_id)
                
                # Step 4: Send audio chunks
                num_chunks = int((duration_seconds * 1000) / chunk_interval_ms)
                
                logger.info(f"Call {call_id}: Sending {num_chunks} audio chunks")
                for i in range(1, num_chunks + 1):
                    # Simulate random errors if specified
                    if error_rate > 0 and random.random() < error_rate:
                        stats["errors"] += 1
                        error = Exception(f"Simulated error on chunk {i}")
                        if error_handler:
                            await error_handler(error)
                        logger.warning(f"Call {call_id}: Simulated error on chunk {i}")
                        continue
                    
                    # Send audio chunk
                    chunk_payload = self._generate_audio_payload(chunk_size_kb)
                    await self._send_media_event(
                        ws, i, chunk_payload, str(i * chunk_interval_ms)
                    )
                    
                    stats["chunks_sent"] += 1
                    stats["bytes_sent"] += len(chunk_payload)
                    
                    # Wait before sending next chunk
                    await asyncio.sleep(chunk_interval_ms / 1000)
                
                # Step 5: Send stop event
                await self._send_stop_event(ws, call_sid)
                
                stats["completed"] = True
                stats["duration"] = time.time() - stats["start_time"]
                logger.info(f"Call {call_id}: Completed successfully in {stats['duration']:.2f}s")
                
        except Exception as e:
            logger.error(f"Call {call_id}: Error during call simulation: {str(e)}")
            stats["error"] = str(e)
            stats["duration"] = time.time() - stats["start_time"]
            if error_handler:
                await error_handler(e)
        
        return stats
    
    @staticmethod
    async def _send_start_event(
        ws: WebSocketClientProtocol, 
        call_sid: str, 
        stream_sid: str, 
        user_id: str
    ):
        """Send the start event to the WebSocket."""
        start_event = {
            "event": "start",
            "sequenceNumber": "1",
            "start": {
                "accountSid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "streamSid": stream_sid,
                "callSid": call_sid,
                "tracks": ["inbound"],
                "mediaFormat": {
                    "encoding": "mulaw", 
                    "sampleRate": 8000, 
                    "channels": 1
                },
                "customParameters": {
                    "user_id": user_id
                }
            }
        }
        
        await ws.send(json.dumps(start_event))
    
    @staticmethod
    async def _send_media_event(
        ws: WebSocketClientProtocol, 
        sequence_number: int,
        payload: str,
        timestamp: str
    ):
        """Send a media event with audio payload to the WebSocket."""
        media_event = {
            "event": "media",
            "sequenceNumber": str(sequence_number + 1),  # +1 because start is 1
            "media": {
                "track": "inbound",
                "chunk": str(sequence_number),
                "timestamp": timestamp,
                "payload": payload,
            }
        }
        
        await ws.send(json.dumps(media_event))
    
    @staticmethod
    async def _send_stop_event(ws: WebSocketClientProtocol, call_sid: str):
        """Send the stop event to the WebSocket."""
        stop_event = {
            "event": "stop",
            "sequenceNumber": "999999",  # High number to ensure it's after all media events
            "stop": {
                "accountSid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "callSid": call_sid
            }
        }
        
        await ws.send(json.dumps(stop_event))
    
    @staticmethod
    def _generate_audio_payload(size_kb: int) -> str:
        """Generate a dummy audio payload of specified size in KB."""
        # Create a string of 'A's that's approximately size_kb kilobytes
        return "A" * (size_kb * 1024)


class StressTestRunner:
    """
    Runs stress tests with configurable parameters.
    """
    
    def __init__(self, server: AppServerTest):
        self.server = server
        self.simulator = CallSimulator(server)
    
    async def run_concurrent_calls(
        self,
        num_calls: int = 10,
        duration_seconds: int = 5,
        chunk_size_kb: int = 2,
        chunk_interval_ms: int = 200,
        error_rate: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Run multiple concurrent calls and return their statistics.
        
        Args:
            num_calls: Number of concurrent calls to simulate
            duration_seconds: Duration of each call in seconds
            chunk_size_kb: Size of each audio chunk in KB
            chunk_interval_ms: Interval between chunks in ms
            error_rate: Probability of simulating errors (0.0-1.0)
            
        Returns:
            List of call statistics dictionaries
        """
        logger.info(f"Starting concurrent call test with {num_calls} calls")
        
        # Create tasks for each call
        tasks = []
        for i in range(num_calls):
            call_id = f"call-{i+1}"
            from_number = f"+155511{i:05d}"
            
            tasks.append(
                self.simulator.simulate_call(
                    call_id=call_id,
                    from_number=from_number,
                    duration_seconds=duration_seconds,
                    chunk_size_kb=chunk_size_kb,
                    chunk_interval_ms=chunk_interval_ms,
                    error_rate=error_rate,
                    error_handler=self._error_handler
                )
            )
        
        # Run all calls concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_duration = time.time() - start_time
        
        # Process results
        stats = []
        success_count = 0
        total_chunks = 0
        total_bytes = 0
        
        for result in results:
            if isinstance(result, Exception):
                stats.append({"error": str(result), "completed": False})
            else:
                stats.append(result)
                if result.get("completed", False):
                    success_count += 1
                    total_chunks += result.get("chunks_sent", 0)
                    total_bytes += result.get("bytes_sent", 0)
        
        # Log summary
        logger.info(f"Stress test completed in {total_duration:.2f}s")
        logger.info(f"Success rate: {success_count}/{num_calls} calls ({success_count/num_calls*100:.1f}%)")
        logger.info(f"Total chunks sent: {total_chunks}")
        logger.info(f"Total data sent: {total_bytes/1024/1024:.2f} MB")
        
        return stats
    
    async def run_sequential_load_test(
        self,
        num_calls: int = 5,
        ramp_up_seconds: int = 2,
        **call_params
    ) -> List[Dict[str, Any]]:
        """
        Run a sequential load test, starting calls one after another.
        
        Args:
            num_calls: Total number of calls to make
            ramp_up_seconds: Time to spread out call starts
            **call_params: Parameters passed to simulate_call
            
        Returns:
            List of call statistics dictionaries
        """
        logger.info(f"Starting sequential load test with {num_calls} calls over {ramp_up_seconds}s")
        
        results = []
        tasks = []
        
        # Start calls with a delay between them
        delay_between_calls = ramp_up_seconds / num_calls if num_calls > 1 else 0
        
        for i in range(num_calls):
            call_id = f"seq-call-{i+1}"
            from_number = f"+155522{i:05d}"
            
            # Create task but don't await immediately
            task = asyncio.create_task(
                self.simulator.simulate_call(
                    call_id=call_id,
                    from_number=from_number,
                    **call_params
                )
            )
            tasks.append(task)
            
            # Wait before starting next call
            if i < num_calls - 1:  # No need to wait after the last call
                await asyncio.sleep(delay_between_calls)
        
        # Wait for all calls to complete
        for task in tasks:
            result = await task
            results.append(result)
        
        return results
    
    async def _error_handler(self, error: Exception):
        """Handle errors during call simulation."""
        logger.warning(f"Error in call simulation: {str(error)}")
        # Could implement more sophisticated error handling here
        await asyncio.sleep(0.1)


# Helper function to run a test function with the server
async def run_server_test(
    test_func: Callable[[AppServerTest], Awaitable[Any]],
    **server_kwargs
) -> Any:
    """
    Run a test function with a server context.
    
    Args:
        test_func: Async function that takes an AppServerTest and returns result
        **server_kwargs: Arguments to pass to AppServerTest constructor
        
    Returns:
        The result of the test function
    """
    with AppServerTest(**server_kwargs) as server:
        return await test_func(server)


# Example usage as a standalone script
if __name__ == "__main__":
    async def sample_test(server):
        runner = StressTestRunner(server)
        return await runner.run_concurrent_calls(
            num_calls=3,
            duration_seconds=3,
            chunk_size_kb=2
        )
    
    result = asyncio.run(run_server_test(sample_test)) 