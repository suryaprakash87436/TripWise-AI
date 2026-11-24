# TripWise AI — Smart Travel Planner

A portfolio-ready Generative AI / Retrieval-Augmented Generation (RAG) travel-planning web application. It retrieves relevant destinations from a curated local dataset and can optionally use Groq API to produce a natural-language itinerary grounded in the retrieved records.

## Features

- Personalized destination recommendations from budget, duration, group size and travel preference.
- Hybrid BM25 + hybrid BM25 + TF-IDF retrieval with unigram/bigram matching and budget-aware reranking.
- Optional Groq generation grounded in retrieved destination records.
- Local fallback mode works without an LLM API key.
- Displays retrieved source destinations and relevance scores for transparency.
- Flask web UI, JSON API, health-check endpoint and input validation.
- Automated tests and Render deployment configuration.

## Architecture

```text
User form / JSON client
        |
        v
     Flask API
        |
        v
Input validation + query construction
        |
        v
Hybrid BM25 + hybrid BM25 + TF-IDF retrieval -> budget-aware reranking
        |
        v
Top destination records (data/destinations.txt)
        |
        +---- Groq API configured? ---- Yes --> Grounded itinerary generation
        |                                  No  --> Local fallback planner
        v
Answer + retrieved source records
        |
        v
Web UI / JSON response
```

## Run locally (Windows PowerShell)

```powershell
# 1. Extract the ZIP and enter the project folder
cd path\to\TripWise-AI

# 2. Create and activate a virtual environment
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 4. Create local environment configuration
Copy-Item .env.example .env

# 5. Run
python app.py
```

Open http://127.0.0.1:5000

Without `GROQ_API_KEY`, the app still works using local retrieval and a deterministic itinerary summary. To enable AI generation, add a valid Groq API key to `.env`. Never commit `.env` to GitHub.

## API

### `GET /health`
Returns service health status.

### `GET /api`
Returns project metadata and whether the Groq key is configured.

### `POST /plan`
Form fields or JSON:
```json
{
  "budget": 15000,
  "days": 3,
  "travelers": 2,
  "preference": "beach and history"
}
```

Example PowerShell request:
```powershell
$body = @{
  budget = 15000
  days = 3
  travelers = 2
  preference = "beach and history"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://127.0.0.1:5000/plan -Method Post -ContentType "application/json" -Body $body
```

## Run tests

```powershell
pip install pytest
python -m pytest -q
```

## Deploy to Render

1. Create a new GitHub repository named `TripWise-AI`.
2. Push the project files to that repository (commands below).
3. In Render, choose **New + → Web Service**, connect the GitHub repository.
4. Render detects `render.yaml`; verify build command `pip install -r requirements.txt` and start command `gunicorn app:app --workers 1 --threads 4 --timeout 120`.
5. Add `GROQ_API_KEY` as a secret environment variable in Render if you want Groq generation. If omitted, local fallback mode remains available.
6. Deploy and open the generated Render URL. Check `/health`.

### GitHub upload commands

Run these commands from the project folder after creating an empty GitHub repository. Replace `YOUR_GITHUB_USERNAME` with your GitHub username.

```powershell
git init
git add .
git status
git commit -m "Build TripWise AI RAG travel planner"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/TripWise-AI.git
git push -u origin main
```

## Resume description

**TripWise AI — RAG-Based Smart Travel Planner | Python, Flask, scikit-learn, Groq API, REST API**

- Developed an AI-assisted travel planning web application that recommends destinations and creates multi-day itineraries from user budget, trip duration, group size and preferences.
- Implemented a retrieval-augmented workflow using hybrid BM25 + hybrid BM25 + TF-IDF retrieval and budget-aware reranking over a curated destination knowledge base.
- Integrated optional Groq generation with retrieved context to reduce unsupported recommendations, plus a local fallback mode.
- Built Flask web and JSON API endpoints with input validation, health checks, source transparency and automated tests.
- Prepared cloud deployment using Gunicorn and Render configuration.

**Important:** Only claim features you have run and verified. The current dataset contains destination estimates, not live flight/hotel prices or real-time availability. Do not describe it as live booking software.

## Advanced improvements you can build next

1. Replace TF-IDF-only retrieval with a hybrid BM25 + vector embedding retriever and evaluate retrieval quality.
2. Add user accounts, saved trips and PostgreSQL persistence.
3. Add live weather and maps using official APIs, with source links and caching.
4. Add budget breakdown by transport, food, stay and activities, clearly labeling estimates.
5. Add multilingual output and downloadable PDF itineraries.
6. Add CI with GitHub Actions and test coverage reporting.

## Limitations

- Recommendations are limited to `data/destinations.txt`.
- Budget values are dataset estimates and are not live quotes.
- Groq generation requires a valid API key and internet access.
- Render's local filesystem may be ephemeral; this version does not store user accounts or saved trips.
