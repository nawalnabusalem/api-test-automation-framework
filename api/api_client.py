from types import TracebackType
from typing import Any, Self

import requests
from requests.exceptions import ConnectionError, RequestException, Timeout

from logger.html_report_logger import HTMLReportLogger


class APIClient:
    """Send HTTP requests and capture their diagnostics in the HTML report."""

    def __init__(
        self,
        logger: HTMLReportLogger,
        base_url: str,
        timeout: float = 10,
    ) -> None:
        """Initialize a reusable HTTP session for one test case."""
        self.session = requests.Session()
        self.logger = logger
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers: dict[str, str] = {}

    def set_headers(self, headers: dict[str, str]) -> None:
        """Merge default headers into subsequent requests."""
        self.headers.update(headers)

    def set_auth_token(self, token: str, token_type: str = "Bearer") -> None:
        """Set the default Authorization header for subsequent requests."""
        self.headers["Authorization"] = f"{token_type} {token}"

    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def request(self, method: str, endpoint: str, **kwargs: Any) -> requests.Response:
        """Send an HTTP request and log its sanitized request/response data."""
        url = self._build_url(endpoint)

        # Reporting controls belong to the logger and must not be forwarded to requests.
        show_headers = kwargs.pop("show_headers", True)
        show_body = kwargs.pop("show_body", True)

        # Merge headers
        headers = self.headers.copy()
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))

        # Prepare request for logging
        request = requests.Request(method, url, headers=headers, **kwargs)
        prepared_request = request.prepare()

        # Log request - pass the prepared_request request object
        self.logger.log_request(
            method=prepared_request.method,
            url=prepared_request.url,
            headers=prepared_request.headers,
            body=prepared_request.body,
            show_headers=show_headers,
            show_body=show_body,
        )

        try:
            response = self.session.send(prepared_request, timeout=self.timeout)

            self.logger.log_response(
                status_code=response.status_code,
                reason=response.reason,
                headers=response.headers,
                body=response.text,
                elapsed_ms=response.elapsed.total_seconds() * 1000,
                show_headers=show_headers,
                show_body=show_body,
            )

            return response

        except Timeout as error:
            self.logger.error(
                "Request timed out after %s seconds: %s %s - %s",
                self.timeout,
                method,
                url,
                error,
            )
            raise

        except ConnectionError as error:
            self.logger.error("Connection failed: %s %s - %s", method, url, error)
            raise

        except RequestException as error:
            self.logger.error("HTTP request failed: %s %s - %s", method, url, error)
            raise

    def get(self, endpoint: str, **kwargs: Any) -> requests.Response:
        """Send a GET request."""
        return self.request("GET", endpoint, **kwargs)

    def post(
        self, endpoint: str, payload: dict[str, Any] | None = None, **kwargs: Any
    ) -> requests.Response:
        """Send a POST request with an optional JSON payload."""
        return self.request("POST", endpoint, json=payload, **kwargs)

    def put(
        self, endpoint: str, payload: dict[str, Any] | None = None, **kwargs: Any
    ) -> requests.Response:
        """Send a PUT request with an optional JSON payload."""
        return self.request("PUT", endpoint, json=payload, **kwargs)

    def patch(
        self, endpoint: str, payload: dict[str, Any] | None = None, **kwargs: Any
    ) -> requests.Response:
        """Send a PATCH request with an optional JSON payload."""
        return self.request("PATCH", endpoint, json=payload, **kwargs)

    def delete(self, endpoint: str, **kwargs: Any) -> requests.Response:
        """Send a DELETE request."""
        return self.request("DELETE", endpoint, **kwargs)

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self.session.close()

    def __enter__(self) -> Self:
        """Return this client when used as a context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Close the HTTP session when leaving a context manager."""
        self.close()
