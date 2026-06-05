# UTK AI HR (FastAPI)

## Setup

1. Create a virtualenv and install deps:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Copy env file:

```bash
cp .env.example .env
```

3. Run the app:

```bash
uvicorn app.main:app --reload
```

Open http://localhost:8000 for the mock frontend.

## Notes

- JWT tokens are stored in SQLite.
- Gmail SMTP requires an app password.
- Gemini API key is optional; fallback tags are used if missing.
