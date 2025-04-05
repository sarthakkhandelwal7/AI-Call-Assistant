import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock, ANY
from uuid import uuid4
import asyncio
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

# Assuming your FastAPI app instance is here
from app.main import app
# Assuming your dependency functions and classes are here
from app.database import get_db
from app.core import get_settings, Settings # Import settings dependencies
from app.models.user import User # Assuming User model location
# Assuming service and function locations - ADJUST THESE IMPORTS if necessary
from app.services.open_ai_service import OpenAiService
from app.routes.ws_routes import get_calendar_events


# --- Mock Data ---
MOCK_CALLER_NUMBER = "+15551112222"
MOCK_TWILIO_NUMBER = "+15553334444"
MOCK_USER_ID = uuid4()
MOCK_STREAM_SID = f"MZ{uuid4().hex}"
MOCK_CALL_SID = f"CA{uuid4().hex}"
# Define the expected test URL
TEST_STREAM_URL = "ws://testserver/audio-stream"

@pytest.fixture
def mock_user() -> User:
    """Fixture for a mock User object."""
    user = MagicMock(spec=User)
    user.id = MOCK_USER_ID
    user.twilio_number = MOCK_TWILIO_NUMBER
    # Add other necessary User attributes if your code uses them
    # user.email = "test@example.com"
    return user

@pytest_asyncio.fixture
async def mock_db_session(mock_user: User) -> AsyncSession:
    """Fixture for a mock SQLAlchemy AsyncSession."""
    session = AsyncMock(spec=AsyncSession)

    # Create a mock result object where scalar_one_or_none is a sync method
    mock_result = MagicMock() # Use MagicMock for sync method simulation
    mock_result.scalar_one_or_none.return_value = mock_user

    # Configure session.execute to be an AsyncMock that returns the sync mock_result
    session.execute = AsyncMock(return_value=mock_result)

    # Keep other necessary async mocks
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()

    # Remove the side effect function as direct return value is simpler here
    # async def execute_side_effect(*args, **kwargs):
    #     print(f"Mock DB Execute called with args: {args}")
    #     return mock_result
    # session.execute = AsyncMock(side_effect=execute_side_effect)

    return session

