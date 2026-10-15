"""Structured logging setup (structlog)."""

import logging
from typing import Any

import structlog

from spd.core.config import Environment


def build_processors(environment: Environment) -> list[Any]:
    """Build the structlog processor chain for the given environment."""
    shared: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]
    if environment is Environment.PRODUCTION:
        return [*shared, structlog.processors.JSONRenderer()]
    return [*shared, structlog.dev.ConsoleRenderer()]


def configure_logging(environment: Environment) -> None:
    """Configure structlog and stdlib logging for the process."""
    logging.basicConfig(level=logging.INFO, format="%(message)s", force=True)
    structlog.configure(
        processors=build_processors(environment),
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    )
