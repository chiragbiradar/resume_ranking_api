import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, Mock
import io

client = TestClient(app)

@pytest.fixture
def sample_pdf():
    return {
        "file": ("test.pdf", io.BytesIO(b"%PDF-1.4\nTest content"), "application/pdf")
    }

@pytest.fixture
def sample_docx():
    return {
        "file": ("test.docx", io.BytesIO(b"PK\x03\x04"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    }

@pytest.fixture
def sample_requirements():
    return ["Python experience", "AWS knowledge"]

class TestEndpoints:
    def test_extract_criteria_success(self, sample_pdf):
        """Should successfully extract criteria from job description"""
        expected_criteria = ["5+ years Python", "AWS certification"]
        
        with patch("app.services.text_processor.TextProcessor.extract_text", return_value="Job description text"), \
             patch("app.services.llm_service.ResumeAnalyzer.extract_requirements", return_value=expected_criteria):
            
            response = client.post("/extract-criteria", files=sample_pdf)
            assert response.status_code == 200
            assert response.json()["criteria"] == expected_criteria

    def test_extract_criteria_invalid_file(self):
        """Should reject invalid file types"""
        files = {
            "file": ("test.txt", io.BytesIO(b"Invalid content"), "text/plain")
        }
        response = client.post("/extract-criteria", files=files)
        assert response.status_code == 400
        assert "file type" in response.json()["detail"].lower()

    def test_extract_criteria_empty_file(self, sample_pdf):
        """Should handle empty files"""
        files = {
            "file": ("empty.pdf", io.BytesIO(b""), "application/pdf")
        }
        response = client.post("/extract-criteria", files=files)
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_score_resumes_success(self, sample_pdf, sample_requirements):
        """Should successfully score resumes"""
        mock_scores = {
            "Python experience": 4,
            "AWS knowledge": 3,
            "total_score": 7
        }
        
        mock_candidate = {
            "name": "John Smith",
            "experience": "5 years",
            "current_role": "Developer",
            "skills": "Python, AWS",
            "education": "BS in CS"
        }
        
        with patch("app.services.text_processor.TextProcessor.extract_text", return_value="Resume content"), \
             patch("app.services.llm_service.ResumeAnalyzer.get_candidate_info", return_value=mock_candidate), \
             patch("app.services.llm_service.ResumeAnalyzer.score_resume", return_value=mock_scores):
            
            response = client.post(
                "/score-resumes",
                files=[("files", ("resume.pdf", io.BytesIO(b"%PDF-1.4\nTest"), "application/pdf"))],
                params={"requirements": sample_requirements}
            )
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/csv"
            assert "resume_scores.csv" in response.headers["content-disposition"]

    def test_score_resumes_no_requirements(self, sample_pdf):
        """Should reject requests without requirements"""
        response = client.post(
            "/score-resumes",
            files=[("files", ("resume.pdf", io.BytesIO(b"%PDF-1.4\nTest"), "application/pdf"))]
        )
        assert response.status_code == 422  # FastAPI validation error

    def test_score_resumes_too_many_files(self, sample_pdf, sample_requirements):
        """Should reject too many files"""
        with patch("app.core.config.get_settings") as mock_settings:
            mock_settings.return_value.MAX_FILES = 1
            
            response = client.post(
                "/score-resumes",
                files=[
                    ("files", ("resume1.pdf", io.BytesIO(b"%PDF-1.4\nTest"), "application/pdf")),
                    ("files", ("resume2.pdf", io.BytesIO(b"%PDF-1.4\nTest"), "application/pdf"))
                ],
                params={"requirements": sample_requirements}
            )
            
            assert response.status_code == 400
            assert "too many files" in response.json()["detail"].lower()

    def test_score_resumes_handles_processing_errors(self, sample_pdf, sample_requirements):
        """Should handle processing errors gracefully"""
        with patch("app.services.text_processor.TextProcessor.extract_text", side_effect=Exception("Processing error")):
            response = client.post(
                "/score-resumes",
                files=[("files", ("resume.pdf", io.BytesIO(b"%PDF-1.4\nTest"), "application/pdf"))],
                params={"requirements": sample_requirements}
            )
            
            assert response.status_code == 500
            assert "process" in response.json()["detail"].lower()
