from enum import IntEnum


class HTTPStatus(IntEnum):
    """HTTP status codes."""

    # 2xx Success
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204

    # 3xx Redirection
    NOT_MODIFIED = 304

    # 4xx Client Errors
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    UNSUPPORTED_MEDIA = 415
    UNPROCESSABLE = 422
    TOO_MANY_REQUESTS = 429

    # 5xx Server Errors
    SERVER_ERROR = 500

    @property
    def label(self) -> str:
        """Human-readable label."""
        return self.name.replace("_", " ").title()

    @property
    def message(self) -> str:
        """Standard message for this code."""
        messages = {
            200: "Success",
            201: "Created",
            204: "No content",
            400: "Bad request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not found",
            422: "Validation failed",
            429: "Rate limit exceeded",
            500: "Server error",
        }
        return messages.get(self.value, "Unknown")
