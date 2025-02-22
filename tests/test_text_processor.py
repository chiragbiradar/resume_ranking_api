import pytest
from fastapi import UploadFile, HTTPException
from pathlib import Path
from app.services.text_processor import TextProcessor
from unittest.mock import Mock, patch
import io

@pytest.fixture
def text_processor():
    return TextProcessor()

@pytest.fixture
def sample_pdf():
    content = b"%PDF-1.4\nSample PDF content"
    return UploadFile(
        filename="test.pdf",
        file=io.BytesIO(content)
    )

@pytest.fixture
def sample_docx():
    content = b"PK\x03\x04\x14\x00\x00\x00\x08\x00"  # DOCX magic numbers
    return UploadFile(
        filename="test.docx",
        file=io.BytesIO(content)
    )

@pytest.fixture
def invalid_file():
    return UploadFile(
        filename="test.txt",
        file=io.BytesIO(b"Some text")
    )

@pytest.fixture
def empty_file():
    return UploadFile(
        filename="empty.pdf",
        file=io.BytesIO(b"")
    )

class TestTextProcessor:
    def test_validate_file_accepts_pdf(self, text_processor, sample_pdf):
        """Should accept PDF files"""
        text_processor.validate_file(sample_pdf)  # Should not raise

    def test_validate_file_accepts_docx(self, text_processor, sample_docx):
        """Should accept DOCX files"""
        text_processor.validate_file(sample_docx)  # Should not raise

    def test_validate_file_rejects_invalid_type(self, text_processor, invalid_file):
        """Should reject files that aren't PDF or DOCX"""
        with pytest.raises(HTTPException) as exc:
            text_processor.validate_file(invalid_file)
        assert exc.value.status_code == 400
        assert "file type" in str(exc.value.detail).lower()

    def test_validate_file_rejects_empty_file(self, text_processor, empty_file):
        """Should reject empty files"""
        with pytest.raises(HTTPException) as exc:
            text_processor.validate_file(empty_file)
        assert exc.value.status_code == 400
        assert "empty" in str(exc.value.detail).lower()

    @patch("app.services.text_processor.extract_text_from_pdf")
    def test_extract_text_from_pdf(self, mock_extract, text_processor, sample_pdf):
        """Should correctly extract text from PDF"""
        expected_text = "Sample extracted text"
        mock_extract.return_value = expected_text
        
        result = text_processor.extract_text(sample_pdf)
        assert result == expected_text
        mock_extract.assert_called_once()

    @patch("app.services.text_processor.extract_text_from_docx")
    def test_extract_text_from_docx(self, mock_extract, text_processor, sample_docx):
        """Should correctly extract text from DOCX"""
        expected_text = "Sample extracted text"
        mock_extract.return_value = expected_text
        
        result = text_processor.extract_text(sample_docx)
        assert result == expected_text
        mock_extract.assert_called_once()

    def test_extract_text_handles_errors(self, text_processor, sample_pdf):
        """Should handle extraction errors gracefully"""
        with patch("app.services.text_processor.extract_text_from_pdf", side_effect=Exception("Extraction failed")):
            with pytest.raises(HTTPException) as exc:
                text_processor.extract_text(sample_pdf)
            assert exc.value.status_code == 500
            assert "extract" in str(exc.value.detail).lower()
