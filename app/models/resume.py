from pydantic import BaseModel
from typing import List, Dict, Optional

class CriteriaResponse(BaseModel):
    """Response model for extracted job criteria"""
    criteria: List[str]

class CandidateInfo(BaseModel):
    """Model for candidate information"""
    name: str
    experience: str
    current_role: str
    skills: str
    education: str

class ResumeScore(BaseModel):
    """Model for resume scoring results"""
    candidate_info: CandidateInfo
    requirement_scores: Dict[str, int]
    total_score: int

class ErrorResponse(BaseModel):
    """Model for error responses"""
    detail: str
