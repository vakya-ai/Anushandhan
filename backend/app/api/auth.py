from fastapi import APIRouter, Depends, HTTPException, Body, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
import jwt
from datetime import datetime
from app.core.database import get_database

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        # Here we would normally verify the token with Google
        # For simplicity, we just decode it to get the user ID
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
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