from pathlib import Path

import streamlit as st
import requests

# def workflow_trigger():
st.set_page_config(page_title="n8n Pipeline Trigger",
                page_icon="🚀", layout="wide")

st.title("n8n Workflow Trigger")

if "pdf_url" not in st.session_state:
    st.session_state.pdf_url = None

col1, col2 = st.columns([2, 3])

with col1:
    with st.expander("Select file"):
        response = requests.get(
            "http://python-api:8000/supabase/storage/pdf-files", params={"path": "tenders"})

        options = tuple(d.get("name", None) for d in response.json())

        pdf_name = st.selectbox(
            "Select the .pdf file to work with",
            options,
            index=None,
        )

        md_path = ""

        if pdf_name:
            pdf_path = Path(f"tenders/{pdf_name}")
            prefix = pdf_path.parent.name[:-1]
            md_path = f'{prefix}_{pdf_path.stem}/{prefix}_{pdf_path.stem}.md'

            md_file_res = requests.get(
                "http://python-api:8000/supabase/storage/processed-files", params={"path": f'{prefix}_{pdf_path.stem}/'})

            if md_file_res.status_code == 200 and len(md_file_res.json()) > 0:
                st.success(f'`{md_path}` OK')
            else:
                st.warning(f'`{md_path}` not found')

        preview_pdf = st.button("Preview PDF", width="stretch", type="primary")

        if preview_pdf:
            if pdf_name:
                try:
                    signed_url_res = requests.get(
                        "http://python-api:8000/supabase/storage/signed-url/pdf-files?",
                        params={"path": f"tenders/{pdf_name}"}
                    )
                    if signed_url_res.status_code == 200:
                        st.session_state.pdf_url = signed_url_res.json().get("signedURL", None)
                        st.toast("Success - File URL retrived")
                    else:
                        st.error(f"Error: {signed_url_res.status_code}")
                except Exception as e:
                    st.error(f"Failed to connect: {e}")
            else:
                st.warning("Please select a pdf file.")

    with st.expander("Pipeline params"):
        tender_url = st.text_input(
            "Tender URL", placeholder="https://banca.com.br/concurso")

        st.text("Select the document sections for each extraction:")

        base_entities_tab, exam_subtopics_tab, job_roles_tab, offices_tab = st.tabs(
            ["Base entities", "Exam subtopics", "Job roles", "Offices"])

        base_entities_sections = []
        exam_subtopics_sections = []
        job_roles_sections = []
        offices_sections = []

        headers_res = requests.get('http://python-api:8000/document-processing/file-headers',
                                params={"bucket": "processed-files", "file_path": md_path})

        with base_entities_tab:
            if headers_res:
                headers = headers_res.json()

                with st.container(height=450):
                    for i, header in enumerate(headers):
                        is_selected = st.checkbox(
                            f"`{header}`", key=f"base_entities_{i}")
                        base_entities_sections.append(
                            {"header": header, "selected": is_selected})
        with exam_subtopics_tab:
            if headers_res:
                headers = headers_res.json()

                with st.container(height=450):
                    for i, header in enumerate(headers):
                        is_selected = st.checkbox(
                            f"`{header}`", key=f"exam_subtopics_{i}")
                        exam_subtopics_sections.append(
                            {"header": header, "selected": is_selected})
        with job_roles_tab:
            if headers_res:
                headers = headers_res.json()

                with st.container(height=450):
                    for i, header in enumerate(headers):
                        is_selected = st.checkbox(
                            f"`{header}`", key=f"job_roles_{i}")
                        job_roles_sections.append(
                            {"header": header, "selected": is_selected})
        with offices_tab:
            if headers_res:
                headers = headers_res.json()

                with st.container(height=450):
                    for i, header in enumerate(headers):
                        is_selected = st.checkbox(
                            f"`{header}`", key=f"offices_{i}")
                        offices_sections.append(
                            {"header": header, "selected": is_selected})
        start_pipeline = st.button(
            "Start pipeline", width="stretch", type="primary")

with col2:
    if st.session_state.pdf_url:
        st.pdf(st.session_state.pdf_url, height=810)
    else:
        st.info("Select a file and click submit to preview the PDF.")

if start_pipeline:
    pipeline_trigger = requests.post("http://n8n:5678/webhook/754b5961-2b27-426b-822e-8c7d29c3c989",
                                    json={"file_path": md_path, "tender_url": tender_url, "base_entities_sections": base_entities_sections, "exam_subtopics_sections": exam_subtopics_sections, "job_roles_sections": job_roles_sections, "offices_sections": offices_sections})

    if pipeline_trigger.status_code == 200:
        st.session_state.offer_id = pipeline_trigger.json().get("id")
        st.switch_page("workflow_results.py")

        st.toast("Sucess - workflow started")
    else:
        st.toast("Failed to strat workflow")
