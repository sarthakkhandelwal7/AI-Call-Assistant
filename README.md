# AI Secretary

An intelligent call screening system inspired by Donna from the TV show Suits. This AI secretary uses natural language processing to screen calls, manage schedules, and make intelligent decisions about call handling.

## Features

-   🎙️ Real-time call screening using OpenAI's Realtime API
-   📅 Google Calendar integration for schedule awareness
-   📞 Smart call handling (transfer, schedule, or end calls)
-   💬 Natural conversation with Donna's personality
-   📱 SMS scheduling link integration
-   🔄 Real-time audio streaming and processing

## Technical Architecture

### Core Components

![Architecture Diagram Incoming calls](diagrams/architecture.png)

1. **FastAPI Backend Server**

    - RESTful endpoints for call handling
    - WebSocket support for real-time audio streaming
    - State management for call status

2. **OpenAI Integration**

    - Real-time audio processing
    - Natural language understanding
    - Context-aware decision making

3. **Twilio Integration**

    - Call handling (inbound/outbound)
    - Audio streaming
    - SMS capabilities

4. **Google Calendar Integration**
    - Schedule checking
    - Availability management

## Setup

### Prerequisites

-   Python 3.9 or higher
-   Poetry for dependency management
-   Twilio account and phone number
-   OpenAI API access
-   Google Cloud project with Calendar API enabled

### Environment Variables

```env
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=your_twilio_number
HARVEY_PHONE_NUMBER=target_transfer_number
STREAM_URL=your_websocket_url
OPENAI_API_KEY=your_openai_key
CALENDLY_URL=your_scheduling_link
```

### Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/ai-secretary.git
    cd ai-secretary
    ```

2. Install dependencies:

    ```bash
    poetry install
    ```

3. Set up Google Calendar credentials:

    - Create a project in Google Cloud Console
    - Enable Calendar API
    - Download credentials.json
    - Place in project root

4. Start the server:
    ```bash
    poetry run uvicorn app.main:app --reload
    ```

## API Endpoints

### Call Management

-   `POST /calls/inbound`: Handle incoming Twilio calls
-   `POST /calls/outbound`: Initiate outbound calls
-   `GET /calls/status`: Check current call status
-   `WS /ws`: WebSocket endpoint for audio streaming

## Call Flow

1. Caller dials Twilio number
2. Twilio webhooks to backend
3. WebSocket connection established
4. Audio streamed to OpenAI
5. AI makes decisions based on:
    - Conversation context
    - Calendar availability
    - Call importance
6. Actions executed:
    - Transfer to personal number
    - Send scheduling link
    - End call (for spam)

## Development

### Running Tests

```bash
poetry run pytest
```

### Local Development

1. Use ngrok for Twilio webhook:

    ```bash
    ngrok http 8000
    ```

2. Update Twilio webhook URL with ngrok URL

3. Start server in debug mode:
    ```bash
    poetry run uvicorn app.main:app --reload --port 8000
    ```
