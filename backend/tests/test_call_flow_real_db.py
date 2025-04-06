import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock, ANY
import uuid # Keep uuid module import
from uuid import UUID # Keep UUID type import
import asyncio
import json
import os # Import os for environment variables

from fastapi import FastAPI
from fastapi.testclient import TestClient
# Remove AsyncSession as we won't mock it
# from sqlalchemy.ext.asyncio import AsyncSession

# Assuming your FastAPI app instance is here
from app.main import app
# Keep DB import only if needed elsewhere, we won't override it
from app.database import get_db
# Keep settings imports
from app.core import get_settings, Settings
# Keep model imports
from app.models.user import User
# Keep service and function imports for patching targets
from app.services.open_ai_service import OpenAiService
from app.routes.ws_routes import get_calendar_events


# --- Test Configuration & Data ---
MOCK_CALLER_NUMBER = "+15551112222"
# Use the first user's Twilio number from the test data
TEST_DB_TWILIO_NUMBER = "+15550000001"
# Use the corresponding UUID from the test data
TEST_DB_USER_ID = UUID('a2d7200a-e061-460a-b5a2-afc47344caa9')
MOCK_STREAM_SID = f"MZ{uuid.uuid4().hex}"
MOCK_CALL_SID = f"CA{uuid.uuid4().hex}"
# Define the expected test URL for TestClient
TEST_STREAM_URL = "ws://testserver/audio-stream"
# Define Test DB URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_secretary_test"

# Remove mock_user fixture
# Remove mock_db_session fixture

@pytest.fixture()
def test_client_real_db() -> TestClient:
    """Fixture for the FastAPI TestClient configured for the REAL TEST DB and mock STREAM_URL."""

    # Define a dependency override for settings
    def get_test_settings() -> Settings:
        # Load original settings - but we will override DB and Stream URL
        # Important: Ensure dummy values for other required fields (API keys etc.)
        # or load from a base .env and only override DB/Stream
        # Simplest for now: create settings with only required overrides + dummies
        # You might need to adjust this based on your actual Settings model requirements
        settings_dict = {
            "DATABASE_URL": TEST_DATABASE_URL,
            "STREAM_URL": TEST_STREAM_URL,
            # Add other MANDATORY settings with dummy values
            "OPENAI_API_KEY": "dummy_openai_key",
            "TWILIO_ACCOUNT_SID": "dummy_twilio_sid",
            "TWILIO_AUTH_TOKEN": "dummy_twilio_token",
            "FRONTEND_URL": "http://dummy.com",
            "GOOGLE_CLIENT_ID": "dummy_google_id",
            "GOOGLE_CLIENT_SECRET": "dummy_google_secret",
            "JWT_SECRET_KEY": "dummy_jwt_secret",
        }
        return Settings(**settings_dict)

    # Override ONLY the settings dependency
    # The get_db dependency will use the DATABASE_URL from the overridden settings
    app.dependency_overrides[get_settings] = get_test_settings

    client = TestClient(app)
    yield client

    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_inbound_call_real_db_simulation(
    test_client_real_db: TestClient, # Use the new client fixture
    mock_openai_ws,  # Add the fixture parameter
    mock_calendar_data,  # Add the fixture parameter
):
    """
    Simulates the full inbound call flow using TestClient against the REAL TEST DB.
    1. Twilio HTTP POST to /calls/inbound (finds user in test DB)
    2. Verify TwiML Response (with test DB user ID)
    3. Twilio WebSocket Connects to /audio-stream
    4. App connects to Mock OpenAI WebSocket
    5. Audio is streamed from Twilio -> App -> Mock OpenAI
    Requires the ai_secretary_test DB to be running and populated.
    ONLY OpenAI Connect/Start, Calendar, Twilio End Call ARE PATCHED.
    """
    # Use the client fixture configured for the real test DB
    test_client = test_client_real_db

    # --- Patch external dependencies (OpenAI, Calendar, Twilio End Call) ---
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
        'app.routes.ws_routes.get_calendar_events',
        return_value=mock_calendar_data,
        new_callable=AsyncMock
    )
    patch_twilio_end_call = patch(
        'app.services.twilio_service.TwilioService.end_call',
        new_callable=MagicMock
    )

    with patch_openai_connect as mock_connect, \
         patch_openai_start as mock_start_session, \
         patch_calendar as mock_get_calendar, \
         patch_twilio_end_call as mock_end_call:

        # 1. Simulate Twilio HTTP POST using the test user's Twilio number
        print("--- Simulating HTTP POST /calls/inbound (Real Test DB) ---")
        response = test_client.post(
            "/calls/inbound",
            data={"From": MOCK_CALLER_NUMBER, "To": TEST_DB_TWILIO_NUMBER}
        )

        # 2. Verify TwiML Response (uses TestClient stream URL and real user ID)
        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/xml'
        twiml_response = response.text
        print(f"Received TwiML: {twiml_response}")
        assert "<Response>" in twiml_response
        assert "<Connect>" in twiml_response
        assert f'<Stream url="{TEST_STREAM_URL}">' in twiml_response
        assert f'<Parameter name="user_id" value="{TEST_DB_USER_ID}"/>' in twiml_response

        # 3. Simulate Twilio WebSocket Connects to /audio-stream
        print("--- Simulating WebSocket Connection /audio-stream (Real Test DB) ---")
        with test_client.websocket_connect("/audio-stream") as simulated_twilio_ws:
            print("WebSocket connected by simulated Twilio.")

            # 4. Simulate Twilio "start" event with the real test user ID
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
                        "user_id": str(TEST_DB_USER_ID)
                    }
                }
            }
            print(f"Sending 'start' event: {start_event}")
            simulated_twilio_ws.send_json(start_event)
            await asyncio.sleep(0.1) # Increased sleep for real DB interaction

            # 5. Verify external mocks (OpenAI, Calendar)
            print("Verifying mock calls after 'start' event...")
            mock_connect.assert_awaited_once()
            print("OpenAI connect mock awaited.")
            mock_get_calendar.assert_awaited_once()
            print("Calendar events mock awaited.")
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
                    "payload": "dummy_base64_encoded_audio_payload",
                }
            }
            print(f"Sending 'media' event: {media_event}")
            simulated_twilio_ws.send_json(media_event)
            await asyncio.sleep(0.1)

            # Verify audio forwarded to mock OpenAI
            print("Verifying audio forwarded to mock OpenAI...")
            expected_openai_payload = {
                "type": "input_audio_buffer.append",
                "audio": "dummy_base64_encoded_audio_payload",
            }
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
            await asyncio.sleep(0.1)

            print("Verifying mock_end_call was not called (unless expected)...")
            mock_end_call.assert_not_called()

        print("--- Real DB Simulation Complete ---") 