from __future__ import annotations

import json
import math
import platform
import re
from collections.abc import Mapping
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

STATUS_PASSED = "passed"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"
STATUS_ERROR = "error"
ALLOWED_STATUSES = frozenset(
    {STATUS_PASSED, STATUS_FAILED, STATUS_SKIPPED, STATUS_ERROR}
)
STATUS_SUMMARY_ORDER = (STATUS_PASSED, STATUS_FAILED, STATUS_SKIPPED, STATUS_ERROR)

SENSITIVE_HEADERS = frozenset(
    {
        "authorization",
        "proxy-authorization",
        "cookie",
        "set-cookie",
        "api-key",
        "x-api-key",
        "token",
    }
)
SENSITIVE_BODY_FIELDS = frozenset(
    {
        "access_token",
        "accesstoken",
        "refresh_token",
        "refreshtoken",
        "username",
        "password",
        "secret",
        "client_secret",
    }
)
SENSITIVE_KEYS = SENSITIVE_HEADERS | SENSITIVE_BODY_FIELDS

MAIN_REPORT_FILENAME = "main_report.html"
DEFAULT_REPORT_FILENAME = "test_case_report.html"
REPORT_TEMPLATE_FILENAME = "test_case_report.html"
REPORT_SCRIPT_FILENAME = "report_script.js"
REPORT_RUNS_DIRECTORY = "runs"
REPORT_DATA_PLACEHOLDER = "__REPORT_DATA__"
REPORT_SCRIPT_PLACEHOLDER = "__REPORT_SCRIPT__"
PAGE_CLASS_PLACEHOLDER = "__PAGE_CLASS__"

LOGGER_DIRECTORY = Path(__file__).resolve().parent
DEFAULT_REPORT_ROOT = Path("reports")
DEFAULT_OUTPUT_PATH = DEFAULT_REPORT_ROOT / DEFAULT_REPORT_FILENAME
DEFAULT_TEMPLATE_DIRECTORY = LOGGER_DIRECTORY / "templates"
DEFAULT_TEMPLATE_PATH = DEFAULT_TEMPLATE_DIRECTORY / REPORT_TEMPLATE_FILENAME


