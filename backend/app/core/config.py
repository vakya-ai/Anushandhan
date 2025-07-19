from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API settings
    API_PREFIX: str = "/api"
    
    # MongoDB settings
    MONGODB_USERNAME: str
    MONGODB_PASSWORD: str
    MONGODB_CLUSTER: str
    MONGODB_DB_NAME: str
    MONGODB_URL: str  # Add this line to allow the mongodb_url field
    
    # Redis settings
    REDIS_URL: str
    
    # Gemini API settings
    GEMINI_API_KEY: str
    GEMINI_MODEL_NAME: str = "gemini-2.0-flash"

    # Google API settings
    GOOGLE_API_KEY: str
    
    # GitHub settings
    GITHUB_TOKEN: str
    
    class Config:
        env_file = "utf-8"

settings = Settings()