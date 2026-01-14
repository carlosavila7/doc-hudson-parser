import streamlit as st
import requests

st.set_page_config(page_title="n8n Pipeline Trigger", page_icon="🚀")

st.title("n8n Workflow Trigger")
st.markdown("Enter the API endpoint or n8n Webhook address below to start the process.")

with st.form("api_trigger_form"):
    target_url = st.text_input(
        "Target Address", 
        placeholder="http://n8n:5678/webhook/your-id",
        help="Enter the full internal or external URL for the GET request."
    )
    
    submit_button = st.form_submit_button("Run Pipeline")

if submit_button:
    if target_url:
        try:
            with st.spinner(f"Sending GET request to {target_url}..."):
                response = requests.get(target_url, timeout=10)
                
                if response.status_code == 200:
                    st.success("Success! Pipeline triggered.")
                    st.json(response.json())
                else:
                    st.error(f"Error: Server returned status code {response.status_code}")
                    st.write(response.text)
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to connect: {e}")
    else:
        st.warning("Please enter a valid address before clicking submit.")