from fastapi import APIRouter, Depends, HTTPException, Body, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, List, Any, Optional
import jwt
from datetime import datetime
from app.core.database import get_database
from bson import ObjectId

router = APIRouter(prefix="/api/chats", tags=["chats"])
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

@router.get("")
async def get_user_chats(user=Depends(get_current_user), db=Depends(get_database)):
    """
    Get all chats for the current user
    """
    try:
        # Get user ID from token
        user_id = user.get("sub")
        
        # Get chats collection
        users_collection = db.get_collection("users")
        
        # Find user and get their chats
        user_doc = await users_collection.find_one({"googleId": user_id})
        if not user_doc:
            return {"chats": []}
        
        chats = user_doc.get("chats", [])
        return {"chats": chats}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chats: {str(e)}")

@router.post("/sync")
async def sync_chats(
    data: Dict[str, List[Dict[str, Any]]] = Body(...),
    user=Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Sync chats from client to server
    """
    try:
        # Get user ID from token
        user_id = user.get("sub")
        
        # Get chats from request body
        chats = data.get("chats", [])
        
        # Mark each chat with user ID
        for chat in chats:
            chat["userId"] = user_id
        
        # Get users collection
        users_collection = db.get_collection("users")
        
        # Update user document with new chats
        await users_collection.update_one(
            {"googleId": user_id},
            {"$set": {"chats": chats}}
        )
        
        # Also store chat activity in activity collection for analytics
        chats_collection = db.get_collection("chats")
        
        # First remove existing chats for this user to avoid duplicates
        await chats_collection.delete_many({"userId": user_id})
        
        # Then insert all current chats
        if chats:
            # Add server timestamp and ensure each chat has required fields
            for chat in chats:
                chat["syncedAt"] = datetime.now()
                
                # Store messages separately if they exist and are too large
                if "messages" in chat and len(str(chat["messages"])) > 10000:
                    messages = chat["messages"]
                    chat_id = chat["id"]
                    
                    # First, delete any existing messages for this chat
                    await db.get_collection("chat_messages").delete_many({"chatId": chat_id})
                    
                    # Then store messages in chunks if needed
                    if messages:
                        for i in range(0, len(messages), 10):
                            chunk = messages[i:i+10]
                            await db.get_collection("chat_messages").insert_one({
                                "chatId": chat_id,
                                "userId": user_id,
                                "chunkIndex": i // 10,
                                "messages": chunk,
                                "createdAt": datetime.now()
                            })
                        
                        # Remove messages from chat object to avoid duplication
                        chat["messages"] = []
                        chat["hasStoredMessages"] = True
            
            # Insert all chats
            await chats_collection.insert_many(chats)
        
        return {"status": "success", "message": "Chats synced successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing chats: {str(e)}")

@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: str,
    user=Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Delete a chat
    """
    try:
        # Get user ID from token
        user_id = user.get("sub")
        
        # Get users collection
        users_collection = db.get_collection("users")
        
        # Find user and remove chat from their chats list
        user_doc = await users_collection.find_one({"googleId": user_id})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        chats = user_doc.get("chats", [])
        updated_chats = [chat for chat in chats if chat.get("id") != chat_id]
        
        # Update user document with new chats list
        await users_collection.update_one(
            {"googleId": user_id},
            {"$set": {"chats": updated_chats}}
        )
        
        # Also remove from chats collection
        await db.get_collection("chats").delete_many({"id": chat_id, "userId": user_id})
        
        # Delete messages for this chat
        await db.get_collection("chat_messages").delete_many({"chatId": chat_id, "userId": user_id})
        
        # Record deletion in activity log
        await db.get_collection("user_activities").insert_one({
            "userId": user_id,
            "type": "delete_chat",
            "details": {"chatId": chat_id},
            "timestamp": datetime.now()
        })
        
        return {"status": "success", "message": "Chat deleted successfully"}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting chat: {str(e)}")

@router.put("/{chat_id}/title")
async def update_chat_title(
    chat_id: str,
    data: Dict[str, str] = Body(...),
    user=Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Update chat title
    """
    try:
        # Get user ID from token
        user_id = user.get("sub")
        
        # Get new title from request body
        new_title = data.get("title")
        if not new_title:
            raise HTTPException(status_code=400, detail="Title is required")
        
        # Get users collection
        users_collection = db.get_collection("users")
        
        # Find user and update chat title
        user_doc = await users_collection.find_one({"googleId": user_id})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        chats = user_doc.get("chats", [])
        updated = False
        for chat in chats:
            if chat.get("id") == chat_id:
                chat["topic"] = new_title
                updated = True
                break
                
        if not updated:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        # Update user document with modified chats
        await users_collection.update_one(
            {"googleId": user_id},
            {"$set": {"chats": chats}}
        )
        
        # Also update in chats collection
        await db.get_collection("chats").update_one(
            {"id": chat_id, "userId": user_id},
            {"$set": {"topic": new_title}}
        )
        
        # Record title update in activity log
        await db.get_collection("user_activities").insert_one({
            "userId": user_id,
            "type": "update_chat_title",
            "details": {"chatId": chat_id, "newTitle": new_title},
            "timestamp": datetime.now()
        })
        
        return {"status": "success", "message": "Chat title updated successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