class HTMLReportLogger:
    """Collect API test data and render it into a standalone HTML report."""

    SENSITIVE_HEADERS = SENSITIVE_HEADERS
    SENSITIVE_KEYS = SENSITIVE_KEYS

    def __init__(
        self,
        output_path: str | Path = DEFAULT_OUTPUT_PATH,
        template_path: str | Path | None = None,
        title: str = "API Test Report",
        environment: str = "local",
        run_info: Mapping[str, Any] | None = None,
    ) -> None:
        """Initialize an in-memory test collector and its output configuration."""
        self.output_path = Path(output_path)
        self.template_path = (
            Path(template_path) if template_path else DEFAULT_TEMPLATE_PATH
        )
        self.title = title
        self.environment = environment
        self.run_info = {
            "base_url": "",
            "branch": "",
            "commit": "",
            "python": platform.python_version(),
            "framework": "pytest",
            "started_at": datetime.now(UTC).astimezone().isoformat(timespec="seconds"),
            **dict(run_info or {}),
        }
        self.tests: list[dict[str, Any]] = []
        self._active: dict[str, Any] | None = None
        self._run_started = perf_counter()

    def start_test(
        self,
        name: str,
        suite: str = "",
        description: str = "",
        file: str = "",
        tags: list[str] | tuple[str, ...] | None = None,
        order: int | None = None,
    ) -> None:
        """Start collecting report data for one test case."""
        if self._active is not None:
            raise RuntimeError("End the active test before starting another test")

        self._active = {
            "name": name,
            "suite": suite,
            "status": STATUS_ERROR,
            "duration_ms": 0,
            "request": None,
            "response": None,
            "error": None,
            "logs": [],
            "info": {
                "description": description,
                "file": file,
                "tags": list(tags or []),
            },
            "_order": order,
            "_started": perf_counter(),
        }

    def set_test_info(
        self,
        description: str | None = None,
        file: str | None = None,
        tags: list[str] | tuple[str, ...] | None = None,
    ) -> None:
        """Update information displayed on the individual test report."""
        info = self._require_active()["info"]

        if description is not None:
            info["description"] = description

        if file is not None:
            info["file"] = file

        if tags is not None:
            info["tags"] = list(tags)

    def log_request(
        self,
        method: str,
        url: str,
        headers: Mapping[str, Any] | None = None,
        body: Any = None,
        show_headers: bool = True,
        show_body: bool = True,
    ) -> None:
        """Record the API request associated with the active test case."""
        test = self._require_active()
        test["request"] = {
            "method": method.upper(),
            "url": url,
            "headers": self._redact(dict(headers or {})) if show_headers else {},
            "body": self._normalise(body) if show_body else None,
        }

    def log_response(
        self,
        status_code: int,
        headers: Mapping[str, Any] | None = None,
        body: Any = None,
        elapsed_ms: float | None = None,
        reason: str = "",
        show_headers: bool = True,
        show_body: bool = True,
    ) -> None:
        """Record the API response associated with the active test case."""
        test = self._require_active()
        test["response"] = {
            "status_code": status_code,
            "reason": reason,
            "headers": self._redact(dict(headers or {})) if show_headers else {},
            "body": self._normalise(body) if show_body else None,
            "elapsed_ms": round(elapsed_ms, 2) if elapsed_ms is not None else None,
        }

    def log(self, message: Any, level: str = "INFO") -> None:
        """Append a message to the active test case at the requested level."""
        test = self._require_active()
        test["logs"].append(
            {
                "timestamp": datetime.now(UTC).astimezone().strftime("%H:%M:%S"),
                "level": level.upper(),
                "message": str(message),
            }
        )

    def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log a DEBUG message using standard percent-style argument formatting."""
        self.log(self._format_log_message(msg, args), "DEBUG")

    def info(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log an INFO message using standard percent-style argument formatting."""
        self.log(self._format_log_message(msg, args), "INFO")

    def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log a WARNING message using standard percent-style argument formatting."""
        self.log(self._format_log_message(msg, args), "WARNING")

    def error(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log an ERROR message using standard percent-style argument formatting."""
        self.log(self._format_log_message(msg, args), "ERROR")

    def critical(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log a CRITICAL message using standard percent-style formatting."""
        self.log(self._format_log_message(msg, args), "CRITICAL")

    def end_test(self, status: str, error: BaseException | str | None = None) -> None:
        """Finish the active test and store its final status and optional error."""
        test = self._require_active()
        status = status.lower()

        if status not in ALLOWED_STATUSES:
            allowed = ", ".join(STATUS_SUMMARY_ORDER)

            raise ValueError(f"status must be one of: {allowed}")

        test["status"] = status
        test["duration_ms"] = round((perf_counter() - test.pop("_started")) * 1000, 2)
        test["error"] = str(error) if error else None
        self.tests.append(test)
        self._active = None

    def generate_report(self) -> Path:
        """Generate the standalone dashboard and test-detail HTML files."""
        if self._active is not None:
            raise RuntimeError("End the active test before generating the report")

        summary = self._summary()
        index_tests = []
        suite_indexes: dict[str, int] = {}
        ordered_tests = sorted(
            self.tests,
            key=lambda test: (
                test.get("_order") is None,
                test.get("_order") if test.get("_order") is not None else 0,
                test.get("name", ""),
            ),
        )
        for test in ordered_tests:
            suite_directory_name = (
                re.sub(r"[^a-zA-Z0-9._-]+", "_", test.get("suite", "")).strip("._")
                or "Unassigned"
            )
            suite_indexes[suite_directory_name] = (
                suite_indexes.get(suite_directory_name, 0) + 1
            )
            index = suite_indexes[suite_directory_name]
            detail_directory = self.output_path.parent / suite_directory_name
            detail_directory.mkdir(parents=True, exist_ok=True)
            safe_name = (
                re.sub(r"[^a-zA-Z0-9._-]+", "_", test["name"]).strip("._") or "test"
            )
            filename = f"{index:03d}_{safe_name}.html"
            request = test.get("request") or {}
            response = test.get("response") or {}
            index_test = {
                "name": test["name"],
                "suite": test.get("suite", ""),
                "status": test["status"],
                "duration_ms": test.get("duration_ms", 0),
                "request": {
                    "method": request.get("method", ""),
                    "url": request.get("url", ""),
                },
                "response": {
                    "status_code": response.get("status_code"),
                    "elapsed_ms": response.get("elapsed_ms"),
                },
                "error": test.get("error"),
                "detail_url": f"{suite_directory_name}/{filename}",
            }
            index_tests.append(index_test)
            detail_data = {
                "title": (
                    f"{test['suite']} - {test['name']}"
                    if test.get("suite")
                    else test["name"]
                ),
                "environment": self.environment,
                "generated_at": datetime.now(UTC)
                .astimezone()
                .isoformat(timespec="seconds"),
                "summary": summary,
                "index_url": "../" + self.output_path.name,
                "tests": [test],
            }
            self._write_report(
                detail_directory / filename, detail_data, page_class="detail-page"
            )

        data = {
            "title": self.title,
            "environment": self.environment,
            "generated_at": datetime.now(UTC)
            .astimezone()
            .isoformat(timespec="seconds"),
            "summary": summary,
            "suite_summary": self._suite_summary(),
            "run_info": self.run_info,
            "is_index": True,
            "tests": index_tests,
        }
        self._write_report(self.output_path, data, page_class="index-page")

        return self.output_path.resolve()

    def _write_report(
        self, path: Path, data: dict[str, Any], page_class: str = ""
    ) -> None:
        """Write one standalone HTML report to disk."""
        report_html = self._build_report_html(data, page_class)

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report_html, encoding="utf-8")

    def _build_report_html(self, data: dict[str, Any], page_class: str) -> str:
        """Build standalone HTML by combining the template, data, and script."""
        template = self.template_path.read_text(encoding="utf-8")
        script_path = self.template_path.with_name(REPORT_SCRIPT_FILENAME)
        report_script = script_path.read_text(encoding="utf-8")
        report_data = self._serialize_report_data(data)

        replacements = {
            REPORT_DATA_PLACEHOLDER: report_data,
            REPORT_SCRIPT_PLACEHOLDER: report_script,
            PAGE_CLASS_PLACEHOLDER: page_class,
        }
        return self._replace_template_placeholders(template, replacements)

    @staticmethod
    def _serialize_report_data(data: dict[str, Any]) -> str:
        """Serialize report data safely for embedding inside an HTML script tag."""
        payload = json.dumps(data, ensure_ascii=False)
        return (
            payload.replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("&", "\\u0026")
        )

    @staticmethod
    def _replace_template_placeholders(
        template: str, replacements: Mapping[str, str]
    ) -> str:
        """Validate and replace every required placeholder in the HTML template."""
        rendered = template
        for placeholder, value in replacements.items():
            if placeholder not in rendered:
                raise ValueError(f"HTML template does not contain {placeholder}")

            rendered = rendered.replace(placeholder, value)

        return rendered

    def _summary(self) -> dict[str, Any]:
        """Calculate run-level counts, pass rate, latency, and duration."""
        counts = {
            key: sum(test["status"] == key for test in self.tests)
            for key in STATUS_SUMMARY_ORDER
        }
        total = len(self.tests)
        latencies = sorted(
            float(test["response"]["elapsed_ms"])
            for test in self.tests
            if test.get("response") and test["response"].get("elapsed_ms") is not None
        )
        p95 = (
            latencies[max(0, math.ceil(0.95 * len(latencies)) - 1)] if latencies else 0
        )

        return {
            **counts,
            "total": total,
            "pass_rate": round(counts[STATUS_PASSED] / total * 100, 1) if total else 0,
            "p95_latency_ms": round(p95, 2),
            "duration_ms": round((perf_counter() - self._run_started) * 1000, 2),
        }

    def _suite_summary(self) -> list[dict[str, Any]]:
        """Aggregate status counts and execution duration for every API suite."""
        suites: dict[str, dict[str, Any]] = {}
        for test in self.tests:
            name = test.get("suite") or "Unassigned"
            suite = suites.setdefault(
                name,
                {
                    "name": name,
                    **{status: 0 for status in STATUS_SUMMARY_ORDER},
                    "total": 0,
                    "duration_ms": 0.0,
                },
            )
            suite[test["status"]] += 1
            suite["total"] += 1
            suite["duration_ms"] += float(test.get("duration_ms", 0))

        for suite in suites.values():
            suite["duration_ms"] = round(suite["duration_ms"], 2)

        return sorted(suites.values(), key=lambda item: item["name"].lower())

    def _normalise(self, value: Any) -> Any:
        """Convert bytes and JSON strings into report-safe Python values."""
        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="replace")

        if isinstance(value, str):
            try:
                value = json.loads(value)

            except json.JSONDecodeError:
                return value

        return self._redact(value)

    def _redact(self, value: Any) -> Any:
        """Recursively mask sensitive fields, headers, and bearer tokens."""
        value = deepcopy(value)

        if isinstance(value, Mapping):
            return {
                str(key): (
                    "***REDACTED***"
                    if str(key).lower() in self.SENSITIVE_KEYS
                    else self._redact(item)
                )
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [self._redact(v) for v in value]

        if isinstance(value, tuple):
            return [self._redact(v) for v in value]

        if isinstance(value, str):
            return re.sub(
                r"(?i)bearer\s+[a-z0-9._~+/=-]+", "Bearer ***REDACTED***", value
            )

        if value is None or isinstance(value, (bool, int, float)):
            return value

        return str(value)

    @staticmethod
    def _format_log_message(message: Any, args: tuple[Any, ...]) -> str:
        """Apply the percent-style formatting used by :mod:`logging`."""
        if not args:
            return str(message)

        format_values: Any = (
            args[0] if len(args) == 1 and isinstance(args[0], Mapping) else args
        )

        return str(message) % format_values

    def _require_active(self) -> dict[str, Any]:
        """Return the active test record or raise if collection has not started."""
        if self._active is None:
            raise RuntimeError("Call start_test() first")

        return self._active
