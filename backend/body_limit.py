"""Bounded ASGI request-body reader, including requests without Content-Length."""
import json


class BodyLimitMiddleware:
    """Reject oversized requests before JSON parsing or endpoint side effects.

    The body is buffered only up to max_body_bytes. A trusted reverse proxy must
    additionally enforce read timeouts and a transport-level body limit.
    """

    def __init__(self, app, max_body_bytes=32 * 1024):
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def reject(status, detail):
            body = json.dumps({"detail": detail}).encode("utf-8")
            await send({"type": "http.response.start", "status": status,
                        "headers": [(b"content-type", b"application/json"),
                                    (b"content-length", str(len(body)).encode("ascii"))]})
            await send({"type": "http.response.body", "body": body})

        lengths = [value for name, value in scope.get("headers", [])
                   if name.lower() == b"content-length"]
        if lengths:
            try:
                # Duplicated, signed or conflicting lengths are rejected, not
                # trusted as proof that the actual streamed body is small.
                if len(lengths) != 1 or not lengths[0].isdigit():
                    raise ValueError
                length = int(lengths[0])
            except ValueError:
                return await reject(400, "bad content-length")
            if length > self.max_body_bytes:
                return await reject(413, "payload too large")

        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            if message["type"] != "http.request":
                continue
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > self.max_body_bytes:
                return await reject(413, "payload too large")
            body.extend(chunk)
            if not message.get("more_body", False):
                break

        replayed = False

        async def replay():
            nonlocal replayed
            if not replayed:
                replayed = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)
