"""Common response helpers to keep API outputs consistent."""

from typing import Any, Optional


def success_response(data: Optional[Any] = None, message: str = "success") -> dict[str, Any]:
    """标准成功响应格式。"""

    return {
        "code": 0,
        "data": data,
        "message": message,
    }


def error_response(code: int = 1, message: str = "error", data: Optional[Any] = None) -> dict[str, Any]:
    """标准错误响应格式，保留 data 便于前端展示细节。"""

    return {
        "code": code,
        "data": data,
        "message": message,
    }
