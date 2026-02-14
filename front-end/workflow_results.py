import streamlit as st
import requests
import pandas as pd

st.set_page_config(layout="wide", page_title="Recruitment Management")

# Constants
API_BASE_URL = "http://python-api:8000/supabase"


def fetch_data(endpoint, params=None):
    """Generic helper to fetch data from your local API."""
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}", params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching {endpoint}: {e}")
        return []


# --- 1. URL & SESSION STATE ---
with st.expander("Recruitment offer ID"):
    offer_id = st.text_input("Recruitment offer ID",
                             st.session_state.get("offer_id"))

if not offer_id:
    st.warning("Please provide a recruitment offer ID")
    st.stop()

# State management for drill-downs
if "selected_exam_id" not in st.session_state:
    st.session_state.selected_exam_id = None
if "selected_topic_id" not in st.session_state:
    st.session_state.selected_topic_id = None

# --- ROW 1: HEADER METRICS ---
offer_data = fetch_data(f"recruitment-offers/{offer_id}")

if offer_data:
    st.title(f"{offer_data.get('name', 'Process')}")
    m1, m2, m3 = st.columns(3)
    m4, m5, m6 = st.columns(3)
    m1.metric("Status", offer_data.get("status", "-"))
    m2.metric("Board", offer_data.get("examining_boards", {}).get("name", "-"))
    m3.metric("Year", offer_data.get("year", "-"))
    m4.metric("Scope", offer_data.get("scope", "-"))
    m5.metric("State", offer_data.get("state", "-"))
    m6.metric("City", offer_data.get("city", "-"))

st.divider()

# --- ROW 2: EXAMS (Selector) ---
col_exam_header, col_exam_refresh = st.columns([0.9, 0.1])
with col_exam_header:
    st.subheader("Exams")
with col_exam_refresh:
    if st.button(":material/refresh:", key="refresh_exams"):
        st.rerun()

exams_list = fetch_data("exams", params={"offer_id": offer_id})
if exams_list:
    df_exams = pd.DataFrame(exams_list)
    df_exams.drop('recruitment_offer_id', axis=1, inplace=True)

    event_exam = st.dataframe(
        df_exams,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="exam_table",
        column_config={
            "id": st.column_config.TextColumn(
                "ID",
                help="The unique UUID for this record",
                width="small",
            ),
            "created_at": st.column_config.DatetimeColumn(
                "Timestamp",
                format="DD/MM/YY HH:mm",
                width="small",
            ),
        }
    )

    if len(event_exam.selection.rows) > 0:
        row_idx = event_exam.selection.rows[0]
        new_exam_id = df_exams.iloc[row_idx]["id"]
        if new_exam_id != st.session_state.selected_exam_id:
            st.session_state.selected_exam_id = new_exam_id
            st.session_state.selected_topic_id = None
            st.rerun()
else:
    st.info("No exams found.")

if st.session_state.selected_exam_id:
    st.divider()
    col_topics, col_subtopics = st.columns([0.4, 0.6])

    with col_topics:
        c1, c2 = st.columns([0.9, 0.1])
        c1.subheader("Topics")
        if c2.button(":material/refresh:", key="ref_topics"):
            st.rerun()

        topics_list = fetch_data(
            "topics", params={"exam_id": st.session_state.selected_exam_id})
        if topics_list:
            df_topics = pd.DataFrame(topics_list)

            event_topic = st.dataframe(
                df_topics,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key="topic_table",
                column_config={
                    "id": st.column_config.TextColumn(
                        "ID",
                        help="The unique UUID for this record",
                        width="small",
                    ),
                    "name": st.column_config.TextColumn(
                        "Topic Name",
                        width="large",
                    ),
                    "created_at": st.column_config.DatetimeColumn(
                        "Timestamp",
                        format="DD/MM/YY HH:mm",
                        width="small",
                    ),
                }
            )
            if len(event_topic.selection.rows) > 0:
                t_row_idx = event_topic.selection.rows[0]
                st.session_state.selected_topic_id = df_topics.iloc[t_row_idx]["id"]
        else:
            st.info("No topics available.")

    with col_subtopics:
        c1, c2 = st.columns([0.9, 0.1])
        c1.subheader("Subtopics")
        if c2.button(":material/refresh:", key="ref_sub"):
            st.rerun()

        if st.session_state.selected_topic_id:
            # Passing both Exam ID and Topic ID as requested
            sub_params = {
                "exam_id": st.session_state.selected_exam_id,
                "topic_id": st.session_state.selected_topic_id
            }
            subtopics = fetch_data("subtopics", params=sub_params)
            if subtopics:
                st.dataframe(subtopics, use_container_width=True, column_config={
                    "id": st.column_config.TextColumn(
                        "ID",
                        help="The unique UUID for this record",
                        width="small",
                    ),
                    "name": st.column_config.TextColumn(
                        "Topic Name",
                        width="large",
                    ),
                    "created_at": st.column_config.DatetimeColumn(
                        "Timestamp",
                        format="DD/MM/YY HH:mm",
                        width="small",
                    ),
                })
            else:
                st.info("No subtopics found for selection.")
        else:
            st.info("Select a topic to view subtopics.")

    # --- ROW 4: JOB ROLES ---
    st.divider()

    c1, c2 = st.columns([0.9, 0.1])
    c1.subheader("Job Roles")
    if c2.button(":material/refresh:", key="ref_roles"):
        st.rerun()

    roles = fetch_data(
        "job-roles", params={"exam_id": st.session_state.selected_exam_id})
    st.dataframe(roles, use_container_width=True, hide_index=True, column_config={
        "id": st.column_config.TextColumn(
            "ID",
            help="The unique UUID for this record",
            width="small",
        ),
        "created_at": st.column_config.DatetimeColumn(
            "Timestamp",
            format="DD/MM/YY HH:mm",
            width="small",
        ),
        "exam_id": None
    }, column_order=("id", "name", "salary", "openings", "has_cr_openings", "created_at"))

    # --- ROW 5: OFFICES ---
    st.divider()

    c1, c2 = st.columns([0.9, 0.1])
    c1.subheader("Offices")
    if c2.button(":material/refresh:", key="ref_off"):
        st.rerun()

    offices = fetch_data("offices", params={
                         "exam_id": st.session_state.selected_exam_id})
    st.dataframe(offices, use_container_width=True, hide_index=True, column_config={
        "id": st.column_config.TextColumn(
            "ID",
            help="The unique UUID for this record",
            width="small",
        ),
        "created_at": st.column_config.DatetimeColumn(
            "Timestamp",
            format="DD/MM/YY HH:mm",
            width="small",
        )
    })

if offer_data:
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        submit_selection = st.button(
            "Get signed file URL", width='stretch')

    signed_url_res = None

    if submit_selection:
        signed_url_res = requests.get(
            "http://python-api:8000/supabase/storage/signed-url/pdf-files?",
            params={"path": offer_data.get("pdf_file_path")}
        )

    with col2:
        st.link_button(
            "Preview file", signed_url_res.json().get("signedUrl") if signed_url_res is not None else "", width='stretch', disabled=(signed_url_res is None))
