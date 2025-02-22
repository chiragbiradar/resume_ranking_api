# Resume Ranking API

A FastAPI-based service that helps recruiters and hiring managers automatically score resumes against job requirements. Built with Python 3.8+ and modern NLP techniques.

## 🚀 Quick Start

1. Clone the repo
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_key_here
   ```
5. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`. Check out the interactive docs at `http://localhost:8000/docs`.

## 📚 How It Works

### Job Requirements Extraction (`/extract-criteria`)

Upload a job description (PDF/DOCX) and get back a list of key requirements. The system:
1. Extracts text from the document
2. Uses AI to identify specific, measurable requirements
3. Returns a clean list of criteria to score against

Example response:
```json
{
    "criteria": [
        "5+ years Python development",
        "Experience with AWS services",
        "Bachelor's in Computer Science",
        "Strong knowledge of React"
    ]
}
```

### Resume Scoring (`/score-resumes`)

Upload multiple resumes and get back a detailed CSV with scores for each candidate. For each resume, we:
1. Extract the text content
2. Get candidate info (name, experience, skills, etc.)
3. Score each requirement on a 0-5 scale
4. Generate a comprehensive report

The scoring scale:
- 0: No match
- 1: Basic/entry level
- 2: Some experience
- 3: Meets requirement
- 4: Exceeds requirement
- 5: Expert level

## 🏗️ Project Structure

```
resume_ranking_api/
├── app/
│   ├── api/
│   │   └── endpoints.py      # API routes
│   ├── core/
│   │   └── config.py        # Settings & configuration
│   ├── models/
│   │   └── resume.py        # Pydantic models
│   ├── services/
│   │   ├── llm_service.py   # AI/NLP logic
│   │   └── text_processor.py # File handling
│   └── main.py             # FastAPI app setup
├── tests/                  # Test files
├── .env                    # Environment variables
└── requirements.txt        # Dependencies
```

## 🛠️ Key Components

### Text Processing
- Handles PDF and DOCX files
- Extracts clean text while preserving structure
- Validates file types and content

### LLM Service
- Uses OpenAI's GPT models for analysis
- Smart retry logic for API calls
- Consistent scoring algorithms

### API Layer
- Clean REST endpoints
- Proper error handling
- Streaming responses for large files

## 📝 API Documentation

### POST /extract-criteria
- **Input**: Job description file (PDF/DOCX)
- **Output**: JSON with key requirements
- **Limits**: Max file size 10MB

### POST /score-resumes
- **Input**: 
  - Multiple resume files
  - List of requirements
- **Output**: CSV file with scores
- **Limits**: Max 20 files per request

## ⚙️ Configuration

Key settings in `.env`:
```
OPENAI_API_KEY=your_key_here
MAX_FILES=20
MODEL_NAME=gpt-4
```

## 🔒 Security

- API keys stored in environment variables
- File type validation
- Size limits on uploads
- Sanitized file content

## 🧪 Testing

Run the test suite:
```bash
pytest
```

Key test areas:
- File processing
- Scoring accuracy
- API endpoints
- Error handling

## 📈 Future Improvements

1. Add bulk processing for large resume sets
2. Implement caching for repeated job descriptions
3. Add more detailed scoring breakdowns
4. Support more file formats
5. Add user authentication

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Run the tests
5. Submit a PR

## 📄 License

MIT License - feel free to use this in your projects!
