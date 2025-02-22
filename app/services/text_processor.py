import logging
from typing import List, Dict
from fastapi import UploadFile, HTTPException
from pypdf import PdfReader
from docx import Document
from io import BytesIO
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class TextProcessor:
    @staticmethod
    async def validate_file(file: UploadFile) -> None:
        """Validate file type and size"""
        if file.content_type not in settings.ALLOWED_MIME_TYPES.keys():
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}. Allowed: PDF, DOCX"
            )
            
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file"
            )
        await file.seek(0)  # Reset file pointer

    @staticmethod
    async def extract_text(file: UploadFile) -> str:
        """Extract text from PDF or DOCX files"""
        try:
            content = await file.read()
            
            if file.content_type == "application/pdf":
                reader = PdfReader(BytesIO(content))
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
            elif "wordprocessingml.document" in file.content_type:
                doc = Document(BytesIO(content))
                text = "\n".join(para.text for para in doc.paragraphs if para.text.strip())
            else:
                text = ""
            
            await file.seek(0)  # Reset file pointer
            
            if not text.strip():
                raise HTTPException(
                    status_code=400,
                    detail="No text content found in file"
                )
                
            return text.strip()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to extract text from file"
            )
