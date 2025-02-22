import pytest
from unittest.mock import patch, Mock
from app.services.llm_service import ResumeAnalyzer
from fastapi import HTTPException

@pytest.fixture
def mock_openai():
    with patch("app.services.llm_service.OpenAI") as mock:
        yield mock

@pytest.fixture
def analyzer(mock_openai):
    return ResumeAnalyzer()

@pytest.fixture
def sample_resume():
    return """
    John Smith
    Senior Software Engineer
    
    Experience:
    - 8 years of Python development
    - Lead developer at Tech Corp
    - AWS certified developer
    
    Education:
    - MS in Computer Science
    """

@pytest.fixture
def sample_requirements():
    return [
        "5+ years Python experience",
        "AWS certification",
        "Bachelor's degree in CS"
    ]

class TestResumeAnalyzer:
    def test_init_requires_api_key(self, mock_openai):
        """Should require OpenAI API key"""
        with patch("app.services.llm_service.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            with pytest.raises(ValueError) as exc:
                ResumeAnalyzer()
            assert "api key" in str(exc.value).lower()

    def test_clean_name_validates_format(self, analyzer):
        """Should properly validate and clean names"""
        # Valid names
        assert analyzer._clean_name("John Smith") == "John Smith"
        assert analyzer._clean_name("Mary Jane Watson") == "Mary Jane Watson"
        
        # Invalid names
        assert analyzer._clean_name("john") == "Unknown Candidate"
        assert analyzer._clean_name("123 456") == "Unknown Candidate"
        assert analyzer._clean_name("") == "Unknown Candidate"

    async def test_get_candidate_info_success(self, analyzer, sample_resume):
        """Should extract candidate info correctly"""
        mock_response = {
            "name": "John Smith",
            "years_experience": "8 years",
            "current_job": "Senior Software Engineer",
            "skills": "Python, AWS",
            "education": "MS in Computer Science"
        }
        
        with patch.object(analyzer, "_call_openai", return_value=str(mock_response)):
            info = await analyzer.get_candidate_info(sample_resume)
            assert info["name"] == "John Smith"
            assert info["experience"] == "8 years"
            assert "Python" in info["skills"]

    async def test_get_candidate_info_handles_errors(self, analyzer, sample_resume):
        """Should handle API errors gracefully"""
        with patch.object(analyzer, "_call_openai", side_effect=Exception("API Error")):
            info = await analyzer.get_candidate_info(sample_resume)
            assert info["name"] == "Unknown Candidate"
            assert info["experience"] == "Not specified"

    async def test_score_resume_calculates_correctly(self, analyzer, sample_resume, sample_requirements):
        """Should score resumes accurately"""
        mock_scores = {"0": "4", "1": "5", "2": "3"}  # Simulated scores for each requirement
        
        with patch.object(analyzer, "_call_openai", side_effect=mock_scores.values()):
            scores = await analyzer.score_resume(sample_resume, sample_requirements)
            
            assert len(scores) == len(sample_requirements) + 1  # +1 for total_score
            assert all(0 <= score <= 5 for req, score in scores.items() if req != "total_score")
            assert scores["total_score"] == sum(score for req, score in scores.items() if req != "total_score")

    async def test_score_resume_handles_invalid_scores(self, analyzer, sample_resume, sample_requirements):
        """Should handle invalid score responses"""
        with patch.object(analyzer, "_call_openai", return_value="invalid"):
            scores = await analyzer.score_resume(sample_resume, sample_requirements)
            assert all(score == 0 for req, score in scores.items() if req != "total_score")

    async def test_extract_requirements_success(self, analyzer):
        """Should extract requirements correctly"""
        job_desc = "Looking for a senior developer with 5+ years Python experience and AWS certification"
        mock_response = '{"requirements": ["5+ years Python experience", "AWS certification"]}'
        
        with patch.object(analyzer, "_call_openai", return_value=mock_response):
            reqs = await analyzer.extract_requirements(job_desc)
            assert len(reqs) == 2
            assert any("Python" in req for req in reqs)
            assert any("AWS" in req for req in reqs)

    async def test_extract_requirements_handles_errors(self, analyzer):
        """Should handle requirement extraction errors"""
        with patch.object(analyzer, "_call_openai", side_effect=Exception("API Error")):
            with pytest.raises(HTTPException) as exc:
                await analyzer.extract_requirements("job description")
            assert exc.value.status_code == 500

    def test_call_openai_retries(self, analyzer):
        """Should retry failed API calls"""
        mock_response = Mock()
        mock_response.choices[0].message.content = "Success"
        
        with patch.object(analyzer.client.chat.completions, "create",
                         side_effect=[Exception("Timeout"), Exception("Error"), mock_response]):
            result = analyzer._call_openai([{"role": "user", "content": "test"}])
            assert result == "Success"
