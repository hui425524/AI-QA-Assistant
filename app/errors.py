from __future__ import annotations

from typing import Any

from flask import Flask, g, jsonify
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def _payload(error: AppError):
    return jsonify(
        {
            "error": {
                "code": error.code,
                "message": error.message,
                "details": error.details,
                "request_id": getattr(g, "request_id", "unknown"),
            }
        }
    ), error.status_code


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def handle_app_error(error: AppError):
        return _payload(error)

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError):
        return _payload(
            AppError(
                "VALIDATION_ERROR",
                "輸入資料格式不正確。",
                422,
                {"fields": error.errors(include_url=False, include_input=False)},
            )
        )

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        return _payload(
            AppError(
                f"HTTP_{error.code}",
                error.description,
                error.code or 500,
            )
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        app.logger.exception("Unhandled application error", exc_info=error)
        return _payload(
            AppError(
                "INTERNAL_ERROR",
                "系統發生未預期錯誤，請使用 request ID 查詢日誌。",
                500,
            )
        )
