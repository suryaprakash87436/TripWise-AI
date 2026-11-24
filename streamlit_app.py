"""Streamlit interface for TripWise AI. Run with: streamlit run streamlit_app.py"""
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from planner import TripPlanner

load_dotenv()

st.set_page_config(
    page_title="TripWise AI | Smart Travel Planner",
    page_icon="✈️",
    layout="wide",
)

def configure_groq_secrets():
    """Expose Streamlit Cloud secrets to the existing planner.py module."""
    try:
        api_key = st.secrets.get("GROQ_API_KEY", "")
        model = st.secrets.get("GROQ_MODEL", "openai/gpt-oss-20b")
        if api_key:
            os.environ["GROQ_API_KEY"] = str(api_key).strip()
        if model:
            os.environ["GROQ_MODEL"] = str(model).strip()
    except Exception as exc:
        st.warning(
            "Could not read Streamlit Secrets. Check Settings → Secrets and "
            "use valid TOML syntax."
        )
        st.caption(f"Secrets detail: {exc}")

def find_dataset() -> Path:
    """Find the dataset, including a folder accidentally named 'data  '."""
    root = Path(__file__).resolve().parent
    standard = root / "data" / "destinations.txt"
    if standard.is_file():
        return standard

    for folder in root.iterdir():
        if folder.is_dir() and folder.name.strip() == "data":
            candidate = folder / "destinations.txt"
            if candidate.is_file():
                return candidate

    raise FileNotFoundError(
        "Missing destinations.txt. Ensure the repository contains "
        "data/destinations.txt and the folder is named data."
    )

@st.cache_resource
def load_planner(dataset_path: str):
    return TripPlanner(data_path=dataset_path)

configure_groq_secrets()

st.title("✈️ TripWise AI")
st.subheader("Your smart travel planner")
st.write(
    "Create a trip plan using your budget, duration and interests. "
    "TripWise uses hybrid BM25 + TF-IDF retrieval with optional Groq AI generation."
)

with st.sidebar:
    st.header("About TripWise AI")
    st.write("**Retrieval:** Hybrid BM25 + TF-IDF")
    st.write("**AI generation:** Groq API (optional)")
    st.write("**Knowledge base:** Curated destination dataset")
    st.divider()
    st.caption(
        "Budget figures are dataset estimates, not live travel, hotel "
        "or transport quotations."
    )

try:
    dataset_path = find_dataset()
    planner = load_planner(str(dataset_path))
    st.success(f"Destination database loaded: {len(planner.destinations)} destinations")
except Exception as exc:
    st.error("TripWise AI could not load its destination database.")
    st.code(str(exc))
    st.info(
        "Check that GitHub contains data/destinations.txt and the folder is "
        "named exactly data (without extra spaces)."
    )
    st.stop()

st.markdown("### Build your trip")

with st.form("trip_planner_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        budget = st.number_input(
            "Total group budget (₹)", min_value=1, max_value=10_000_000,
            value=15_000, step=1_000
        )
    with col2:
        days = st.number_input(
            "Trip duration (days)", min_value=1, max_value=30,
            value=3, step=1
        )
    with col3:
        travelers = st.number_input(
            "Number of travelers", min_value=1, max_value=20,
            value=2, step=1
        )

    preference = st.text_input(
        "What kind of trip do you prefer?",
        value="beach and history",
        max_chars=120,
        placeholder="Example: beaches, nature, history, family",
    )
    submitted = st.form_submit_button(
        "✨ Generate my travel plan",
        type="primary",
        use_container_width=True,
    )

if submitted:
    clean_preference = preference.strip()
    if not clean_preference:
        st.error("Please enter your travel preference.")
    else:
        with st.spinner("Finding destinations and preparing your itinerary..."):
            try:
                result = planner.generate(
                    budget=float(budget),
                    days=int(days),
                    preference=clean_preference,
                    travelers=int(travelers),
                )
            except Exception as exc:
                st.error("The trip planner encountered an error.")
                st.exception(exc)
            else:
                st.success("Your travel plan is ready!")
                st.caption(f"Generation mode: {result.get('mode', 'Not specified')}")
                st.markdown("## Your itinerary")
                st.markdown(result.get("answer", "No itinerary was returned."))

                sources = result.get("sources", [])
                if sources:
                    st.markdown("## Retrieved destination matches")
                    st.dataframe(sources, use_container_width=True, hide_index=True)

                st.caption(
                    "Verify current local conditions and actual costs before booking. "
                    "TripWise does not provide live bookings."
                )
else:
    st.info("Enter your trip details above and click Generate my travel plan.")
