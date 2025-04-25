# In your main API file (likely in app/api/__init__.py or similar)
from .research_generator import router as research_router

# Add this to your existing router registration
# app.include_router(research_router, prefix="/research", tags=["research"])