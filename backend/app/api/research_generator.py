# In backend/app/api/research_generator.py or similar
from fastapi import APIRouter, HTTPException
from ..services.gemini_generator import ResearchPaperGenerator

router = APIRouter()
generator = ResearchPaperGenerator()

@router.post("/generate-paper")
async def generate_research_paper(request_data: dict):
    try:
        topic = request_data.get("topic")
        sections = request_data.get("sections")
        word_count = request_data.get("wordCount", 3000)
        
        if not topic:
            raise HTTPException(status_code=400, detail="Topic is required")
            
        paper = generator.generate_research_paper(topic, sections, word_count)
        return {"paper": paper}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))