from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API settings
    API_PREFIX: str = "/api"
    
    # MongoDB settings
    MONGODB_USERNAME: str = "varadkulkarni172"
    MONGODB_PASSWORD: str = "LemonLaw@1"
    MONGODB_CLUSTER: str = "academai.gxn18.mongodb.net"
    MONGODB_DB_NAME: str = "academai"
    MONGODB_URL: str = None  # Add this line to allow the mongodb_url field
    
    # Redis settings
    REDIS_URL: str = "redis-14949.c305.ap-south-1-1.ec2.redns.redis-cloud.com:14949"
    
    # Gemini API settings
    GEMINI_API_KEY: str = "AIzaSyCMsJUHU8dcXKpyUJabqTzmiYpVgj2SQ9k"
    GEMINI_MODEL_NAME: str = "gemini-2.0-flash"

    # Google API settings
    GOOGLE_API_KEY: str = "AIzaSyCx-YO4G7FLSTKIJPJE17BbDQBuo_xazEc"
    
    # GitHub settings
    GITHUB_TOKEN: str = "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"
    
    class Config:
        env_file = ".env"

settings = Settings()