import motor.motor_asyncio
import logging
import os
from urllib.parse import quote_plus

# Setup logging
logger = logging.getLogger(__name__)

# MongoDB connection information
MONGODB_USERNAME = os.getenv("MONGODB_USERNAME", "varadkulkarni172")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD", "LemonLaw@1")
MONGODB_HOST = os.getenv("MONGODB_HOST", "academai.gxn18.mongodb.net")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "academai")

async def init_db():
    """Initialize database connection and return database instance."""
    try:
        # Encode username and password for URL
        username = quote_plus(MONGODB_USERNAME)
        password = quote_plus(MONGODB_PASSWORD)
        
        # Generate MongoDB connection URL
        mongo_url = f"mongodb+srv://{username}:{password}@{MONGODB_HOST}/?retryWrites=true&w=majority&appName=academai&connectTimeoutMS=10000&socketTimeoutMS=10000"
        
        logger.info(f"Generated MongoDB URL: {mongo_url}")
        print(f"MongoDB URL: {mongo_url}")
        
        # Create client and connect to the database
        client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
        
        # Get database instance
        database = client[MONGODB_DATABASE]
        
        # Ping the database to verify connection
        await database.command("ping")
        
        return database
    
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise

async def get_database():
    """Get the database instance."""
    from app.main import db
    return db