from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import insert
from app.database import get_db
from app.models.user import User

router = APIRouter()

@router.get("/healthcheck")
async def health_status():
    return JSONResponse(content={"status": "ok"}, status_code=200)