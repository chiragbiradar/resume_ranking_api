from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from typing import List
import pandas as pd
from io import BytesIO
import logging

from app.services.text_processor import TextProcessor
from app.services.llm_service import ResumeAnalyzer
from app.models.resume import CriteriaResponse, ErrorResponse
from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

@router.post(
    "/extract-criteria",
    response_model=CriteriaResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def extract_criteria(
    file: UploadFile = File(...),
    text_processor: TextProcessor = Depends(TextProcessor),
    analyzer: ResumeAnalyzer = Depends(ResumeAnalyzer)
):
    """Extract key requirements from a job description"""
    try:
        await text_processor.validate_file(file)
        text = await text_processor.extract_text(file)
        requirements = await analyzer.extract_requirements(text)
        return CriteriaResponse(criteria=requirements)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process job description: {e}")
        raise HTTPException(500, "Failed to process job description")

@router.post(
    "/score-resumes",
    responses={
        200: {"content": {"text/csv": {}}},
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def score_resumes(
    files: List[UploadFile] = File(...),
    requirements: List[str] = Query(...),
    text_processor: TextProcessor = Depends(TextProcessor),
    analyzer: ResumeAnalyzer = Depends(ResumeAnalyzer)
):
    """Score multiple resumes against requirements"""
    try:
        if not requirements:
            raise HTTPException(400, "No requirements provided")
            
        if len(files) > settings.MAX_FILES:
            raise HTTPException(400, f"Too many files. Maximum is {settings.MAX_FILES}")

        results = []
        for resume in files:
            try:
                await text_processor.validate_file(resume)
                text = await text_processor.extract_text(resume)
                
                # Get candidate info and scores
                candidate = await analyzer.get_candidate_info(text)
                scores = await analyzer.score_resume(text, requirements)
                
                # Combine results
                result = {
                    "Name": candidate["name"],
                    "Experience": candidate["experience"],
                    "Current Role": candidate["current_role"],
                    "Education": candidate["education"],
                    "Skills": candidate["skills"]
                }
                
                # Add individual scores
                for req in requirements:
                    result[f"Score - {req}"] = scores.get(req, 0)
                result["Total Score"] = scores.get("total_score", 0)
                
                results.append(result)
                
            except Exception as e:
                logger.warning(f"Failed to process {resume.filename}: {e}")
                continue

        if not results:
            raise HTTPException(400, "No valid resumes to process")

        # Create CSV response
        df = pd.DataFrame(results)
        df = df.sort_values("Total Score", ascending=False)
        
        output = BytesIO()
        df.to_csv(output, index=False, encoding="utf-8")
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=resume_scores.csv"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume scoring failed: {e}")
        raise HTTPException(500, "Failed to process resumes")
