import os
import json
import requests
from datetime import datetime, timedelta
from backend.app.models.calander import GoogleCredential
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

@router.post("/auth/google")
async def google_auth(credential: GoogleCredential):
    try:
        # Exchange the authorization code for tokens
        token_response = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'code': credential.code,
                'client_id': os.getenv('GOOGLE_CLIENT_ID'),
                'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
                'redirect_uri': credential.redirect_uri,
                'grant_type': 'authorization_code',
            },
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        )
        
        if not token_response.ok:
            raise HTTPException(status_code=400, detail=f"Failed to exchange code: {token_response.text}")
            
        tokens = token_response.json()
        
        # Calculate expiry time in ISO format
        expires_in = tokens.get('expires_in', 3600)  # Default to 1 hour if not provided
        expiry = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat() + "Z"
        
        # Create credentials dict that CalendarService can use
        credentials_dict = {
            'token': tokens.get('access_token'),
            'refresh_token': tokens.get('refresh_token'),
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'token_uri': "https://oauth2.googleapis.com/token",
            'scopes': ['https://www.googleapis.com/auth/calendar.events'],
            'expiry': expiry
        }
        
        # Create credentials directory if it doesn't exist
        os.makedirs('backend/credentials', exist_ok=True)
        
        # Save credentials to JSON file
        with open('backend/credentials/credentials.json', 'w') as f:
            json.dump(credentials_dict, f)
        
        return {"message": "Credentials saved successfully"}
        
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e)) 