import hashlib
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.core.config import CORS_ORIGINS, LLM_PROVIDER, MAX_UPLOAD_BYTES
from app.schemas import ChatHistoryResponse, ChatRequest, ChatResponse, SessionId, SessionListResponse, SessionRenameRequest
from app.services import database_service as db
from app.services.file_service import chunk_text, extract_text_from_file, save_uploaded_file
from app.services.llm_service import ProviderError, generate_response, generate_streaming_response, validate_provider

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.initialize_database()
    yield


app = FastAPI(title="Personal AI API", version="1.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS,
                   allow_credentials=False, allow_methods=["*"], allow_headers=["*"])


@app.get("/")
def root():
    return {"message": "Personal AI API is running"}


@app.get("/health")
def health():
    connection = db.get_connection()
    try:
        connection.execute("SELECT 1")
    finally:
        connection.close()
    return {"status": "ok", "database": "ok"}


@app.get("/config")
def get_config():
    try:
        validate_provider()
        configured = True
    except ProviderError:
        configured = False
    return {"llm_provider": LLM_PROVIDER, "configured": configured,
            "max_upload_bytes": MAX_UPLOAD_BYTES}


def check_provider():
    try:
        validate_provider()
    except ProviderError as error:
        raise HTTPException(503, str(error)) from error


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    check_provider()
    db.create_session(request.session_id, request.message[:50])
    try:
        response = generate_response(request.session_id, request.message)
    except ProviderError as error:
        raise HTTPException(502, str(error)) from error
    return ChatResponse(session_id=request.session_id, user_message=request.message, ai_response=response)


@app.post("/chat/stream")
def chat_stream(request: ChatRequest):
    check_provider()
    db.create_session(request.session_id, request.message[:50])

    def events():
        try:
            for delta in generate_streaming_response(request.session_id, request.message):
                yield f"data: {json.dumps({'type': 'delta', 'content': delta})}\n\n"
            yield 'data: {"type":"done"}\n\n'
        except ProviderError as error:
            yield f"data: {json.dumps({'type': 'error', 'message': str(error)})}\n\n"
        except Exception:
            logger.exception("Chat stream failed")
            yield 'data: {"type":"error","message":"Unable to complete the response. Please retry."}\n\n'

    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/reset")
def reset(session_id: SessionId):
    db.clear_messages(session_id)
    return {"message": "Conversation cleared"}


@app.get("/history/{session_id}", response_model=ChatHistoryResponse)
def get_history(session_id: SessionId):
    return ChatHistoryResponse(session_id=session_id, messages=db.get_messages(session_id))


@app.get("/sessions", response_model=SessionListResponse)
def list_sessions():
    return SessionListResponse(sessions=db.get_sessions())


@app.patch("/sessions/{session_id}")
def update_session_title(session_id: SessionId, request: SessionRenameRequest):
    if not any(s["session_id"] == session_id for s in db.get_sessions()):
        raise HTTPException(404, "Session not found")
    db.rename_session(session_id, request.title)
    return {"message": "Session renamed", "title": request.title}


@app.delete("/sessions/{session_id}")
def remove_session(session_id: SessionId):
    db.delete_session(session_id)
    return {"message": "Session deleted", "session_id": session_id}


@app.get("/documents/{session_id}")
def list_documents(session_id: SessionId):
    return {"session_id": session_id, "documents": db.get_documents(session_id)}


@app.delete("/documents/{document_id}")
def remove_document(document_id: int):
    session_id = db.delete_document(document_id)
    if session_id is None:
        raise HTTPException(404, "Document not found")
    return {"message": "Document deleted", "session_id": session_id}


def process_upload(session_id: str, filename: str, content: bytes):
    file_hash = hashlib.sha256(content).hexdigest()
    if db.document_hash_exists(session_id, file_hash):
        raise HTTPException(409, "This file is already attached to this chat")
    file_path = save_uploaded_file(session_id, filename, content)
    document_id = None
    try:
        text = extract_text_from_file(file_path)
        if not text.strip():
            raise HTTPException(400, "No readable text found. Scanned PDFs need OCR before upload.")
        chunks = chunk_text(text)
        if len(chunks) > 2000:
            raise HTTPException(413, "Document contains too much text. Split it into smaller files.")
        document_id = db.create_document(session_id, filename, file_hash)
        db.save_document_chunks(document_id, session_id, chunks)
        db.create_session(session_id, filename[:50])
        return {"session_id": session_id, "document_id": document_id, "filename": filename,
                "characters": len(text), "chunks": len(chunks), "preview": text[:300]}
    except HTTPException:
        if document_id is not None:
            db.delete_document(document_id)
        raise
    except ValueError as error:
        if document_id is not None:
            db.delete_document(document_id)
        raise HTTPException(400, str(error)) from error
    except Exception as error:
        if document_id is not None:
            db.delete_document(document_id)
        logger.exception("Document processing failed")
        raise HTTPException(503, "Document processing failed. Check the local embedding model and retry.") from error
    finally:
        # Extracted text and embeddings live in SQLite; do not retain duplicate originals.
        file_path.unlink(missing_ok=True)


@app.post("/files/upload")
async def upload_file(session_id: str = Form(..., pattern=r"^[A-Za-z0-9_-]{1,100}$"), file: UploadFile = File(...)):
    try:
        filename = (file.filename or "uploaded-file").replace("\\", "/").split("/")[-1]
        if len(filename) > 255 or Path(filename).suffix.lower() not in {".pdf", ".txt"}:
            raise HTTPException(400, "Only PDF and TXT filenames up to 255 characters are supported")
        content = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, f"File exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB upload limit")
        if not content:
            raise HTTPException(400, "Uploaded file is empty")
        return await run_in_threadpool(process_upload, session_id, filename, content)
    finally:
        await file.close()


@app.get("/debug/rag/{session_id}")
def debug_rag(session_id: SessionId, query: str):
    return {"session_id": session_id, "query": query,
            "results": db.search_document_chunks(session_id, query, limit=5)}
