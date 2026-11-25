# TripWise AI — Smart Travel Planner

**Live application:** https://tripwise-ai-mvnq7z7wqxeb2cmbxdxouz.streamlit.app/  
**GitHub repository:** https://github.com/suryaprakash87436/TripWise-AI

TripWise AI is an AI-assisted travel planner. It recommends destinations from a curated dataset using hybrid BM25 + TF-IDF retrieval and can generate a grounded itinerary using the Groq API.

## Features

- Personalized trip planning using total group budget, trip duration, number of travelers and travel preference.
- Hybrid BM25 + TF-IDF retrieval to find relevant destinations in the curated dataset.
- Optional Groq API generation using retrieved destination records as context.
- Local fallback itinerary when the Groq API key is not configured or the API is unavailable.
- Retrieved destination matches and relevance scores for transparency.
- Streamlit user interface.

## Technology stack

- **Language:** Python
- **Frontend:** Streamlit
- **Retrieval:** BM25, TF-IDF and cosine similarity
- **AI generation:** Groq API
- **Libraries:** scikit-learn, Requests, python-dotenv
- **Dataset:** Curated destination records in `data/destinations.txt`
- **Version control:** Git and GitHub
- **Deployment:** Streamlit Community Cloud

## How it works

```text
User enters trip details
        |
        v
Streamlit interface
        |
        v
TripPlanner builds a search query
        |
        v
Hybrid BM25 + TF-IDF retrieval
        |
        v
Top matching destination records
        |
        +---- Groq API configured? ---- Yes --> Grounded AI itinerary
        |                                  No  --> Local fallback itinerary
        v
Itinerary + retrieved destination matches
```

## Run locally

### 1. Clone the repository

```bash
git clone https://github.com/suryaprakash87436/TripWise-AI.git
cd TripWise-AI
```

### 2. Create and activate a virtual environment (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure the Groq API key (optional)

Create a local `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
```

Keep `.env` private. It is excluded from Git by `.gitignore`. Never commit or share your real API key. The app can still use its local retrieval fallback without a key.

### 5. Start the Streamlit app

```bash
streamlit run streamlit_app.py
```

Streamlit will display the local URL in the terminal, usually http://localhost:8501.

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with GitHub.
3. Create or deploy an app from this repository.
4. Set the **Main file path** to `streamlit_app.py`.
5. In the app settings, open **Secrets** and add:

```toml
GROQ_API_KEY = "your_groq_api_key"
GROQ_MODEL = "openai/gpt-oss-20b"
```

6. Save the secrets and deploy or reboot the app.

Do not put API keys in Python source files, README files, screenshots or Git commits.

## Dataset structure

The app reads destination information from:

```text
data/
  destinations.txt
```

The dataset contains destination records and fields such as destination name, state, travel type, budget estimates, attractions and travel tips.

## Important limitations

- Recommendations are limited to the destinations in the bundled dataset.
- Budget values are estimates from the dataset, not live quotations.
- The app does not provide live transport schedules, hotel availability, booking or payment.
- Groq-powered generation requires a valid API key and internet access. Without it, the local fallback can still generate a basic itinerary.

## Resume description

**TripWise AI — AI-Assisted Travel Planner | Python, Streamlit, Groq API, BM25, TF-IDF, scikit-learn**

- Built a travel-planning application that accepts budget, trip duration, group size and travel preferences.
- Implemented hybrid BM25 + TF-IDF retrieval to rank relevant destinations from a curated knowledge base.
- Integrated Groq API for itinerary generation grounded in retrieved destination records, with a local fallback mode.
- Deployed the application using Streamlit Community Cloud and managed API credentials through application secrets.

Only list features and deployment details that you have personally tested and verified.
