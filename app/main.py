from fastapi import FastAPI

app = FastAPI(
    title="Personal AI API",
    version="0.1.0",
)

@app.get("/")
def root():
    return {
        "message": "Personal AI API is running"
    }

@app.get("/health")
def health():
    return {
        "status": "ok"
    }



