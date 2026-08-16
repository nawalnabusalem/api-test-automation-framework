import subprocess
from collections.abc import Generator
from pathlib import Path

import pytest
from _pytest.config import Config
from _pytest.fixtures import SubRequest

from api.api_client import APIClient
from logger.html_report_logger import MAIN_REPORT_FILENAME, HTMLReportLogger
from utils import APISuite


class BaseTest:
    """Base class for API tests; subclasses can override API_SUITE."""

    API_SUITE: APISuite
    api_client: APIClient | None = None
    logger: HTMLReportLogger | None = None

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, request: SubRequest) -> Generator[None, None, None]:
        """Initialize reporting and the API client, then always close the session."""
        if BaseTest.logger is None:
            BaseTest.logger = self.create_logger(request.config)

        BaseTest.logger.start_test(
            name=request.node.name,
            suite=self._suite_name(request),
            description=request.node.function.__doc__ or "",
            file=str(request.node.path),
            tags=self._report_tags(request),
            order=getattr(request.node, "_report_order", None),
        )
        request.node._html_report_logger = BaseTest.logger

        self.api_client = APIClient(
            timeout=int(request.config.getoption("timeout")),
            base_url=request.config.getoption("base_url"),
            logger=BaseTest.logger,
        )

        try:
            yield
        finally:
            self.api_client.close()

    @classmethod
    def create_logger(cls, config: Config) -> HTMLReportLogger:
        """Create a logger for a normal run, worker, or xdist controller."""
        logger = HTMLReportLogger(
            output_path=Path(config.getoption("report_root")) / MAIN_REPORT_FILENAME,
            title="API Test Report",
            environment=config.getoption("environment"),
            run_info={
                "base_url": config.getoption("base_url"),
                "branch": cls._git_value("--abbrev-ref", "HEAD"),
                "commit": cls._git_value("--short", "HEAD"),
                "framework": f"pytest {pytest.__version__}",
            },
        )
        logger._run_started = getattr(
            config, "_report_run_started", logger._run_started
        )
        return logger

    @staticmethod
    def _git_value(*arguments: str) -> str:
        try:
            result = subprocess.run(
                ["git", "-c", f"safe.directory={Path.cwd()}", "rev-parse", *arguments],
                capture_output=True,
                text=True,
                check=False,
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        except OSError:
            return ""

    @staticmethod
    def _report_tags(request: SubRequest) -> list[str]:
        """Return only markers explicitly configured as report tags."""
        allowed_tags = set(request.config.getini("report_tags"))
        return sorted(
            {
                marker.name
                for marker in request.node.iter_markers()
                if marker.name in allowed_tags
            }
        )

    def _suite_name(self, request: SubRequest) -> str:
        """Use an explicit API_SUITE or infer it from tests/<suite>/... path."""
        configured = getattr(self, "API_SUITE", None)
        if configured is not None:
            return configured.value if hasattr(configured, "value") else str(configured)

        path_parts = {part.lower() for part in Path(request.node.path).parts}
        suites = {
            "auth": APISuite.AUTH.value,
            "product": APISuite.PRODUCT.value,
            "user": APISuite.USER.value,
        }
        for directory, suite_name in suites.items():
            if directory in path_parts:
                return suite_name
        return "Unassigned"
