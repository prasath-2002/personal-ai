"""Offline regression suite. Uses isolated databases and deterministic embeddings."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ["LLM_PROVIDER"] = "mock"
os.environ["OPENAI_API_KEY"] = ""
os.environ["GROQ_API_KEY"] = ""

from fastapi.testclient import TestClient
from app.main import app
from app.services import database_service as db, file_service, llm_service
from app.services.file_service import chunk_text


class APITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temp.cleanup)
        directory = Path(self.temp.name)
        for target, value in [
            ("app.services.database_service.DB_PATH", directory / "test.db"),
            ("app.services.file_service.UPLOAD_DIR", directory / "uploads"),
            ("app.services.embedding_service.generate_embedding", lambda text: [1.0, 0.0] if "apple" in text.lower() else [0.0, 1.0]),
        ]:
            patcher = patch(target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.client = TestClient(app)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def chat(self, message="hello", session="chat-1", stream=False):
        return self.client.post("/chat/stream" if stream else "/chat", json={"session_id": session, "message": message})

    def upload(self, content=b"apple document", session="chat-1", name="notes.txt"):
        return self.client.post("/files/upload", data={"session_id": session}, files={"file": (name, content)})

    def test_chat_persistence_and_session_lifecycle(self):
        self.assertEqual(self.chat().status_code, 200)
        self.assertEqual(len(self.client.get("/history/chat-1").json()["messages"]), 2)
        self.assertEqual(self.client.get("/history/other").json()["messages"], [])
        self.assertEqual(self.client.patch("/sessions/chat-1", json={"title": "Renamed"}).status_code, 200)
        self.assertEqual(self.client.get("/sessions").json()["sessions"][0]["title"], "Renamed")
        self.client.post("/reset", params={"session_id": "chat-1"})
        self.assertEqual(db.get_messages("chat-1"), [])
        self.client.delete("/sessions/chat-1")
        self.assertEqual(db.get_sessions(), [])

    def test_sse_unicode_and_done(self):
        response = self.chat("வணக்கம்", stream=True)
        events = [json.loads(frame[6:]) for frame in response.text.strip().split("\n\n")]
        self.assertEqual(events[-1]["type"], "done")
        text = "".join(event.get("content", "") for event in events)
        self.assertIn("வணக்கம்", text)
        self.assertEqual(db.get_messages("chat-1")[-1]["content"], text)

    def test_upload_retrieval_isolation_cleanup_and_delete(self):
        uploaded = self.upload()
        self.assertEqual(uploaded.status_code, 200, uploaded.text)
        document_id = uploaded.json()["document_id"]
        self.assertEqual(len(db.get_sessions()), 1)
        self.assertEqual(list(file_service.UPLOAD_DIR.iterdir()), [])
        self.assertEqual(self.upload().status_code, 409)
        self.assertEqual(db.search_document_chunks("other", "apple"), [])
        self.assertEqual(db.search_document_chunks("chat-1", "apple")[0]["filename"], "notes.txt")
        self.assertIn("apple document", llm_service.build_document_context("chat-1", "apple"))
        self.assertEqual(self.client.delete(f"/documents/{document_id}").status_code, 200)
        self.assertEqual(db.search_document_chunks("chat-1", "apple"), [])
        self.assertEqual(self.client.delete(f"/documents/{document_id}").status_code, 404)

    def test_session_delete_removes_documents_and_chunks(self):
        self.upload()
        self.chat()
        self.client.delete("/sessions/chat-1")
        self.assertEqual(db.get_documents("chat-1"), [])
        self.assertEqual(db.get_messages("chat-1"), [])
        self.assertEqual(db.search_document_chunks("chat-1", "apple"), [])

    def test_invalid_inputs(self):
        for message in ["", "   ", "x" * 20001]:
            self.assertEqual(self.chat(message).status_code, 422)
        self.assertEqual(self.chat(session="../escape").status_code, 422)
        self.assertEqual(self.upload(session="../escape").status_code, 422)
        self.assertEqual(self.upload(b"").status_code, 400)
        self.assertEqual(self.upload(name="script.exe").status_code, 400)
        self.assertEqual(self.upload(b"not a PDF", name="bad.pdf").status_code, 400)
        self.assertEqual(self.upload(b"\xff", name="bad.txt").status_code, 400)
        self.assertEqual(self.client.patch("/sessions/missing", json={"title": "title"}).status_code, 404)
        self.assertEqual(self.client.patch("/sessions/missing", json={"title": " "}).status_code, 422)

    def test_size_limit_and_failed_processing_cleanup(self):
        with patch("app.main.MAX_UPLOAD_BYTES", 5):
            self.assertEqual(self.upload().status_code, 413)
        with self.assertLogs("app.main", level="ERROR"), patch("app.services.embedding_service.generate_embedding", side_effect=RuntimeError("offline")):
            self.assertEqual(self.upload().status_code, 503)
        self.assertEqual(db.get_documents("chat-1"), [])
        self.assertEqual(list(file_service.UPLOAD_DIR.iterdir()), [])

    def test_provider_failure_and_retry_do_not_duplicate_history(self):
        self.assertFalse(llm_service.is_configured("YOUR_GROQ_API_KEY"))
        self.assertFalse(llm_service.is_configured("YOUR_GROQ_MODEL"))
        with patch.object(llm_service, "LLM_PROVIDER", "groq"), patch.object(llm_service, "groq_client", None):
            self.assertEqual(self.chat().status_code, 503)
        self.assertEqual(db.get_messages("chat-1"), [])
        self.assertEqual(self.chat().status_code, 200)
        self.assertEqual(len(db.get_messages("chat-1")), 2)

    def test_stream_error_event(self):
        def fail(*args):
            yield "partial"
            raise llm_service.ProviderError("Please retry")
        with patch("app.main.generate_streaming_response", fail):
            response = self.chat(stream=True)
        self.assertIn('"type": "error"', response.text)
        self.assertNotIn('"type":"done"', response.text)
        self.assertEqual(db.get_messages("chat-1"), [])

    def test_health_config_and_chunk_parameters(self):
        self.assertEqual(self.client.get("/health").json()["database"], "ok")
        self.assertTrue(self.client.get("/config").json()["configured"])
        self.assertEqual(chunk_text("abcdef", 4, 1), ["abcd", "def"])
        with self.assertRaises(ValueError):
            chunk_text("abc", 2, 2)


if __name__ == "__main__":
    unittest.main()
