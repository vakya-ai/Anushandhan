# backend/app/api/papers.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any

# Imports for secure token verification
from google.oauth2 import id_token
from google.auth.transport import requests
import os # Recommended for handling environment variables

router = APIRouter(prefix="/api/papers", tags=["papers"])
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

# Example of a protected endpoint in papers.py
@router.get("/my-papers")
async def get_my_papers(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Example protected endpoint to get papers belonging to the authenticated user.
    """
    # The user object is the payload from the verified Google token
    user_email = user.get("email")
    user_google_id = user.get("sub")

    # Here, you would add your logic to fetch papers from your database
    # based on the user_google_id.
    
    # For demonstration purposes, we'll just return a confirmation message.
    return {
        "message": f"Successfully accessed protected paper route for user {user_email}.",
        "userId": user_google_id,
        "papers": [
            {"id": "paper1", "title": "Example Paper Title 1"},
            {"id": "paper2", "title": "Example Paper Title 2"},
        ]
    }