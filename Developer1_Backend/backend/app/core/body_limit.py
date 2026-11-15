import json
from starlette.responses import JSONResponse

class BodyLimitMiddleware:
    def __init__(self, app, max_bytes=15_000_000):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if (
            scope["type"] != "http"
            or scope["method"] not in {"POST", "PUT", "PATCH", "DELETE"}
        ):
            return await self.app(scope, receive, send)

        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > self.max_bytes:
                response = JSONResponse(
                    status_code=413,
                    content={
                        "error": {
                            "code": "request_too_large",
                            "message": "Request exceeds the backend limit",
                            "details": None,
                        },
                        "request_id": scope.get("state", {}).get(
                            "request_id", ""
                        ),
                    },
                )
                return await response(scope, receive, send)
            if not message.get("more_body", False):
                break

        content_type = dict(scope.get("headers", [])).get(
            b"content-type", b""
        ).split(b";", 1)[0]

        if content_type == b"application/json":
            def reject_nonfinite(value):
                raise ValueError("Nonfinite JSON numbers are invalid")
            try:
                json.loads(body, parse_constant=reject_nonfinite)
            except json.JSONDecodeError:
                pass
            except (ValueError, RecursionError):
                response = JSONResponse(
                    status_code=422,
                    content={
                        "error": {
                            "code": "invalid_json",
                            "message": (
                                "JSON requires finite numbers "
                                "and bounded nesting"
                            ),
                            "details": None,
                        },
                        "request_id": scope.get("state", {}).get(
                            "request_id", ""
                        ),
                    },
                )
                return await response(scope, receive, send)

        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {
                    "type": "http.request",
                    "body": bytes(body),
                    "more_body": False,
                }
            return await receive()

        return await self.app(scope, replay, send)
