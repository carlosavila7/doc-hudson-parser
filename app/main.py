from fastapi import FastAPI
from .supabase.supabase_router import router as supabase_router
from .document_processing.document_processing_router import router as document_processing_router

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


app.include_router(supabase_router)
app.include_router(document_processing_router)
