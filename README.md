# AI Call Assistant

An intelligent call screening system using AI to screen calls, manage schedules, and make decisions about call handling based on real-time conversation analysis.

## Features

-   🎙️ Real-time call screening using OpenAI.
-   📅 Google Calendar integration for schedule awareness.
-   📞 Smart call handling (transfer, schedule appointment via SMS, or end spam calls).
-   💬 Natural language conversation capabilities.
-   📱 SMS integration via Twilio for scheduling links.
-   ☁️ Deployable to AWS using Terraform and Docker.

## Technical Architecture (AWS Deployment)

The deployed application utilizes the following AWS services:

-   **Frontend:** React application built as static assets, hosted on **S3** and served globally via **CloudFront** (HTTPS, CDN).
-   **Backend:** FastAPI application containerized with Docker, stored in **ECR**, and run using **AWS App Runner** for scalability and managed infrastructure.
-   **Database:** **RDS PostgreSQL** instance running within a private VPC subnet for data persistence.
-   **Secrets Management:** **AWS Secrets Manager** securely stores API keys (OpenAI, Twilio), Google OAuth credentials, and JWT secrets, injecting them into the App Runner environment at runtime.
-   **Networking:** A custom **VPC** with public and private subnets isolates resources. App Runner connects to the VPC to access the RDS database.
-   **Infrastructure as Code:** **Terraform** manages the provisioning and configuration of all AWS resources.

_For a diagram and detailed explanation of the infrastructure components, see the [AWS Deployment Guide](terraform/instructions.md)._

## Setup

This project supports both local development and deployment to AWS.

### 1. Local Development Setup

**Prerequisites:**

-   Python 3.11 or higher
-   Poetry (Python dependency manager)
-   Node.js and npm (for frontend development)
-   Docker (optional, for containerized testing)
-   Git
-   `ngrok` (or similar tunneling tool for receiving Twilio webhooks locally)
-   Twilio Account & Phone Number
-   OpenAI API Key
-   Google Cloud Project with OAuth 2.0 Credentials (Client ID is needed locally)

**Environment Variables (Local `.env`):**

Create a `.env` file in the project root directory. You only need the following for basic local backend/frontend operation (referencing `backend/app/core/config.py`):

```env
# Required
OPENAI_API_KEY=sk-...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
JWT_SECRET_KEY=generate_a_strong_random_secret_string # e.g., using openssl rand -hex 32

# Needed for Google Login (Frontend needs ID, Backend uses defaults locally if secret missing)
GOOGLE_CLIENT_ID=....apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=... # Optional locally, but needed for full backend auth flow testing


# Database (Example for local Postgres instance)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ai_call_assistant_dev

# Frontend URL (Used by React build)
FRONTEND_URL=http://localhost:3001 # Default React dev server port

# Set App Runner WS URL (for local Twilio testing via Ngrok)
# You'll need to run ngrok http 8000 and use the https URL here
STREAM_URL=wss://YOUR_NGROK_HTTPS_URL/audio-stream
```

_Note: For full local testing including Google login token exchange, you might need to set `GOOGLE_CLIENT_SECRET` and `GOOGLE_REDIRECT_URI` and configure your Google Cloud credentials for `http://localhost:8000/oauth2callback`._

**Installation & Running Locally:**

1.  **Clone:** `git clone https://github.com/sarthakkhandelwal7/AI-Call-Assistant.git`
2.  **Backend Setup:**
    ```bash
    cd AI-Call-Assistant/backend
    poetry install
    # Set up local database if needed
    # Run migrations (requires DATABASE_URL to be set)
    # alembic upgrade head
    # Start backend (listens on port 8000 by default)
    poetry run uvicorn app.main:app --reload
    ```
3.  **Frontend Setup:**
    ```bash
    cd ../frontend
    npm install
    # Start frontend (access at http://localhost:3001)
    npm start
    ```
4.  **Ngrok:** If testing Twilio webhooks:
    ```bash
    ngrok http 8000
    ```
    Update your Twilio number's webhook settings to use the ngrok HTTPS URL (e.g., `https://<ngrok_id>.ngrok.io/calls/inbound`) and set the `STREAM_URL` in your `.env`.

### 2. AWS Deployment

The application is designed to be deployed fully to AWS using the provided Terraform configuration. This includes setting up the VPC, RDS database, ECR repository, App Runner service, S3 bucket, CloudFront distribution, and all necessary IAM roles and secrets.

**For detailed, step-by-step deployment instructions, please see:**

➡️ **[AWS Deployment Guide](terraform/instructions.md)** ⬅️

## API Endpoints

-   `/auth/google-login`: Handles Google OAuth callback and authentication.
-   `/auth/get-user-info`: Retrieves information for the logged-in user.
-   `/auth/logout`: Logs the user out.
-   `/user/update-profile`: Updates user profile details.
-   `/calls/inbound`: Handles incoming Twilio calls (Twilio Webhook).
-   `/calls/status`: (GET) Check the current call status (if any).
-   `/ws/audio-stream`: WebSocket endpoint for bi-directional audio streaming during a call.
-   `/phone-number/...`: Endpoints for searching, buying, and retrieving Twilio numbers.
-   `/verify/...`: Endpoints for sending and checking phone verification OTPs via Twilio Verify.

## Development

### Running Tests

```bash
# Navigate to backend directory
cd backend
# Set necessary environment variables for testing if needed (e.g., test database URL)
poetry run pytest
```

### Stress Testing

See the [Stress Testing Documentation](backend/tests/stress_tests/README.md) for details on evaluating performance.

## Acknowledgments

This project draws inspiration from [donna](https://github.com/raviriley/donna).
