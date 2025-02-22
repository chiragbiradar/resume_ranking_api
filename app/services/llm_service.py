import logging
import json
import time
from typing import List, Dict
from openai import OpenAI
from fastapi import HTTPException
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class ResumeAnalyzer:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not found")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def _call_openai(self, messages: List[Dict], json_response: bool = False) -> str:
        """Simple wrapper for OpenAI API calls with retries"""
        max_retries = 3
        wait_time = 1  # seconds

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=settings.MODEL_NAME,
                    messages=messages,
                    temperature=0.1,
                    response_format={"type": "json_object"} if json_response else None,
                    timeout=30
                )
                return response.choices[0].message.content.strip()

            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"OpenAI API failed: {e}")
                    raise HTTPException(status_code=503, detail="AI service unavailable")
                time.sleep(wait_time * (attempt + 1))

    def _clean_name(self, name: str) -> str:
        """Clean and validate candidate name"""
        if not name or len(name.split()) < 2:
            return "Unknown Candidate"
            
        # Check if name has at least first and last name
        name_parts = name.strip().split()
        if len(name_parts) < 2:
            return "Unknown Candidate"
            
        # Validate each part is a proper name
        for part in name_parts:
            if not part.isalpha() or not part[0].isupper():
                return "Unknown Candidate"
                
        return " ".join(name_parts)

    async def get_candidate_info(self, resume_text: str) -> Dict[str, str]:
        """Extract basic info from resume"""
        messages = [
            {
                "role": "system",
                "content": "Extract candidate information from resumes. Be precise and factual."
            },
            {
                "role": "user",
                "content": f"Get candidate info from this resume. Return JSON with: name, years_experience, current_job, skills, education.\n\n{resume_text[:3000]}"
            }
        ]

        try:
            response = self._call_openai(messages, json_response=True)
            info = json.loads(response)
            
            # Clean and validate the data
            return {
                "name": self._clean_name(info.get("name", "")),
                "experience": info.get("years_experience", "Not specified"),
                "current_role": info.get("current_job", "Not specified"),
                "skills": info.get("skills", "Not specified"),
                "education": info.get("education", "Not specified")
            }
        except Exception as e:
            logger.error(f"Failed to extract candidate info: {e}")
            return {
                "name": "Unknown Candidate",
                "experience": "Not specified",
                "current_role": "Not specified",
                "skills": "Not specified",
                "education": "Not specified"
            }

    async def score_resume(self, resume_text: str, job_requirements: List[str]) -> Dict[str, int]:
        """Score resume against job requirements"""
        scores = {}
        total = 0

        # Get candidate background first
        candidate = await self.get_candidate_info(resume_text)
        
        for req in job_requirements:
            messages = [
                {
                    "role": "system",
                    "content": f"""Score this requirement for candidate: {candidate['name']}
                    Background: {candidate['experience']} experience, {candidate['current_role']}
                    Score 0-5 where:
                    0: No match
                    1: Basic/entry level
                    2: Some experience
                    3: Meets requirement
                    4: Exceeds requirement
                    5: Expert level
                    Return only the score number."""
                },
                {
                    "role": "user",
                    "content": f"Requirement: {req}\n\nResume:\n{resume_text[:5000]}"
                }
            ]

            try:
                score_text = self._call_openai(messages)
                score = min(5, max(0, int(score_text)))
                scores[req] = score
                total += score
            except Exception as e:
                logger.warning(f"Failed to score requirement '{req}': {e}")
                scores[req] = 0

        scores["total_score"] = total
        return scores

    async def extract_requirements(self, job_desc: str) -> List[str]:
        """Get key requirements from job description"""
        messages = [
            {
                "role": "system",
                "content": "Extract specific, measurable job requirements. Focus on technical skills, experience, and qualifications."
            },
            {
                "role": "user",
                "content": f"List the main requirements from this job post. Return as JSON array of strings.\n\n{job_desc[:10000]}"
            }
        ]

        try:
            response = self._call_openai(messages, json_response=True)
            data = json.loads(response)
            
            # Clean and validate requirements
            reqs = []
            for req in data.get("requirements", [])[:settings.MAX_CRITERIA]:
                if isinstance(req, str) and len(req.strip()) > 10:
                    reqs.append(req.strip())
            
            if not reqs:
                raise ValueError("No valid requirements found")
            
            return reqs
            
        except Exception as e:
            logger.error(f"Failed to extract requirements: {e}")
            raise HTTPException(
                status_code=500,
                detail="Could not process job requirements"
            )
