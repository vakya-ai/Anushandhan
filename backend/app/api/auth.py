from fastapi import APIRouter, Depends, HTTPException, Body, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
import jwt
from datetime import datetime
from app.core.database import get_database

# Import the Google Auth library
from google.oauth2 import id_token
from google.auth.transport import requests

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()

# IMPORTANT: Get your Google Client ID from your environment variables
# You can get this from the Google Cloud Console where you set up your OAuth credentials.
# It's the same one you're using in your frontend.
GOOGLE_CLIENT_ID = str # It's recommended to load this from an environment variable

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Securely validates a Google ID token and returns the user's information.
    """
    token = credentials.credentials
    try:
        # Verify the token with Google's servers
        id_info = id_token.verify_oauth2_token(
            token, requests.Request(), GOOGLE_CLIENT_ID
        )

        # The 'sub' field is Google's unique identifier for the user.
        return id_info

    except ValueError as e:
        # Token is invalid
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        # Handle other exceptions
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during authentication: {e}",
        )

@router.post("/google-signin")
async def google_signin(user_data: Dict[str, Any], db=Depends(get_database)):
    """
    Handle Google OAuth signin/signup
    Store user data in MongoDB
    """
    try:
        # Get users collection
        users_collection = db.get_collection("users")

        # Check if user already exists
        existing_user = await users_collection.find_one({"googleId": user_data.get("googleId")})

        if existing_user:
            # Update existing user's last login and token
            await users_collection.update_one(
                {"googleId": user_data.get("googleId")},
                {
                    "$set": {
                        "lastLogin": datetime.now(),
                        "token": user_data.get("token"),
                        "name": user_data.get("name"),
                        "email": user_data.get("email"),
                        "avatar": user_data.get("avatar")
                    }
                }
            )

            # Create a new session
            await db.get_collection("sessions").insert_one({
                "userId": user_data.get("googleId"),
                "startTime": datetime.now(),
                "active": True,
                "device": user_data.get("device", "unknown"),
                "lastActivity": datetime.now()
            })

            return {"status": "success", "message": "User logged in successfully", "isNewUser": False}
        else:
            # Create new user
            new_user = {
                "googleId": user_data.get("googleId"),
                "name": user_data.get("name"),
                "email": user_data.get("email"),
                "avatar": user_data.get("avatar"),
                "token": user_data.get("token"),
                "createdAt": datetime.now(),
                "lastLogin": datetime.now(),
                "chats": []
            }

            result = await users_collection.insert_one(new_user)

            # Create a new session
            await db.get_collection("sessions").insert_one({
                "userId": user_data.get("googleId"),
                "startTime": datetime.now(),
                "active": True,
                "device": user_data.get("device", "unknown"),
                "lastActivity": datetime.now()
            })

            return {"status": "success", "message": "User created successfully", "isNewUser": True}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in Google signin: {str(e)}")

@router.post("/logout")
async def logout(data: Dict[str, str] = Body(...), db=Depends(get_database)):
    """
    Handle user logout
    Update session in database
    """
    try:
        user_id = data.get("userId")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")

        # Update all active sessions for this user to inactive
        result = await db.get_collection("sessions").update_many(
            {"userId": user_id, "active": True},
            {"$set": {"active": False, "endTime": datetime.now()}}
        )

        return {"status": "success", "message": "Logged out successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in logout: {str(e)}")

@router.post("/track-activity")
async def track_activity(
    activity_data: Dict[str, Any],
    user=Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Track user activity
    Store in MongoDB
    """
    try:
        # Get the user ID from the token
        user_id = user.get("sub")

        # Create activity document
        activity = {
            "userId": user_id,
            "timestamp": datetime.now(),
            "type": activity_data.get("type"),
            "details": activity_data.get("details", {}),
            "sessionId": activity_data.get("sessionId")
        }

        # Store activity in database
        await db.get_collection("user_activities").insert_one(activity)

        # Update last activity timestamp in session
        if activity_data.get("sessionId"):
            await db.get_collection("sessions").update_one(
                {"_id": activity_data.get("sessionId")},
                {"$set": {"lastActivity": datetime.now()}}
            )

        return {"status": "success"}

    except Exception as e:
        # Log error but don't fail the request
        print(f"Error tracking activity: {str(e)}")
        return {"status": "error", "message": str(e)}