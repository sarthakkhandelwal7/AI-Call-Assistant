"""
Shared fixtures for stress testing the call flow.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
import json
import os
import sys
import time
import random
import asyncio

# Import directly from parent conftest using absolute imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from conftest import mock_calendar_data

# Test database config for server tests
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_secretary_test"
TEST_USER_ID = "a2d7200a-e061-460a-b5a2-afc47344caa9"
TEST_TWILIO_NUMBER = "+15550000001"

@pytest.fixture()
def mock_openai_ws():
    """
    Mock WebSocket connection to OpenAI.
    This is now used only for pytest.mark.parametrize in existing tests.
    """
    mock = AsyncMock()
    
    # Add required methods for WebSocket simulations
    mock.send = AsyncMock()
    mock.recv = AsyncMock(return_value=json.dumps({
        "type": "message_delta", 
        "delta": {"content": "Mock response"}, 
        "timestamp": time.time()
    }))
    mock.close = AsyncMock()
    
    # Add methods needed for resilience testing
    async def flaky_send(*args, **kwargs):
        # Randomly fail sometimes
        if random.random() < 0.05:  # 5% failure rate
            raise Exception("Simulated random failure")
        await asyncio.sleep(0.01)
        return None
    
    # Set up special behavior for resilience testing if needed
    # mock.send.side_effect = flaky_send
    
    return mock 