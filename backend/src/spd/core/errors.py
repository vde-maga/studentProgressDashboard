"""Problem+json (RFC 7807) error handling."""

from http import HTTPStatus

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

PROBLEM_JSON = "application/problem+json"

logger = structlog.get_logger("spd.errors")


class AppError(Exception):
    """Expected, domain-level failure mapped to a problem+json response."""

    def __init__(self, status_code: int, code: str, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.code = code
        self.detail = detail


def problem_response(
    status_code: int,
    code: str,
    detail: str,
    *,
    errors: list[dict[str, object]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Render an RFC 7807 problem document."""
    body: dict[str, object] = {
        "type": "about:blank",
        "title": HTTPStatus(status_code).phrase,
        "status": status_code,
        "code": code,
        "detail": detail,
    }
    if errors is not None:
        body["errors"] = errors
    return JSONResponse(
        status_code=status_code,
        content=body,
        media_type=PROBLEM_JSON,
        headers=headers,
    )


async def _app_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)
    return problem_response(exc.status_code, exc.code, exc.detail)


async def _http_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    return problem_response(
        exc.status_code,
        "http_error",
        str(exc.detail),
        headers=dict(exc.headers or {}),
    )


async def _validation_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    errors = [
        {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]
    return problem_response(
        422,
        "validation_error",
        "Request payload or parameters are invalid.",
        errors=errors,
    )


async def _unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "unhandled_error",
        path=request.url.path,
        method=request.method,
        error_type=type(exc).__name__,
    )
    return problem_response(
        500,
        "internal_error",
        "An unexpected error occurred.",
    )


def register_error_handlers(app: FastAPI) -> None:
    """Attach every exception handler to the application."""
    app.add_exception_handler(AppError, _app_error_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_exception_handler(Exception, _unhandled_error_handler)