@pytest.fixture()
def test_client(mock_db_session: AsyncSession) -> TestClient:
    """Fixture for the FastAPI TestClient with DB and Settings overrides."""

    # Define a dependency override for settings
    def get_test_settings() -> Settings:
        # Load original settings to get other values potentially needed
        original_settings = get_settings()
        # Create a dictionary from the original settings
        settings_dict = original_settings.model_dump()
        # Override the specific setting for the test
        settings_dict["STREAM_URL"] = TEST_STREAM_URL
        # Return a new Settings instance with the modified value
        # This handles potential immutability (frozen=True)
        return Settings(**settings_dict)

    # Override dependencies
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_settings] = get_test_settings

    client = TestClient(app)
    yield client

    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_inbound_call_simulation(
    test_client: TestClient,
    mock_calendar_data: list,
    # We don't need mock_user or mock_db_session directly in the test function,
    # as they are used by the test_client fixture
):
    """
    Simulates the full inbound call flow:
    1. Twilio HTTP POST to /calls/inbound
    2. Verify TwiML Response
    3. Twilio WebSocket Connects to /audio-stream
    4. App connects to Mock OpenAI WebSocket
    5. Audio is streamed from Twilio -> App -> Mock OpenAI
    """
    # --- Patch external dependencies ---
    # Adjust the target paths if your imports differ in the actual route/service files
    patch_openai_connect = patch(
        'app.services.open_ai_service.OpenAiService.connect',
        return_value=mock_openai_ws,
        new_callable=AsyncMock
    )
    patch_openai_start = patch(
        'app.services.open_ai_service.OpenAiService.start_session',
        new_callable=AsyncMock
    )
    patch_calendar = patch(
        # IMPORTANT: Adjust this target based on where get_calendar_events is *used*
        # If ws_routes.py imports it as `from app.utils.calendar import get_calendar_events`,
        # then the target is 'app.routes.ws_routes.get_calendar_events'
        # If it's imported differently, adjust accordingly.
        'app.routes.ws_routes.get_calendar_events',
        return_value=mock_calendar_data,
        new_callable=AsyncMock # Use AsyncMock if get_calendar_events is async
    )
    # Example patch for an outbound Twilio call if needed (adjust method name)
    patch_twilio_end_call = patch(
        'app.services.twilio_service.TwilioService.end_call',
        new_callable=MagicMock # Use MagicMock if end_call is synchronous
    )

    # Use regular `with`, not `async with` for patch context managers
    with patch_openai_connect as mock_connect, \
         patch_openai_start as mock_start_session, \
         patch_calendar as mock_get_calendar, \
         patch_twilio_end_call as mock_end_call:

        # 1. Simulate Twilio HTTP POST to /calls/inbound
        print("--- Simulating HTTP POST /calls/inbound ---")
        response = test_client.post(
            "/calls/inbound",
            data={"From": MOCK_CALLER_NUMBER, "To": MOCK_TWILIO_NUMBER}
        )

        # 2. Verify TwiML Response
        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/xml'
        twiml_response = response.text
        print(f"Received TwiML: {twiml_response}")
        assert "<Response>" in twiml_response
        assert "<Connect>" in twiml_response
        # Check for Stream URL using the test URL
        assert f'<Stream url="{TEST_STREAM_URL}">' in twiml_response # Use defined constant
        assert f'<Parameter name="user_id" value="{MOCK_USER_ID}"/>' in twiml_response

        # 3. Simulate Twilio WebSocket Connects to /audio-stream
        print("--- Simulating WebSocket Connection /audio-stream ---")
        with test_client.websocket_connect("/audio-stream") as simulated_twilio_ws:
            print("WebSocket connected by simulated Twilio.")

            # 4. Simulate Twilio "start" event (triggers user lookup, OpenAI connect etc.)
            start_event = {
                "event": "start",
                "sequenceNumber": "1",
                "start": {
                    "accountSid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    "streamSid": MOCK_STREAM_SID,
                    "callSid": MOCK_CALL_SID,
                    "tracks": ["inbound"],
                    "mediaFormat": {"encoding": "mulaw", "sampleRate": 8000, "channels": 1},
                    "customParameters": {
                        "user_id": str(MOCK_USER_ID) # Ensure it's a string if expected
                    }
                }
            }
            print(f"Sending 'start' event: {start_event}")
            simulated_twilio_ws.send_json(start_event)

            # Allow background tasks like connect/start_session to run
            await asyncio.sleep(0.01)

            # 5. Verify external mocks were called correctly after "start"
            print("Verifying mock calls after 'start' event...")
            await asyncio.sleep(0.01)

            mock_connect.assert_awaited_once()
            print("OpenAI connect mock awaited.")
            mock_get_calendar.assert_awaited_once()
            print("Calendar events mock awaited.")
            # Check start_session args precisely
            mock_start_session.assert_awaited_once_with(
                ws=mock_openai_ws,
                events=mock_calendar_data
            )
            print("OpenAI start_session mock awaited with correct args.")


            # 6. Simulate Audio (Twilio -> App -> Mock OpenAI)
            media_event = {
                "event": "media",
                "sequenceNumber": "2",
                "media": {
                    "track": "inbound",
                    "chunk": "1",
                    "timestamp": "5",
                    "payload": "dummy_base64_encoded_audio_payload", # Replace with actual example if needed
                }
            }
            print(f"Sending 'media' event: {media_event}")
            simulated_twilio_ws.send_json(media_event)
            await asyncio.sleep(0.01)

            # Verify that the audio payload was sent to the mock OpenAI WebSocket
            print("Verifying audio forwarded to mock OpenAI...")
            expected_openai_payload = {
                "type": "input_audio_buffer.append",
                "audio": "dummy_base64_encoded_audio_payload",
            }
            # Assert that send (not send_json) was called with the JSON string
            mock_openai_ws.send.assert_awaited_with(json.dumps(expected_openai_payload))
            print("Mock OpenAI WebSocket received expected audio payload via send().")

            # 7. Simulate Call End (Twilio sends "stop")
            stop_event = {
                "event": "stop",
                "sequenceNumber": "3",
                "stop": {
                    "accountSid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    "callSid": MOCK_CALL_SID
                }
            }
            print(f"Sending 'stop' event: {stop_event}")
            simulated_twilio_ws.send_json(stop_event)
            await asyncio.sleep(0.01)

            # Add assertions for cleanup if necessary
            # e.g., mock_end_call.assert_called_once() if you expect it
            print("Verifying mock_end_call was not called (unless expected)...")
            mock_end_call.assert_not_called() # Assuming normal stop doesn't trigger end_call service method


        print("--- Simulation Complete ---")

# Add more tests for edge cases: user not found, WebSocket errors, etc.