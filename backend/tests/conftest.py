import sys
import os
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

# Add the project root directory (parent of 'tests') to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

print(f"Added {project_root} to sys.path")

# --- Common Fixtures ---

@pytest.fixture
def mock_calendar_data() -> list:
    """Fixture for mock calendar event data."""
    return [{"summary": "Meeting", "start": "2024-01-01T10:00:00", "end": "2024-01-01T11:00:00"}]

@pytest.fixture
def mock_openai_ws() -> AsyncMock:
    """Fixture for a mock OpenAI WebSocket connection."""
    websocket = AsyncMock(name="MockOpenAIWebSocket")
    websocket.send_json = AsyncMock()
    websocket.send_text = AsyncMock()
    websocket.send_bytes = AsyncMock()
    websocket.send = AsyncMock()
    websocket.receive_json = AsyncMock()
    websocket.receive_text = AsyncMock()
    websocket.receive_bytes = AsyncMock()
    websocket.recv = AsyncMock()
    websocket.close = AsyncMock()
    # Simulate a connected state for the `openai_ws.state.value == 1` check
    websocket.state = MagicMock()
    websocket.state.value = 1
    return websocket 