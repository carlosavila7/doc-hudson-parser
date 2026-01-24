import streamlit as st
import requests

st.set_page_config(layout="wide")

# Constants
API_BASE_URL = "http://python-api:8000/supabase"  # Your local API address


def fetch_data(endpoint, params=None):
    """Generic helper to fetch data from your local API."""
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}", params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching {endpoint}: {e}")
        return None


# --- URL PARAMETER HANDLING ---
query_params = st.query_params
offer_id = query_params.get("recruitment_offer_id")

if not offer_id:
    st.warning("Please provide a ?recruitment_offer_id=... in the URL.")
    st.stop()

# --- HEADER METRICS (Recruitment Offer) ---
# We fetch this once to populate the top of the page
offer_data = fetch_data(f"recruitment-offers/{offer_id}")

if offer_data:
    st.title(f"{offer_data.get('name', 'N/A')}")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Status", offer_data.get("status", "Unknown"))
    col2.metric("Year", offer_data.get("year", "N/A"))
    col3.metric("City", offer_data.get("city", "N/A"))
    col4.metric("Scope", offer_data.get("scope", "N/A"))

st.divider()

# --- DYNAMIC DATA TABLES ---


def render_table_section(title, endpoint, param_key, param_val):
    """Renders a header, a refresh button, and the resulting dataframe."""
    st.subheader(title)
    if st.button(f"Refresh {title}", key=f"btn_{endpoint}"):
        # Streamlit buttons trigger a rerun by default
        st.toast(f"Refreshing {title}...")

    data = fetch_data(f"{endpoint}/{param_val}")

    if data:
        st.dataframe(data, use_container_width=True)
    else:
        st.info(f"No {title.lower()} found yet for this ID.")


# 1. Exams (Linked directly to recruitment_offer_id)
render_table_section("Exams", "exams", "offer_id", offer_id)

# For the following sections, we typically need an exam_id.
# We'll assume you want to see data for the FIRST exam found, or you can iterate.
exams = fetch_data(f"exams/{offer_id}")

if exams:
    # Example: Taking the first exam ID to populate related tables
    selected_exam_id = exams[0]['id']

    col_a, col_b = st.columns(2)

    with col_a:
        render_table_section("Topics", "topics", "exam_id", selected_exam_id)
        render_table_section("Subtopics", "subtopics",
                             "exam_id", selected_exam_id)

    with col_b:
        render_table_section("Offices", "offices", "exam_id", selected_exam_id)
        render_table_section("Job Roles", "job-roles",
                             "exam_id", selected_exam_id)
