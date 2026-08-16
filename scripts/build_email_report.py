"""Build a static, email-safe summary from a generated main HTML report."""

from __future__ import annotations

import argparse
import json
import re
from html import escape
from pathlib import Path
from typing import Any

REPORT_DATA_PATTERN = re.compile(
    r'<script id="report-data" type="application/json">(.*?)</script>',
    re.DOTALL,
)
STATUS_COLORS = {
    "passed": "#15803d",
    "failed": "#dc2626",
    "error": "#b91c1c",
    "skipped": "#a16207",
}
TABLE_STYLE = (
    "border-collapse:collapse;table-layout:fixed;width:100%;"
    "font-family:Arial,sans-serif;font-size:13px"
)
CELL_STYLE = (
    "border:1px solid #cbd5e1;padding:9px 10px;text-align:left;"
    "vertical-align:middle;word-break:break-word"
)
HEADER_STYLE = f"{CELL_STYLE};background:#e2e8f0;color:#0f172a;font-weight:700"


def read_report_data(report_path: Path) -> dict[str, Any]:
    """Extract embedded JSON data from a generated main report."""
    report_html = report_path.read_text(encoding="utf-8")
    match = REPORT_DATA_PATTERN.search(report_html)
    if match is None:
        raise ValueError(f"Report data was not found in {report_path}")
    return json.loads(match.group(1))


def summary_card(label: str, value: object, color: str = "#0f172a") -> str:
    """Render one compact metric card using email-compatible inline styles."""
    return (
        '<td width="25%" style="padding:6px;vertical-align:top;width:25%">'
        '<div style="border:1px solid #cbd5e1;border-radius:8px;padding:12px;min-height:52px">'
        f'<div style="color:#64748b;font-size:12px">{escape(label)}</div>'
        f'<div style="color:{color};font-size:22px;font-weight:700">{escape(str(value))}</div>'
        "</div></td>"
    )


def render_summary(summary: dict[str, Any]) -> str:
    """Render run-level status, latency, and duration metrics."""
    cards = [
        summary_card(
            "Pass rate", f"{summary.get('pass_rate', 0)}%", STATUS_COLORS["passed"]
        ),
        summary_card("Total", summary.get("total", 0)),
        summary_card("Passed", summary.get("passed", 0), STATUS_COLORS["passed"]),
        summary_card("Failed", summary.get("failed", 0), STATUS_COLORS["failed"]),
        summary_card("Errors", summary.get("error", 0), STATUS_COLORS["error"]),
        summary_card("Skipped", summary.get("skipped", 0), STATUS_COLORS["skipped"]),
        summary_card("P95 latency", f"{summary.get('p95_latency_ms', 0)} ms"),
        summary_card("Duration", f"{summary.get('duration_ms', 0)} ms"),
    ]
    rows = ["".join(cards[index : index + 4]) for index in range(0, len(cards), 4)]
    return (
        '<table role="presentation" width="100%" style="border-collapse:collapse;width:100%;table-layout:fixed"><tbody><tr>'
        + ("</tr><tr>".join(rows))
        + "</tr></tbody></table>"
    )


def header_cell(label: str, width: str) -> str:
    """Render an inline-styled table header with a stable column width."""
    return (
        f'<th width="{width}" style="{HEADER_STYLE};width:{width}">{escape(label)}</th>'
    )


def data_cell(value: object, width: str, extra_style: str = "") -> str:
    """Render an inline-styled data cell for email clients that strip style blocks."""
    return (
        f'<td width="{width}" style="{CELL_STYLE};width:{width};{extra_style}">'
        f"{escape(str(value))}</td>"
    )


def render_suite_rows(suites: list[dict[str, Any]]) -> str:
    """Render the API-suite execution breakdown."""
    return "".join(
        "<tr>"
        f"{data_cell(suite.get('name', 'Unassigned'), '30%')}"
        f"{data_cell(suite.get('total', 0), '12%')}"
        f"{data_cell(suite.get('passed', 0), '12%', 'color:#15803d;font-weight:700')}"
        f"{data_cell(suite.get('failed', 0), '12%', 'color:#dc2626;font-weight:700')}"
        f"{data_cell(suite.get('error', 0), '12%', 'color:#b91c1c;font-weight:700')}"
        f"{data_cell(str(suite.get('duration_ms', 0)) + ' ms', '22%')}"
        "</tr>"
        for suite in suites
    )


def render_test_rows(tests: list[dict[str, Any]]) -> str:
    """Render compact status and endpoint information for every test."""
    rows = []
    for test in tests:
        request = test.get("request") or {}
        response = test.get("response") or {}
        status = str(test.get("status", "error"))
        color = STATUS_COLORS.get(status, "#0f172a")
        rows.append(
            "<tr>"
            f"{data_cell(status.upper(), '12%', f'color:{color};font-weight:700')}"
            f"{data_cell(test.get('name', ''), '36%')}"
            f"{data_cell(test.get('suite', 'Unassigned'), '16%')}"
            f"{data_cell(request.get('method', '--'), '10%')}"
            f"{data_cell(response.get('status_code', '--'), '10%')}"
            f"{data_cell(str(test.get('duration_ms', 0)) + ' ms', '16%')}"
            "</tr>"
        )
    return "".join(rows)


def build_email_html(report: dict[str, Any]) -> str:
    """Create a static HTML email containing the main dashboard results."""
    summary = report.get("summary") or {}
    suites = report.get("suite_summary") or []
    tests = report.get("tests") or []
    suite_headers = "".join(
        [
            header_cell("Suite", "30%"),
            header_cell("Total", "12%"),
            header_cell("Passed", "12%"),
            header_cell("Failed", "12%"),
            header_cell("Errors", "12%"),
            header_cell("Duration", "22%"),
        ]
    )
    test_headers = "".join(
        [
            header_cell("Status", "12%"),
            header_cell("Test", "36%"),
            header_cell("Suite", "16%"),
            header_cell("Method", "10%"),
            header_cell("HTTP", "10%"),
            header_cell("Duration", "16%"),
        ]
    )
    return f"""<!doctype html>
<html>
<body style="margin:0;background:#f8fafc;color:#0f172a;font-family:Arial,sans-serif">
  <main style="max-width:960px;margin:0 auto;padding:24px">
    <h1 style="margin-bottom:4px">{escape(str(report.get("title", "API Test Report")))}</h1>
    <p style="color:#64748b;margin-top:0">{escape(str(report.get("environment", "")))} · {escape(str(report.get("generated_at", "")))}</p>
    <h2>Execution summary</h2>
    {render_summary(summary)}
    <h2>Suite breakdown</h2>
    <table width="100%" style="{TABLE_STYLE};margin-top:8px">
      <thead><tr>{suite_headers}</tr></thead>
      <tbody>{render_suite_rows(suites)}</tbody>
    </table>
    <h2>Test results</h2>
    <table width="100%" style="{TABLE_STYLE};margin-top:8px">
      <thead><tr>{test_headers}</tr></thead>
      <tbody>{render_test_rows(tests)}</tbody>
    </table>
    <p style="color:#64748b;margin-top:20px">The complete interactive HTML report is attached as a ZIP archive.</p>
  </main>
</body>
</html>"""


def main() -> None:
    """Parse command-line paths and write the email-safe HTML report."""
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()

    report = read_report_data(arguments.report)
    arguments.output.write_text(build_email_html(report), encoding="utf-8")


if __name__ == "__main__":
    main()
