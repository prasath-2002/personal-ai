from fastapi import FastAPI
from app.schemas import ChatRequest, ChatResponse
from app.services.llm_service import generate_response


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

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    ai_response = generate_response(request.message)

    return ChatResponse(
        user_message=request.message,
        ai_response=ai_response
    )