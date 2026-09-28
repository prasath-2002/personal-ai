from fastapi import FastAPI
from app.schemas import ChatRequest, ChatResponse
from app.services.llm_service import generate_response
from app.services.llm_service import generate_response, reset_conversation
from app.services.database_service import initialize_database



app = FastAPI(
    title="Personal AI API",
    version="0.1.0",
)

initialize_database()

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
    ai_response = generate_response(
        request.session_id,
        request.message
    )

    return ChatResponse(
    session_id=request.session_id,
    user_message=request.message,
    ai_response=ai_response
)

@app.post("/reset")
def reset(session_id: str):
    reset_conversation(session_id)

    return {
        "message": f"Conversation '{session_id}' cleared"
    }