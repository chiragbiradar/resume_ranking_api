from setuptools import setup, find_packages

setup(
    name="resume_ranking_api",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "python-multipart",
        "openai",
        "pandas",
        "python-docx",
        "pypdf",
        "pydantic",
        "pydantic-settings",
        "python-dotenv"
    ],
    extras_require={
        "test": [
            "pytest",
            "pytest-asyncio",
            "pytest-mock",
            "httpx"
        ]
    }
)
