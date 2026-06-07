# UTK AI HR

AI-powered HR Recruitment and Onboarding Platform built with FastAPI.

## Features

* JWT Authentication (Login & Signup)
* Email Invitation System using SMTP
* Job Creation & Management
* AI-Based ATS Resume Screening
* Bulk Resume Upload (PDF/DOCX)
* Resume Parsing & Candidate Ranking
* Video Interview Scheduling
* Google Meet Interview Invites
* OCR-Based Aadhaar & PAN Verification
* Employee Onboarding System
* Recommendation Letter Generation

## Technology Stack

### Backend

* FastAPI
* Python
* SQLAlchemy ORM
* Pydantic
* JWT Authentication

### Database

* SQLite (Development)
* PostgreSQL (Production Ready)

### AI Services

* Google Gemini API
* OpenAI API (Backup)
* Claude API (Backup)

### OCR & Document Verification

* Tesseract OCR
* pdf2image
* pdfminer

### Frontend

* HTML
* CSS
* JavaScript

## Installation

```bash
python -m venv .venv
```

Activate Virtual Environment:

```bash
.venv\Scripts\activate
```

Install Dependencies:

```bash
pip install -r requirements.txt
```

Run Application:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000
```

## Environment Variables

Create a `.env` file:

```env
DATABASE_URL=sqlite:///./data/app.db

JWT_SECRET=your_secret

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

GEMINI_API_KEY=your_key
OPENAI_API_KEY=your_key
CLAUDE_API_KEY=your_key
```

## Highlights

* AI-powered ATS scoring and candidate shortlisting
* Multi-LLM architecture with Gemini, OpenAI, and Claude backup support
* Easy database migration from SQLite to PostgreSQL by changing a single connection string
* Complete recruitment pipeline from hiring to onboarding

## Developer

**Utkrisht Singh**
B.Tech Computer Science Engineering
