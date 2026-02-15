import streamlit as st
import requests
import time

from pathlib import Path

st.title("Document Management Dashboard")

st.set_page_config(layout="wide", page_icon=":material/document_search:", page_title="Document processing",)

# --- Expander 1: Upload to Supabase ---
with st.expander("Upload New PDF Document"):
    with st.form("upload_form", clear_on_submit=True):
        file_path = st.text_input(
            "File Path (Folder Name)", placeholder="e.g., orgao_YYYY.pdf")
        file_type = st.selectbox(
            "Document Type", ["tender", "exam", "answer_sheet"])
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

        submit_upload = st.form_submit_button(
            "Upload to Supabase", width="stretch", type="primary")

        if submit_upload:
            if uploaded_file and file_path:
                full_path = f"{file_type}s/{file_path}".replace(
                    "//", "/")

                try:
                    bytes_data = uploaded_file.getvalue()
                    files = {'file': (uploaded_file.name,
                                      bytes_data, 'application/pdf')}
                    with st.spinner("Uploading file...", show_time=True):
                        res = requests.post(
                            "http://python-api:8000/supabase/storage/upload-file/pdf-files", params={"path": full_path}, files=files)

                        if res.status_code == 200:
                            st.success(
                                f"Successfully uploaded to: {full_path}")
                        else:
                            st.error(f"Error while uploading file to Supabase")
                except Exception as e:
                    st.error(f"Upload failed: {e}")
            else:
                st.warning("Please provide a file path and a PDF file.")

# --- Expander 2: Select and Process ---
with st.expander("Convert PDF to markdown"):
    selected_category = st.selectbox(
        "Filter by Category", ["tender", "exam", "answer_sheet"])

    try:
        response = requests.get(
            "http://python-api:8000/supabase/storage/pdf-files", params={"path": f"{selected_category}s"})
        files_list = response.json()
        file_names = [f['name']
                      for f in files_list if f['name'] != '.emptyFolderPlaceholder']
    except:
        file_names = []

    # with st.form("selection_form"):
    target_file = st.selectbox(
        "Select File", options=file_names if file_names else ["No files found"], index=None)

    md_path = None
    if target_file:
        target_file_path = Path(target_file)

        md_file_res = requests.get(
            "http://python-api:8000/supabase/storage/processed-files", params={"path": f'{selected_category}_{target_file_path.stem}/'})

        if md_file_res.status_code == 200:
            files_list = md_file_res.json()
            options = [f
                       for f in files_list if f['name'] != '.emptyFolderPlaceholder']

            md_path = options[0].get("name") if len(options) > 0 else None

            if md_path is not None:
                st.warning(f"Markdown file (`{md_path}`) already existent")

    col1, col2 = st.columns(2)

    with col1:
        submit_selection = st.button(
            "Get signed file URL", width='stretch', disabled=(target_file is None))

    signed_url_res = None
    if submit_selection:
        if target_file:
            signed_url_res = requests.get(
                "http://python-api:8000/supabase/storage/signed-url/pdf-files?",
                params={"path": f"{selected_category}s/{target_file}"}
            )

            # if signed_url_res.status_code == 200:

            # Add your processing logic here
        else:
            st.error("No valid file selected.")
    with col2:
        st.link_button(
            "Preview file", signed_url_res.json().get("signedUrl") if signed_url_res is not None else "", width='stretch', disabled=(signed_url_res is None))

    st.text("Select the PDF page interval to be converted:")

    start_col, end_col = st.columns(2)

    with start_col:
        start_page = st.number_input(
            "Start page (optional)", step=1, value=None, placeholder="Enter the interval start")
    with end_col:
        end_page = st.number_input(
            "End page (optional)", step=1, value=None, placeholder="Enter the interval end")

    interval_is_valid = end_page is None if start_page is None else end_page is not None

    submit_convert_file = st.button(
        "Convert file to markdown", type="primary", width="stretch", disabled=(target_file is None or not interval_is_valid or md_path is not None))

    if submit_convert_file:
        if interval_is_valid:
            with st.spinner(text="Convertendo arquivo para markdown", show_time=False, width="content"):
                convert_file_res = requests.post(
                    "http://python-api:8000/document-processing/process-pdf", params={"file_path": f"{selected_category}s/{target_file}", "start_page": start_page, "end_page": end_page})

            json_res = convert_file_res.json()

            if json_res.get("status") == "success":
                st.success("Arquivo convertido com sucesso!")

            st.json(json_res)

            md_path = json_res.get("markdown_path")
        else:
            st.error("Page interval is not valid")

with st.expander("Preview converted markdown file"):
    rendered_tab, raw_tab = st.tabs(["Rendered", "Raw"])

    if md_path:
        md_path = Path(md_path)

        full_path = Path(md_path.stem) / \
            md_path if len(md_path.parts) == 1 else md_path

        md_signed_url = requests.get(
            "http://python-api:8000/supabase/storage/signed-url/processed-files?",
            params={"path": full_path}
        )

        if md_signed_url.status_code == 200:
            signed_url = md_signed_url.json().get("signedUrl")

            res = requests.get(signed_url)

            if res.status_code == 200:
                res.encoding = 'utf-8'
                content = res.text

                with raw_tab:
                    with st.container(height=800, border=True):
                        st.code(content)
                with rendered_tab:
                    with st.container(height=800, border=True):
                        st.markdown(content)
        # res = requests.get(md_file_res)
