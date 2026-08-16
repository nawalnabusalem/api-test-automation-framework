import shutil
from datetime import datetime
from pathlib import Path
from time import perf_counter

import pytest

from config.config import Config
from logger.html_report_logger import (
    DEFAULT_REPORT_ROOT,
    REPORT_RUNS_DIRECTORY,
    STATUS_ERROR,
    STATUS_FAILED,
    STATUS_PASSED,
    STATUS_SKIPPED,
)


def pytest_configure(config):
    config._report_run_started = perf_counter()


def _is_worker(config):
    return hasattr(config, "workerinput")


def _prepare_report_root(config):
    """Clear only temporary root output; timestamped runs are preserved."""
    if _is_worker(config) or getattr(config, "_report_prepared", False):
        return
    config._report_prepared = True

    report_root = Path(config.getoption("report_root"))
    if not report_root.exists():
        return

    runs_root = report_root / REPORT_RUNS_DIRECTORY
    current_entries = [entry for entry in report_root.iterdir() if entry != runs_root]
    for entry in current_entries:
        if entry.is_dir():
            shutil.rmtree(entry)
        else:
            entry.unlink()


def _store_completed_run(config):
    """Move every completed controller report into a timestamped run folder."""
    if _is_worker(config):
        return

    report_root = Path(config.getoption("report_root"))
    current_entries = [
        entry for entry in report_root.iterdir() if entry.name != REPORT_RUNS_DIRECTORY
    ]
    if not current_entries:
        return

    runs_root = report_root / REPORT_RUNS_DIRECTORY
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_path = runs_root / timestamp
    suffix = 1
    while run_path.exists():
        run_path = runs_root / f"{timestamp}_{suffix}"
        suffix += 1
    run_path.mkdir(parents=True)
    for entry in current_entries:
        destination = run_path / entry.name
        shutil.move(str(entry), str(destination))

    retention = max(0, config.getoption("report_retention"))
    if runs_root.exists():
        runs = sorted(
            (entry for entry in runs_root.iterdir() if entry.is_dir()),
            key=lambda entry: entry.name,
            reverse=True,
        )
        for expired in runs[retention:]:
            shutil.rmtree(expired)


def pytest_addoption(parser):
    parser.addoption(
        "--console-log-level",
        action="store",
        default="info",
        help="Console log level, valid values: debug, info, warning, error",
    )
    parser.addoption(
        "--timeout",
        action="store",
        default=20,
        help="Waiting request timeout in seconds, default 20 seconds",
    )
    parser.addoption("--base_url", action="store", default="https://dummyjson.com", help="Base URL")
    parser.addoption(
        "--environment",
        action="store",
        default="Testing",
        help="Environment name shown in the HTML report",
    )
    parser.addoption(
        "--report-root",
        action="store",
        default=str(DEFAULT_REPORT_ROOT),
        help="Directory for the latest HTML report",
    )
    parser.addoption(
        "--report-retention",
        action="store",
        type=int,
        default=10,
        help="Number of timestamped report runs to keep",
    )
    parser.addini(
        "report_tags",
        type="linelist",
        default=["critical", "negative", "smoke", "regression"],
        help="Pytest marker names that should appear as HTML report tags",
    )


def pytest_collection_finish(session):
    """Archive the previous report only when collected tests will execute."""
    if session.config.option.collectonly or not session.items or _is_worker(session.config):
        return
    _prepare_report_root(session.config)


def pytest_collection_modifyitems(items):
    """Give results a stable order independent of parallel completion time."""
    for order, item in enumerate(items):
        item._report_order = order


@pytest.hookimpl(optionalhook=True)
def pytest_xdist_setupnodes(config, specs):
    """Archive once in the xdist controller before workers execute tests."""
    if not config.option.collectonly and specs:
        _prepare_report_root(config)


@pytest.hookimpl(optionalhook=True)
def pytest_testnodedown(node, error):
    """Merge a completed worker's serializable results into the controller."""
    config = node.config
    results = getattr(config, "_worker_report_tests", [])
    results.extend(node.workeroutput.get("html_report_tests", []))
    if error:
        results.append(
            {
                "name": f"worker_{node.gateway.id}_crash",
                "suite": "pytest-xdist",
                "status": STATUS_ERROR,
                "duration_ms": 0,
                "request": None,
                "response": None,
                "error": str(error),
                "logs": [],
                "info": {"description": "Parallel test worker crashed", "file": "", "tags": []},
                "_order": None,
            }
        )
    config._worker_report_tests = results


def pytest_runtest_logstart(nodeid, location):
    """Disable test start messages"""
    pass


def pytest_runtest_logfinish(nodeid, location):
    """Disable test finish messages"""
    pass


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()

    # Store all phases (setup/call/teardown)
    setattr(item, f"rep_{rep.when}", rep)

    if rep.when == "teardown" and hasattr(item, "_html_report_logger"):
        logger = item._html_report_logger
        setup = getattr(item, "rep_setup", None)
        test_call = getattr(item, "rep_call", None)

        if setup is not None and setup.skipped:
            logger.end_test(STATUS_SKIPPED, setup.longrepr)
        elif setup is not None and setup.failed:
            logger.end_test(STATUS_ERROR, setup.longrepr)
        elif test_call is not None and test_call.skipped:
            logger.end_test(STATUS_SKIPPED, test_call.longrepr)
        elif test_call is not None and test_call.failed:
            error = str(test_call.longrepr)
            if rep.failed:
                error += f"\n\nTeardown error:\n{rep.longrepr}"
            logger.end_test(STATUS_FAILED, error)
        elif rep.failed:
            logger.end_test(STATUS_ERROR, rep.longrepr)
        elif test_call is not None and test_call.passed:
            logger.end_test(STATUS_PASSED)
        else:
            logger.end_test(STATUS_ERROR, "Test did not produce a call-phase result")

        del item._html_report_logger


def pytest_sessionfinish(session, exitstatus):
    """Generate one main report after every API test suite has finished."""
    from tests.base_test import BaseTest

    if _is_worker(session.config):
        if BaseTest.logger is not None:
            if BaseTest.logger._active is not None:
                BaseTest.logger.end_test(
                    STATUS_ERROR, "Worker ended before test teardown completed"
                )
            session.config.workeroutput["html_report_tests"] = BaseTest.logger.tests
        return

    worker_tests = getattr(session.config, "_worker_report_tests", None)
    if worker_tests is not None:
        logger = BaseTest.create_logger(session.config)
        logger.tests = worker_tests
        logger.generate_report()
        _store_completed_run(session.config)
    elif BaseTest.logger is not None:
        if BaseTest.logger._active is not None:
            BaseTest.logger.end_test(
                STATUS_ERROR, "Pytest session ended before test teardown completed"
            )
        BaseTest.logger.generate_report()
        _store_completed_run(session.config)
