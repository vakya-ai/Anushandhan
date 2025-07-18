# backend/app/api/chats.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId
from typing import List, Dict, Any
from app.core.database import get_database
from pymongo.database import Database

# Imports for secure token verification
from google.oauth2 import id_token
from google.auth.transport import requests
import os # Recommended for handling environment variables

router = APIRouter(prefix="/api/chats", tags=["chats"])
security = HTTPBearer()

# It's best practice to load your Client ID from an environment variable
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", str)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Securely validates a Google ID token and returns the user's information.
    This function is now self-contained and secure.
    """
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Verify the token with Google's servers
        id_info = id_token.verify_oauth2_token(
            token, requests.Request(), GOOGLE_CLIENT_ID
        )

        # 'sub' is Google's unique ID for the user.
        return id_info

    except ValueError as e:
        # Catches invalid tokens (e.g., expired, wrong audience, bad signature)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        # Handle other potential errors during verification
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during authentication: {e}",
        )


@router.post("/")
async def create_chat(
    chat_data: Dict[str, Any],
    db: Database = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new chat session.
    """
    try:
        user_google_id = user.get("sub")  # Use 'sub' from the verified token
        chat_collection = db.get_collection("chats")
        
        new_chat = await chat_collection.insert_one({
            "userId": user_google_id,
            "title": chat_data.get("title", "New Chat"),
            "history": [],
            "createdAt": chat_data.get("createdAt")
        })
        
        return {"status": "success", "chatId": str(new_chat.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def get_chats(
    db: Database = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Retrieve all chats for the authenticated user.
    """
    try:
        user_google_id = user.get("sub")
        chats_collection = db.get_collection("chats")
        
        chats_cursor = chats_collection.find({"userId": user_google_id})
        chats = []
        async for chat in chats_cursor:
            chat["_id"] = str(chat["_id"]) # Convert ObjectId to string
            chats.append(chat)
            
        return chats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{chat_id}/history")
async def get_chat_history(
    chat_id: str,
    db: Database = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Retrieve the message history for a specific chat.
    """
    try:
        user_google_id = user.get("sub")
        chats_collection = db.get_collection("chats")

        chat = await chats_collection.find_one({
            "_id": ObjectId(chat_id),
            "userId": user_google_id  # Ensure the user owns this chat
        })

        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found or access denied")
            
        return {"history": chat.get("history", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))