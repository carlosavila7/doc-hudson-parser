from pathlib import Path

import streamlit as st
import requests

# def workflow_trigger():
st.set_page_config(page_title="Pipeline Trigger",
                   page_icon=":material/home:", layout="wide")

st.title("n8n Workflow Trigger")

if "pdf_url" not in st.session_state:
    st.session_state.pdf_url = None

with st.expander("Select file"):
    response = requests.get(
        "http://python-api:8000/supabase/storage/pdf-files", params={"path": "tenders"})
    files_list = response.json()
    options = [f['name']
               for f in files_list if f['name'] != '.emptyFolderPlaceholder']

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

    col1, col2 = st.columns(2)

    with col1:
        submit_selection = st.button(
            "Get signed file URL", width='stretch')

    signed_url_res = None

    if submit_selection:
        signed_url_res = requests.get(
            "http://python-api:8000/supabase/storage/signed-url/pdf-files?",
            params={"path": str(pdf_path)}
        )

    with col2:
        st.link_button(
            "Preview file", signed_url_res.json().get("signedUrl") if signed_url_res is not None else "", width='stretch', disabled=(signed_url_res is None))

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
            base_entity_token_approximation = 0
            headers = headers_res.json()

            with st.container(height=450):
                for i, header in enumerate(headers):
                    is_selected = st.checkbox(
                        f"`{header.get('header')}` ({round(header.get('token_approximation'))})", key=f"base_entities_{i}")
                    base_entities_sections.append(
                        {"header": header.get('header'), "selected": is_selected})

                    if is_selected: base_entity_token_approximation += header.get(
                        'token_approximation')

            st.badge(
                f"~ {round(base_entity_token_approximation)} tokens", color="gray")

    with exam_subtopics_tab:
        if headers_res:
            exam_subtopics_token_approximation = 0
            headers = headers_res.json()

            with st.container(height=450):
                for i, header in enumerate(headers):
                    is_selected = st.checkbox(
                        f"`{header.get('header')}` ({round(header.get('token_approximation'))})", key=f"exam_subtopics_{i}")
                    exam_subtopics_sections.append(
                        {"header": header.get('header'), "selected": is_selected})
                    
                    if is_selected: exam_subtopics_token_approximation += header.get(
                        'token_approximation')
                    
            st.badge(f"~ {round(exam_subtopics_token_approximation)} tokens", color="gray")

    with job_roles_tab:
        if headers_res:
            job_roles_token_approximation = 0
            headers = headers_res.json()

            with st.container(height=450):
                for i, header in enumerate(headers):
                    is_selected = st.checkbox(
                        f"`{header.get('header')}` ({round(header.get('token_approximation'))})", key=f"job_roles_{i}")
                    job_roles_sections.append(
                        {"header": header.get('header'), "selected": is_selected})
                    
                    if is_selected: job_roles_token_approximation += header.get(
                        'token_approximation')
                    
            st.badge(f"~ {round(job_roles_token_approximation)} tokens", color="gray")

    with offices_tab:
        if headers_res:
            offices_token_approximation = 0
            headers = headers_res.json()

            with st.container(height=450):
                for i, header in enumerate(headers):
                    is_selected = st.checkbox(
                        f"`{header.get('header')}` ({round(header.get('token_approximation'))})", key=f"offices_{i}")
                    offices_sections.append(
                        {"header": header.get('header'), "selected": is_selected})
                    
                    if is_selected: offices_token_approximation += header.get(
                        'token_approximation')
                    
            st.badge(f"~ {round(offices_token_approximation)} tokens", color="gray")

    col1, col2 = st.columns([1,3])

    with col1:
        start_test_pipeline = st.button(
        "Start test pipeline", width="stretch", type="secondary")

    with col2: 
        start_pipeline = st.button(
            "Start pipeline", width="stretch", type="primary")


if start_pipeline:
    pipeline_trigger = requests.post("http://n8n:5678/webhook/754b5961-2b27-426b-822e-8c7d29c3c989",
                                     json={"file_path": md_path, "pdf_file_path": f"tenders/{pdf_path.stem}.pdf", "tender_url": tender_url, "base_entities_sections": base_entities_sections, "exam_subtopics_sections": exam_subtopics_sections, "job_roles_sections": job_roles_sections, "offices_sections": offices_sections})

    if pipeline_trigger.status_code == 200:
        st.session_state.offer_id = pipeline_trigger.json().get("id")
        st.switch_page("workflow_results.py")

        st.toast("Sucess - workflow started")
    else:
        st.toast("Failed to strat workflow")

if start_test_pipeline:
    pipeline_trigger = requests.post("http://n8n:5678/webhook-test/754b5961-2b27-426b-822e-8c7d29c3c989",
                                    json={"file_path": md_path, "pdf_file_path": f"tenders/{pdf_path.stem}.pdf", "tender_url": tender_url, "base_entities_sections": base_entities_sections, "exam_subtopics_sections": exam_subtopics_sections, "job_roles_sections": job_roles_sections, "offices_sections": offices_sections})

    if pipeline_trigger.status_code == 200:
        st.session_state.offer_id = pipeline_trigger.json().get("id")
        st.switch_page("workflow_results.py")

        st.toast("Sucess - workflow started")
    else:
        st.toast("Failed to strat workflow")
