"""Grounded destination retrieval and itinerary generation."""
import os
import re
import requests
from collections import Counter
import math
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class BM25Index:
    """Small self-contained BM25 Okapi index for the bundled destination corpus."""
    def __init__(self, tokenized_docs, k1=1.5, b=0.75):
        self.docs = tokenized_docs
        self.k1, self.b = k1, b
        self.avgdl = sum(map(len, self.docs)) / max(len(self.docs), 1)
        self.doc_freq = Counter()
        for doc in self.docs:
            self.doc_freq.update(set(doc))
        self.lengths = [len(doc) for doc in self.docs]

    def get_scores(self, query_tokens):
        scores = [0.0] * len(self.docs)
        n = len(self.docs)
        frequencies = Counter(query_tokens)
        for term, qf in frequencies.items():
            df = self.doc_freq.get(term, 0)
            if not df:
                continue
            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
            for i, doc in enumerate(self.docs):
                tf = doc.count(term)
                norm = tf + self.k1 * (1 - self.b + self.b * self.lengths[i] / max(self.avgdl, 1))
                scores[i] += qf * idf * (tf * (self.k1 + 1) / norm if norm else 0)
        return scores

def parse_destination_records(text):
    records = []
    for block in re.split(r"\n\s*\n", text.strip()):
        item = {}
        for line in block.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                item[key.strip().upper()] = value.strip()
        if item.get("DESTINATION"):
            records.append(item)
    return records

class TripPlanner:
    def __init__(self, data_path="data/destinations.txt"):
        path = Path(data_path)
        if not path.exists():
            path = Path(__file__).parent / data_path
        if not path.exists():
            raise FileNotFoundError(f"Destination dataset not found: {data_path}")
        self.destinations = parse_destination_records(path.read_text(encoding="utf-8"))
        if not self.destinations:
            raise ValueError("No destination records were found in the dataset.")
        self.documents = [
            " ".join(f"{k}: {v}" for k, v in record.items())
            for record in self.destinations
        ]
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        self.matrix = self.vectorizer.fit_transform(self.documents)
        self.tokenized_documents = [self._tokenize(doc) for doc in self.documents]
        self.bm25 = BM25Index(self.tokenized_documents)

    @staticmethod
    def _tokenize(text):
        return re.findall(r"[a-z0-9]+", text.lower())

    def retrieve(self, query, budget, days, top_k=4):
        # Hybrid retrieval: combine lexical BM25 relevance with TF-IDF cosine similarity.
        query_tokens = self._tokenize(query)
        bm25_scores = self.bm25.get_scores(query_tokens)
        bm25_max = max(bm25_scores) if len(bm25_scores) else 0
        bm25_norm = [score / bm25_max for score in bm25_scores] if bm25_max > 0 else bm25_scores
        query_vec = self.vectorizer.transform([query])
        tfidf_scores = cosine_similarity(query_vec, self.matrix).ravel()
        hybrid_scores = [0.55 * bm25 + 0.45 * float(tfidf) for bm25, tfidf in zip(bm25_norm, tfidf_scores)]
        ranked = sorted(enumerate(hybrid_scores), key=lambda pair: pair[1], reverse=True)
        # Keep retrieval relevance primary; budget is considered during ranking.
        selected = []
        for idx, score in ranked:
            record = self.destinations[idx]
            budget_text = (record.get("ESTIMATED_3_DAY_BUDGET", "") +
                           " " + record.get("ESTIMATED_DAILY_EXPENSE", ""))
            numbers = [int(x.replace(",", "")) for x in re.findall(r"\d[\d,]*", budget_text)]
            estimated = (sum(numbers[:2]) / 2) if len(numbers) >= 2 else None
            budget_fit = 0.15 if estimated and budget >= estimated * (days / 3) else 0
            selected.append((float(score) + budget_fit, record, float(score)))
        selected.sort(key=lambda x: x[0], reverse=True)
        return selected[:top_k]

    def _groq_answer(self, budget, days, preference, travelers, candidates):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return None
        model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
        context = "\n\n".join(
            "\n".join(f"{k}: {v}" for k, v in item.items())
            for _, item, _ in candidates
        )
        prompt = f"""You are TripWise AI, a careful travel planning assistant.
Use ONLY the supplied destination records. Never invent attractions, prices,
transport schedules, hotel availability or facts. If a detail is missing, say
it is not in the dataset. Treat the budget as the total group budget in INR.
Create a practical day-by-day outline for {days} days for {travelers} traveler(s).
User budget: INR {budget:,.0f}. Preference: {preference}.
Choose only from these retrieved records:
{context}
Return clear Markdown with: Recommended destination, Why it fits, Budget notes,
Day-by-day itinerary, Attractions from dataset, Travel tips, and Data limitations.
Do not claim exact live prices. Clearly label dataset estimates as estimates."""
        url = "https://api.groq.com/openai/v1/chat/completions"
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are TripWise AI, a careful travel planning assistant. Ground every claim in the provided destination records."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_completion_tokens": 1200
            },
            timeout=35
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    def _fallback_answer(self, budget, days, preference, travelers, candidates):
        if not candidates or candidates[0][2] < 0.015:
            return ("No strong match was found in the available destination dataset. "
                    "Try a broader preference such as beach, nature, history or family.")
        _, place, score = candidates[0]
        name = place.get("DESTINATION", "Selected destination")
        attractions = place.get("FAMOUS_FOR", "Not listed in the dataset")
        daily = place.get("ESTIMATED_DAILY_EXPENSE", "Not listed")
        total = place.get("ESTIMATED_3_DAY_BUDGET", "Not listed")
        tips = place.get("TRAVEL_TIPS", "Check local conditions before travelling.")
        lines = [
            f"## Recommended destination: {name}",
            f"**State:** {place.get('STATE', 'Not listed')}",
            f"**Why it fits:** Its listed travel types are {place.get('TRAVEL_TYPE', 'not specified')}. "
            f"This is the closest match to your preference: {preference}.",
            "",
            "## Budget notes",
            f"- Your entered group budget: ₹{budget:,.0f}",
            f"- Dataset daily estimate: {daily}",
            f"- Dataset 3-day estimate: {total}",
            "- These are dataset estimates, not live quotations. Confirm transport and accommodation costs.",
            "",
            "## Suggested itinerary",
        ]
        for day in range(1, days + 1):
            lines.append(f"- **Day {day}:** Explore {attractions}. "
                         "Choose activities according to local opening hours and your pace.")
        lines += ["", "## Attractions listed in the dataset", attractions,
                  "", "## Travel tips", tips,
                  "", f"**Travelers:** {travelers}",
                  "", "_AI generation is not configured; this plan uses grounded dataset retrieval._"]
        return "\n".join(lines)

    def generate(self, budget, days, preference, travelers=1):
        query = f"{preference} travel destination for {days} days, budget INR {budget}"
        candidates = self.retrieve(query, budget, days)
        try:
            answer = self._groq_answer(budget, days, preference, travelers, candidates)
            mode = "Groq API + hybrid BM25/TF-IDF retrieval" if answer else "Hybrid BM25/TF-IDF retrieval (local fallback)"
        except (requests.RequestException, KeyError, IndexError, ValueError):
            answer = None
            mode = "Hybrid retrieval (Groq API unavailable; local fallback)"
        if not answer:
            answer = self._fallback_answer(budget, days, preference, travelers, candidates)
        sources = [
            {"destination": item.get("DESTINATION", "Unknown"),
             "state": item.get("STATE", "Not listed"),
             "retrieval_score": round(score, 3)}
            for _, item, score in candidates
        ]
        return {"answer": answer, "mode": mode, "sources": sources}
