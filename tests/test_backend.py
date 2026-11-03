"""Offline regressions. All databases are temporary; SMTP is mocked."""
import asyncio
import os
from pathlib import Path
import ssl
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
TEMP = tempfile.TemporaryDirectory(prefix="raschet-backend-regression-")
os.environ["DB_PATH"] = str(Path(TEMP.name) / "data" / "test.db")
os.environ["ENV"] = "production"
os.environ["FEEDBACK_RETENTION_DAYS"] = "30"
import db
import feedback
from body_limit import BodyLimitMiddleware
from main import app
from httpx import ASGITransport, AsyncClient


class BodyLimitTests(unittest.TestCase):
    def run_request(self, chunks, headers=()):
        messages = [{"type": "http.request", "body": body,
                     "more_body": index < len(chunks) - 1}
                    for index, body in enumerate(chunks)]
        sent, calls = [], []
        async def receive():
            return messages.pop(0)
        async def send(message):
            sent.append(message)
        async def downstream(scope, receive, send):
            calls.append((await receive())["body"])
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"ok"})
        asyncio.run(BodyLimitMiddleware(downstream, max_body_bytes=8)(
            {"type": "http", "headers": list(headers)}, receive, send))
        return sent[0]["status"], calls

    def test_chunked_without_length_rejected_before_endpoint(self):
        status, calls = self.run_request([b"12345", b"6789"])
        self.assertEqual((status, calls), (413, []))

    def test_false_small_length_does_not_bypass_limit(self):
        self.assertEqual(self.run_request([b"123456789"], [(b"content-length", b"1")])[0], 413)

    def test_exact_limit_replayed(self):
        self.assertEqual(self.run_request([b"123", b"45678"]), (200, [b"12345678"]))

    def test_invalid_and_conflicting_length(self):
        for raw in (b"-1", b"x", b"+1", b"1,1"):
            self.assertEqual(self.run_request([b""], [(b"content-length", raw)])[0], 400)
        self.assertEqual(self.run_request([b""], [(b"content-length", b"1"), (b"content-length", b"2")])[0], 400)


class SMTPTests(unittest.TestCase):
    def test_both_tls_modes_verify_peer(self):
        item = feedback.FeedbackIn(topic="offline test", message="fake test message")
        for port in (465, 587):
            fake = MagicMock()
            with (
                patch.dict(os.environ, {"SMTP_HOST": "smtp.example.invalid", "SMTP_PORT": str(port),
                                        "SMTP_USER": "test", "SMTP_PASSWORD": "test-only", "FEEDBACK_TO": "test@example.invalid"}),
                patch.object(feedback.smtplib, "SMTP_SSL", return_value=fake) as implicit,
                patch.object(feedback.smtplib, "SMTP", return_value=fake) as explicit,
            ):
                feedback._send_mail(item)
                context = (implicit.call_args.kwargs["context"] if port == 465 else
                           fake.__enter__.return_value.starttls.call_args.kwargs["context"])
                self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
                self.assertTrue(context.check_hostname)
                fake.__enter__.return_value.send_message.assert_called_once()
                (explicit if port == 465 else implicit).assert_not_called()

    def test_tls_error_does_not_fall_back_to_cleartext(self):
        item = feedback.FeedbackIn(topic="offline test", message="fake message")
        fake = MagicMock()
        fake.__enter__.return_value.starttls.side_effect = ssl.SSLCertVerificationError("test invalid cert")
        with (
            patch.dict(os.environ, {"SMTP_HOST": "smtp.example.invalid", "SMTP_PORT": "587",
                                    "SMTP_USER": "test", "FEEDBACK_TO": "test@example.invalid"}),
            patch.object(feedback.smtplib, "SMTP", return_value=fake),
        ):
            with self.assertRaises(ssl.SSLCertVerificationError):
                feedback._send_mail(item)
            fake.__enter__.return_value.login.assert_not_called()
            fake.__enter__.return_value.send_message.assert_not_called()


class DatabaseTests(unittest.TestCase):
    def test_retention_only_deletes_expired_contact_rows(self):
        db.init_db()
        now = 100 * 86400
        conn = db.connect()
        try:
            conn.execute("DELETE FROM feedback")
            conn.executemany("INSERT INTO feedback (created_at, topic, message) VALUES (?, ?, ?)",
                             [(now - 31 * 86400, "old", "fake"), (now - 30 * 86400, "edge", "fake"), (now, "new", "fake")])
            self.assertEqual(db.purge_expired_feedback(conn, now=now), 1)
            self.assertEqual([r[0] for r in conn.execute("SELECT topic FROM feedback ORDER BY created_at")], ["edge", "new"])
            conn.commit()
        finally:
            conn.close()

    def test_invalid_retention_fails_closed(self):
        db.init_db()
        conn = db.connect()
        try:
            with patch.dict(os.environ, {"FEEDBACK_RETENTION_DAYS": "0"}):
                with self.assertRaises(ValueError):
                    db.purge_expired_feedback(conn)
        finally:
            conn.close()


class ApplicationTests(unittest.TestCase):
    def test_health_and_headers(self):
        async def run():
            # ASGITransport intentionally has no lifespan side effects.
            async with app.router.lifespan_context(app):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.get("/api/health")
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.headers["x-frame-options"], "DENY")
                    self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        asyncio.run(run())

    def test_chunked_app_body_keeps_cors_and_security_headers(self):
        async def chunks():
            yield b"x" * 20000
            yield b"y" * 20000
        async def run():
            async with app.router.lifespan_context(app):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post("/api/event", content=chunks(),
                        headers={"Origin": "https://raschet.net", "Content-Type": "application/json"})
                    self.assertEqual(response.status_code, 413)
                    self.assertEqual(response.headers["access-control-allow-origin"], "https://raschet.net")
                    self.assertEqual(response.headers["x-frame-options"], "DENY")
        asyncio.run(run())


if __name__ == "__main__":
    try:
        unittest.main()
    finally:
        TEMP.cleanup()
