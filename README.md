# API Test Automation Framework 🧪

An API automation framework built with **Python**, **Requests**, and **Pytest**. The included
tests target [DummyJSON](https://dummyjson.com/), while the framework structure and custom HTML
reporter are reusable for other REST APIs.

The main focus of this project is not only showing whether a test passed or failed. It captures
the HTTP evidence needed to understand an API failure: endpoint, method, headers, payload,
response, latency, assertion error, and the logs produced by that specific test.

## 🎯 Why a Custom API Report?

General-purpose test reports normally focus on test names, execution time, and final status.
That is useful for tracking a test run, but it is often not enough for API debugging. When an
API test fails, QA engineers and developers usually need to answer additional questions:

- Which HTTP method and URL were called?
- What request headers and payload were sent?
- What status code, response headers, and body came back?
- Was the problem an assertion failure, timeout, connection failure, or another request error?
- Was the endpoint slow even when it passed?
- Which test steps and diagnostic messages were logged?
- Can the request be copied and reproduced outside the framework?

The custom reporter collects this information during the test and presents it in a standalone,
Postman-style HTML report. The dashboard remains compact, while every test has its own detailed
page for investigation.

## 📦 Project Structure

<pre>
api-test-automation-framework/
├── api/
│   ├── api_client.py             # Shared Requests session and HTTP logging
│   ├── auth/                     # Authentication API service
│   ├── cart/                     # Cart API service
│   ├── product/                  # Product API service
│   └── user/                     # User API service
├── config/
│   └── config.py                 # Environment variables and defaults
├── logger/
│   ├── html_report_logger.py     # Report data collection and generation
│   └── templates/
│       ├── test_case_report.html # Shared HTML and CSS template
│       └── report_script.js      # Dashboard and detail-page behavior
├── tests/
│   ├── base_test.py              # Test setup and guaranteed client cleanup
│   ├── auth/                     # Authentication tests
│   ├── product/                  # Product tests grouped by HTTP method
│   └── user/                     # User tests grouped by HTTP method
├── utils/                         # API suite and HTTP status enums
├── reports/
│   └── runs/                     # Timestamped report history
├── conftest.py                    # Pytest hooks, CLI options, and report lifecycle
├── pytest.ini                     # Test discovery, markers, and cache settings
└── requirements.txt              # Framework dependencies
</pre>

## 🚀 Framework Features

### API client

- Reuses a `requests.Session` during each test.
- Supports GET, POST, PUT, PATCH, and DELETE.
- Combines shared headers with headers supplied for one request.
- Supports bearer-token authentication through `set_auth_token()`.
- Applies a configurable timeout to every request.
- Logs the prepared request before sending it.
- Logs the complete response and elapsed API time.
- Handles and logs `Timeout`, `ConnectionError`, and generic `RequestException` separately.
- Re-raises request exceptions so Pytest records the test failure correctly.
- Always closes the HTTP session through fixture `try/finally` cleanup.

### Endpoint service layer

API operations are defined under `api/` rather than being repeated inside tests. Tests focus on
behavior and assertions, while service classes manage endpoint paths and payload submission.
This separation makes endpoint changes easier to maintain and keeps tests readable.

### Test organization

- Tests are grouped by API suite: Auth, Product, and User.
- Product and user tests are further grouped by HTTP method.
- Parametrization covers multiple inputs without duplicating test logic.
- Docstrings describe test intent and are shown as the test purpose in the report.
- Configured Pytest markers are included as report tags.
- Stable collection order is preserved even when tests execute in parallel.

### Parallel execution

`pytest-xdist` can distribute tests across multiple workers. Each worker collects serializable
test results, and the controller merges them into one final dashboard. A worker crash is recorded
as an error result instead of silently losing its report data.

## 📊 HTML Report Features

### Main dashboard

The main report is designed for quickly understanding the complete execution without expanding
large request and response bodies.

- Circular execution-progress chart for passed, failed, skipped, and error results.
- Pass rate, total tests, status counts, P95 API latency, and total run duration.
- Suite summary with total, passed, failed, error, and duration values.
- Clickable suite names that immediately filter the test list.
- One compact row per test showing:
  - Test status.
  - Test name and API suite.
  - HTTP method and endpoint URL.
  - HTTP response status code.
  - Test duration.
  - A short failure preview for failed and error results.
- Failed and error tests are shown before skipped and passed tests.
- Slower tests are shown first within the same status group.
- Light and dark themes, with the selected theme saved in the browser.

### Dashboard filtering

Filters can be combined to narrow a large execution quickly:

- Free-text search across test name, suite, status, method, URL, response code, and error.
- Test-result status filter.
- HTTP method filter.
- API suite filter.
- Clear Filters button to reset the complete selection.
- Active filters are stored in the page URL, making a filtered report view bookmarkable or
  shareable with another team member.

### Individual test-case report

Every test result links to a separate HTML file. This keeps the dashboard readable and gives the
detail page enough room for API-specific evidence.

The test information section contains:

- Status and API suite.
- Test duration.
- Source test file.
- Pytest tags.
- Test purpose taken from the test docstring.
- Full assertion or execution failure, including a teardown failure when both phases fail.

The request section contains:

- HTTP method and complete URL.
- Request body.
- Request headers and header count.
- Generated cURL command for reproducing the request.
- Copy buttons for body, headers, and cURL.

The response section contains:

- HTTP status code and reason.
- API response latency in milliseconds.
- Response body.
- Response headers and header count.
- Copy buttons for response body and headers.

### JSON viewer

- Automatically parses valid JSON bodies.
- Uses `{}` for objects and `[]` for arrays so their types are immediately visible.
- Shows the number of fields or items in each node.
- Displays strings, numbers, booleans, and null values with different colors.
- Expands the first levels by default while deeper nodes remain individually collapsible.
- Uses a scrollable body area for large API responses.
- Keeps the raw pretty-printed JSON available for accurate copying.
- Falls back to readable text when a body is not valid JSON.

### Test-case logs

- Captures `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL` messages.
- Uses Python logging-style `%` argument formatting.
- Adds a timestamp and level to every message.
- Colors entries by log level.
- Keeps logs attached to the test that produced them.
- Provides search inside the current test case's logs.

### Security and safe output

Sensitive values are recursively masked before report generation. This includes common values
such as authorization headers, proxy authorization, cookies, API keys, access tokens, refresh
tokens, passwords, secrets, and client secrets. Bearer tokens found inside strings are masked as
well.

Report data is safely escaped before it is embedded into the HTML script, reducing the risk of
response content breaking the generated document.

### Standalone output

The template, report data, CSS, and JavaScript are combined into each generated HTML file. No
application server, external JavaScript package, or report viewer is required. A completed run
can be archived or shared as a normal directory and opened directly in a browser.

## 🕒 Report History

Each completed run is moved into a timestamped directory:

<pre>
reports/
└── runs/
    └── 2026-08-16_09-39-33/
        ├── main_report.html
        ├── AuthAPI/
        │   ├── 001_test_get_authenticated_user_profile.html
        │   └── ...
        ├── ProductAPI/
        │   └── ...
        └── UserAPI/
            └── ...
</pre>

History behavior:

- A unique timestamp is created after every completed controller run.
- The main dashboard and all linked test details move together, preserving relative links.
- Existing timestamped runs are not cleared when a new run starts.
- The default retention is the latest 10 runs.
- `--report-retention` changes the number of histories kept.
- Older directories beyond the configured limit are automatically removed.
- `--report-retention=0` disables history retention after the run.
- Collection-only and empty test sessions do not clear report output.
- In parallel execution, history is managed by the controller rather than individual workers.

To open the newest report, select the latest timestamp under `reports/runs/` and open its
`main_report.html` file.

## ⚙️ Running the Tests

### 1. Install dependencies

```powershell
pip install -r .\requirements.txt
```

### 2. Run tests

Run a specific API suite:

```powershell
pytest .\tests\product
```

Run tests in parallel:

```powershell
pytest -n auto
```

## 🧰 Test Configuration Options

This project uses **Pytest** with custom command-line options to provide flexibility when running
tests against different environments and controlling HTML report output.

### 🔧 Available CLI Options

| Option | Description                                        | Default | Example |
| --- |----------------------------------------------------| --- | --- |
| `--base_url` | Override the API base URL.                         | Value from `BASE_URL` | `--base_url=https://api.example.com` |
| `--timeout` | Override the request timeout in seconds.           | Value from `TIMEOUT` | `--timeout=20` |
| `--environment` | Environment label displayed in the report.         | `test` | `--environment=staging` |
| `--report-root` | Directory that contains generated report history.  | `reports` | `--report-root=artifacts` |
| `--report-retention` | Maximum number of timestamped report runs to keep. | `10` | `--report-retention=20` |

Example:

```powershell
pytest --environment=staging --timeout=20 --report-retention=20
```

## 🔐 Environment Configuration

`TEST_USERNAME` and `TEST_PASSWORD` are secrets. The repository therefore contains only a safe
`.env.example`; real credentials cannot be downloaded or copied from GitHub.

### Local execution

Copy the example file to `.env`:

```powershell
Copy-Item .env.example .env
```

Then open `.env` and provide the values for your own test environment:

```dotenv
TEST_USERNAME=your_real_test_username
TEST_PASSWORD=your_real_test_password
```

The `.env` file is excluded by `.gitignore`. Never commit real usernames, passwords, tokens, or
other secrets. Team members must receive test credentials through an approved password manager
or another secure channel, then add them to their own local `.env` file.

| Variable | Description |
| --- | --- |
| `TEST_USERNAME` | Username used only by authentication tests. |
| `TEST_PASSWORD` | Password used only by authentication tests. |

## 🛠️ GitHub Actions Workflow

The workflow in `.github/workflows/api-tests.yml` runs the complete API test suite on:

- Every push to `main`.
- Every pull request targeting `main`.
- Manual execution from the GitHub Actions page.

It checks out the project, sets up Python 3.12, installs `requirements.txt`, validates the
required credentials, and runs Pytest in parallel with `pytest -n auto`. The complete
`reports/runs/` directory is uploaded to this repository's GitHub Actions artifacts and retained
for 14 days.

The artifact can contain API requests, responses, errors, and logs. Repository access should be
limited to trusted team members.

### Set up the test username and password

Do not add real credentials to the workflow or repository files. Store them as encrypted GitHub
repository secrets:

1. Open the repository on GitHub.
2. Select **Settings**.
3. Select **Secrets and variables** → **Actions**.
4. Select **New repository secret**.
5. Create `TEST_USERNAME` and enter the test username.
6. Create `TEST_PASSWORD` and enter the test password.

The workflow safely maps the secrets to the environment variables read by `config.py`:

```yaml
env:
  TEST_USERNAME: ${{ secrets.TEST_USERNAME }}
  TEST_PASSWORD: ${{ secrets.TEST_PASSWORD }}
```

GitHub does not provide repository secrets to workflows triggered from untrusted fork pull
requests. Those runs cannot execute the authenticated tests without credentials in a trusted
workflow context.

### Download the complete report artifact

1. Open the completed run from the repository's **Actions** tab.
2. Scroll to **Artifacts**.
3. Download `api-html-report-<run number>`.
4. Extract the downloaded archive.
5. Open the timestamped run's `main_report.html` in a browser.

### Email the complete HTML report

When the report is generated, the workflow compresses the complete `reports/runs/` directory into
`api-html-report.zip` and emails it to the trusted address stored in `TEST_USER_EMAIL`. The ZIP
contains the main dashboard and all suite-specific test-case detail pages.

The email body contains a static, email-compatible view of the main dashboard with execution
metrics, suite breakdown, and the complete test-result list. The interactive dashboard itself
uses JavaScript, which email clients normally block, so `scripts/build_email_report.py` converts
its embedded report data into safe static HTML before sending the message.

The following repository secrets are required:

| Secret | Description |
| --- | --- |
| `SMTP_SERVER` | SMTP server hostname, such as `smtp.gmail.com`. |
| `SMTP_PORT` | Secure SMTP port, normally `465` for Gmail. |
| `SMTP_USERNAME` | Gmail address used to send the report. |
| `SMTP_PASSWORD` | Google App Password, not the normal Gmail password. |
| `REPORT_EMAIL_FROM` | Sender address displayed in the email. |
| `TEST_USER_EMAIL` | Trusted recipient of the complete report ZIP. |

For the current setup, `TEST_USER_EMAIL` contains `nawalabusalem98@gmail.com`. The email subject
and body use `github.actor` to identify who triggered the workflow.

The recipient should extract `api-html-report.zip` and open the newest timestamped run's
`main_report.html`. Relative links from the dashboard to the detailed test-case reports remain
available because the complete report directory is included.

The email step is skipped when no report files were generated—for example, if dependency
installation or credential validation fails before Pytest starts.

### Run the workflow manually

1. Open the repository's **Actions** tab.
2. Select **API Tests**.
3. Select **Run workflow**.
4. Choose the `main` branch and select **Run workflow**.

## 🏷️ Pytest Markers

| Marker | Purpose |
| --- | --- |
| `smoke` | Essential checks for fast environment validation. |
| `critical` | Business-critical API behavior. |
| `negative` | Invalid input and error-response validation. |
| `regression` | Broader behavior protected against regression. |

Only markers configured under `report_tags` in `pytest.ini` are displayed as tags in the HTML
test details.

## ➕ Extending the Framework

To add another API area:

1. Create an endpoint service under `api/<service>/`.
2. Accept `APIClient` in the service constructor.
3. Add methods that describe API operations and return `requests.Response`.
4. Add tests under `tests/<service>/<http_method>/`.
5. Inherit the test class from `BaseTest` to receive the client and report lifecycle.
6. Add a test docstring so the purpose appears in the detail report.
7. Add meaningful logger calls for actions that help investigate failures.

The reporter is generated automatically at the end of the Pytest session; individual tests do
not need to create or write HTML files.
