from fastapi import FastAPI
from . import dependencies

app = FastAPI(
    title="Modern File Processing API",
    description="API for processing files, interacting with Supabase, and calling LLMs.",
    version="0.0.1",

)
@app.get("/")
def read_root():
    """
    A simple root endpoint to confirm the API is running.
    """
    return {"message": "Welcome to the File Processing API!"}
