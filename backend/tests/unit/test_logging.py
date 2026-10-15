"""Tests for structured logging configuration."""

import pytest
import structlog

from spd.core.config import Environment
from spd.core.logging import build_processors, configure_logging


def test_production_renders_json() -> None:
    processors = build_processors(Environment.PRODUCTION)

    assert isinstance(processors[-1], structlog.processors.JSONRenderer)


def test_development_renders_console() -> None:
    processors = build_processors(Environment.DEVELOPMENT)

    assert isinstance(processors[-1], structlog.dev.ConsoleRenderer)


def test_shared_processors_carry_context_and_timestamps() -> None:
    processors = build_processors(Environment.TESTING)

    assert structlog.processors.add_log_level in processors
    assert any(isinstance(p, structlog.processors.TimeStamper) for p in processors)
    assert any(
        isinstance(p, structlog.processors.StackInfoRenderer) for p in processors
    )


def test_configure_logging_outputs_readable_lines(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging(Environment.DEVELOPMENT)

    structlog.get_logger("spd").info("starting", port=8000)

    captured = capsys.readouterr()
    assert "starting" in captured.out
