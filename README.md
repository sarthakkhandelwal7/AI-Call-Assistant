# AI Secretary

An intelligent call screening system. This AI secretary uses natural language processing to screen calls, manage schedules, and make intelligent decisions about call handling.

## Features

-   🎙️ Real-time call screening using OpenAI's Realtime API
-   📅 Google Calendar integration for schedule awareness
-   📞 Smart call handling (transfer, schedule, or end calls)
-   💬 Natural conversation with personality you want your assistant to be
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
    - Context-aware decision-making

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
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

### Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/sarthakkhandelwal7/AI-Call-Assistant
    cd ai-call-assistant/backend
    ```

2. Install dependencies:

    ```bash
    poetry install
    ```

3. Set up Google Calendar credentials (to register the application with Google):

    - Create a project in the Google Cloud Console
    - Enable Calendar API
    - Go to Credentials and generate OAuth 2.0 credentials 
    - Save GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env
    - Register http://localhost:3001 or your frontend uri in Authorized JavaScript origins

4. Start the server:
    ```bash
    poetry run uvicorn app.main:app --reload
    ```
5. Run the docker-compose file to run the front end in a docker container.
    - Frontend URL: http://localhost:3001
    - You can register your Google Calander to fetch events
   
## API Endpoints

### Call Management

-   `POST /calls/inbound`: Handle incoming Twilio calls
-   `POST /calls/outbound`: Initiate outbound calls
-   `GET /calls/status`: Check the current call status
-   `WS /audio-stream`: WebSocket endpoint for audio streaming

## Call Flow

1. The caller dials the Twilio number
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

### Acknowledgments
This project draws inspiration from [donna](https://github.com/raviriley/donna). It is a valuable reference while exploring and enhancing capabilities in building applications powered by LLMs like ChatGPT.
