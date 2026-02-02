from pathlib import Path

import streamlit as st
import requests


pg = st.navigation(
    ["workflow_results.py", "workflow_trigger.py", "document_processing.py"])
pg.run()
