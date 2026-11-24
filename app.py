import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from planner import TripPlanner

load_dotenv()
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024
planner = TripPlanner(data_path=os.getenv("DATA_PATH", "data/destinations.txt"))

@app.get("/")
def home():
    return render_template("index.html")

@app.post("/plan")
def plan_trip():
    payload = request.get_json(silent=True) if request.is_json else request.form
    payload = payload or {}
    try:
        budget = float(payload.get("budget", 0))
        days = int(payload.get("days", 0))
        preference = str(payload.get("preference", "")).strip()
        travelers = int(payload.get("travelers", 1))
        if budget <= 0 or budget > 10000000:
            raise ValueError("Enter a budget between ₹1 and ₹1 crore.")
        if not 1 <= days <= 30:
            raise ValueError("Trip duration must be between 1 and 30 days.")
        if not 1 <= travelers <= 20:
            raise ValueError("Travelers must be between 1 and 20.")
        if not preference or len(preference) > 120:
            raise ValueError("Enter a travel preference (up to 120 characters).")
        result = planner.generate(
            budget=budget, days=days, preference=preference, travelers=travelers
        )
        if request.is_json:
            return jsonify(result)
        return render_template("index.html", result=result)
    except (ValueError, TypeError) as exc:
        message = str(exc) or "Please check your inputs."
        if request.is_json:
            return jsonify({"error": message}), 400
        return render_template("index.html", error=message), 400
    except Exception:
        app.logger.exception("Trip planning failed")
        message = "The planner is temporarily unavailable. Please try again."
        if request.is_json:
            return jsonify({"error": message}), 500
        return render_template("index.html", error=message), 500

@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "TripWise AI"})

@app.get("/api")
def api_info():
    return jsonify({
        "name": "TripWise AI",
        "version": "2.0.0",
        "endpoints": {"health": "GET /health", "plan": "POST /plan"},
        "llm_configured": bool(os.getenv("GEMINI_API_KEY"))
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
