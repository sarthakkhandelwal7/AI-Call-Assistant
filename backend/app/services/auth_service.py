from datetime import datetime, timedelta, timezone
import jwt
import secrets
from fastapi import HTTPException, status, Request
import hashlib
import os
from dotenv import load_dotenv
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from backend.app.models.user import User, UserCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

load_dotenv()

class AuthService:
    def __init__(self):
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.jwt_secret = os.getenv("JWT_SECRET_KEY")
        self.jwt_algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 30

    async def _get_user_timezone(self, refresh_token: str) -> str:
        """Get user's timezone from their primary calendar"""
        try:
            credentials = Credentials.from_authorized_user_info({
                'refresh_token': refresh_token,
                'client_id': self.google_client_id,
                'client_secret': self.google_client_secret,
                'scopes': ["https://www.googleapis.com/auth/calendar.events"]
            })
            
            service = build('calendar', 'v3', credentials=credentials)
            calendar = service.calendars().get(calendarId='primary').execute()
            return calendar.get('timeZone', 'UTC')
        except HttpError as error:
            print(f'Error fetching timezone: {error}')
            return 'UTC'

    def _generate_fingerprint(self, request: Request) -> str:
        """Generate unique fingerprint based on request metadata"""
        fingerprint_data = f"{request.client.host}:{request.headers.get('user-agent')}:{request.headers.get('accept-language')}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()

    def create_access_token(self, user_id: int, request: Request) -> tuple[str, datetime]:
        """Create access token with fingerprint"""
        expires = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        fingerprint = self._generate_fingerprint(request)
        csrf_token = secrets.token_hex(32)
        
        payload = {
            "sub": str(user_id),
            "exp": expires.timestamp(),
            "fingerprint": fingerprint,
            "csrf": csrf_token
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token, expires, csrf_token

    def verify_token(self, token: str, request: Request, csrf_token: str = None) -> int:
        """Verify JWT token with fingerprint and CSRF token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            current_fingerprint = self._generate_fingerprint(request)
            if payload["fingerprint"] != current_fingerprint:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid request origin"
                )
            
            if csrf_token and payload["csrf"] != csrf_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid CSRF token"
                )
            
            return int(payload["sub"])
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    async def verify_google_token(self, token: str) -> dict:
        try:
            print(f"Verifying token: {token}")
            
            token_response = requests.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'code': token,
                    'client_id': self.google_client_id,
                    'client_secret': self.google_client_secret,
                    'redirect_uri': os.getenv("FRONTEND_URL"),
                    'grant_type': 'authorization_code',
                }
            )
            
            if not token_response.ok:
                raise Exception(f"Token exchange failed: {token_response.text}")
            
            token_data = token_response.json()
            refresh_token = token_data.get('refresh_token')
            
            # Get user info using access token
            userinfo_response = requests.get(
                'https://www.googleapis.com/oauth2/v3/userinfo',
                headers={'Authorization': f'Bearer {token_data["access_token"]}'}
            )
            user_info = userinfo_response.json()
            
            # Get timezone if refresh token is available
            timezone = 'UTC'
            if refresh_token:
                timezone = await self._get_user_timezone(refresh_token)
            
            return {
                'email': user_info['email'],
                'google_id': user_info['sub'],
                'full_name': user_info.get('name'),
                'profile_picture': user_info.get('picture'),
                'refresh_token': refresh_token,
                'timezone': timezone
            }
        except Exception as e:
            print(f"Token Verification Error: {str(e)}")
            raise

    async def get_or_create_user(self, db: AsyncSession, user_data: dict) -> User:
        try:
            user = await db.execute(
                select(User).filter(User.email == user_data['email'])
            )
            user = user.scalar_one_or_none()
            
            if user:
                # Update existing user
                user.last_login = datetime.now(datetime.timezone.utc)
                user.profile_picture = user_data.get('profile_picture')
                user.calendar_connected = user_data.get('refresh_token') is not None
                
                if user_data.get('refresh_token'):
                    user.refresh_token = user_data['refresh_token']
                    # Update timezone when refresh token is updated
                    user.timezone = user_data.get('timezone', 'UTC')
                
                await db.commit()
                await db.refresh(user)
                return user

            # Create new user
            new_user = User(
                email=user_data['email'],
                google_id=user_data['google_id'],
                full_name=user_data['full_name'],
                profile_picture=user_data.get('profile_picture'),
                calendar_connected=user_data.get('refresh_token') is not None,
                refresh_token=user_data.get('refresh_token'),
                timezone=user_data.get('timezone', 'UTC'),
                created_at=datetime.now(timezone.utc),  # Explicitly set created_at
                last_login=None  # Make sure this is None or timezone-aware
            )
            
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            
            return new_user
        except Exception as e:
            await db.rollback()
            print(f"Database Error: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Database error: {str(e)}"
            )