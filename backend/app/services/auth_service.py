from datetime import datetime, timedelta
import jwt
import secrets
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Request
import hashlib
import os
from dotenv import load_dotenv
import requests
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

    def _generate_fingerprint(self, request: Request) -> str:
        """Generate unique fingerprint based on request metadata"""
        fingerprint_data = f"{request.client.host}:{request.headers.get('user-agent')}:{request.headers.get('accept-language')}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()

    def create_access_token(self, user_id: int, request: Request) -> tuple[str, datetime]:
        """Create access token with fingerprint"""
        expires = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        # Generate fingerprint and CSRF token
        fingerprint = self._generate_fingerprint(request)
        csrf_token = secrets.token_hex(32)
        
        payload = {
            "sub": str(user_id),
            "exp": expires,
            "fingerprint": fingerprint,
            "csrf": csrf_token
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token, expires, csrf_token

    def verify_token(self, token: str, request: Request, csrf_token: str = None) -> int:
        """Verify JWT token with fingerprint and CSRF token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Verify fingerprint
            current_fingerprint = self._generate_fingerprint(request)
            if payload["fingerprint"] != current_fingerprint:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid request origin"
                )
            
            # Verify CSRF token
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
            print(f"Verifying token: {token}")  # Detailed logging
            
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
            
            print(f"Token Response Status: {token_response.status_code}")
            print(f"Token Response Body: {token_response.text}")
            
            if not token_response.ok:
                raise Exception(f"Token exchange failed: {token_response.text}")
            
            token_data = token_response.json()
            
            # Get user info using access token
            userinfo_response = requests.get(
                'https://www.googleapis.com/oauth2/v3/userinfo',
                headers={'Authorization': f'Bearer {token_data["access_token"]}'}
            )
            user_info = userinfo_response.json()
            
            return {
                'email': user_info['email'],
                'google_id': user_info['sub'],
                'full_name': user_info.get('name'),
                'profile_picture': user_info.get('picture'),
                'refresh_token': token_data.get('refresh_token')
            }
        except Exception as e:
            print(f"Token Verification Error: {str(e)}")
            raise

    async def get_or_create_user(self, db: AsyncSession, user_data: dict) -> User:
        try:
            # Use async query
            user = await db.execute(
                select(User).filter(User.email == user_data['email'])
            )
            user = user.scalar_one_or_none()
            
            if user:
                # Update existing user
                user.last_login = datetime.utcnow()
                user.profile_picture = user_data.get('profile_picture')
                user.calendar_connected = user_data.get('refresh_token') is not None
                
                if user_data.get('refresh_token'):
                    user.refresh_token = user_data['refresh_token']
                
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
                refresh_token=user_data.get('refresh_token')
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