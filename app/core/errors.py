from enum import StrEnum
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CAPACITY_EXCEEDED = "CAPACITY_EXCEEDED"
    DIET_MISMATCH = "DIET_MISMATCH"
    COLD_CHAIN_UNAVAILABLE = "COLD_CHAIN_UNAVAILABLE"
    WINDOW_INFEASIBLE = "WINDOW_INFEASIBLE"
    OFFER_EXPIRED = "OFFER_EXPIRED"
    OFFER_NOT_PENDING = "OFFER_NOT_PENDING"
    OTP_INVALID = "OTP_INVALID"
    ROUTE_VERSION_CONFLICT = "ROUTE_VERSION_CONFLICT"
    DRIVER_CAPACITY_EXCEEDED = "DRIVER_CAPACITY_EXCEEDED"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL = "INTERNAL"


class AppException(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


AppError = AppException


class ValidationException(AppException):
    def __init__(self, message: str = "Request validation failed.", details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class UnauthenticatedException(AppException):
    def __init__(
        self, message: str = "Authentication credentials were not provided or are invalid."
    ) -> None:
        super().__init__(
            code=ErrorCode.UNAUTHENTICATED,
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class ForbiddenException(AppException):
    def __init__(self, message: str = "You do not have permission to perform this action.") -> None:
        super().__init__(
            code=ErrorCode.FORBIDDEN,
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class NotFoundException(AppException):
    def __init__(self, message: str = "The requested resource could not be found.") -> None:
        super().__init__(
            code=ErrorCode.NOT_FOUND,
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class CapacityExceededException(AppException):
    def __init__(
        self,
        message: str,
        available: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        merged_details = details or {}
        if available is not None and "available" not in merged_details:
            merged_details["available"] = available
        super().__init__(
            code=ErrorCode.CAPACITY_EXCEEDED,
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=merged_details,
        )


class DietMismatchException(AppException):
    def __init__(
        self, message: str = "Dietary preference does not match recipient acceptance criteria."
    ) -> None:
        super().__init__(
            code=ErrorCode.DIET_MISMATCH,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class ColdChainUnavailableException(AppException):
    def __init__(
        self, message: str = "Cold storage or vehicle cold-box capacity is unavailable."
    ) -> None:
        super().__init__(
            code=ErrorCode.COLD_CHAIN_UNAVAILABLE,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class WindowInfeasibleException(AppException):
    def __init__(
        self, message: str = "Delivery cannot safely reach destination before the expiry deadline."
    ) -> None:
        super().__init__(
            code=ErrorCode.WINDOW_INFEASIBLE,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class OfferExpiredException(AppException):
    def __init__(self, message: str = "This offer has already expired.") -> None:
        super().__init__(
            code=ErrorCode.OFFER_EXPIRED,
            message=message,
            status_code=status.HTTP_410_GONE,
        )


class OfferNotPendingException(AppException):
    def __init__(self, message: str = "This offer is no longer in a pending state.") -> None:
        super().__init__(
            code=ErrorCode.OFFER_NOT_PENDING,
            message=message,
            status_code=status.HTTP_409_CONFLICT,
        )


class OtpInvalidException(AppException):
    def __init__(self, message: str = "The OTP entered is incorrect or expired.") -> None:
        super().__init__(
            code=ErrorCode.OTP_INVALID,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class RouteVersionConflictException(AppException):
    def __init__(
        self, message: str = "Route has been modified by another concurrent action. Please refresh."
    ) -> None:
        super().__init__(
            code=ErrorCode.ROUTE_VERSION_CONFLICT,
            message=message,
            status_code=status.HTTP_409_CONFLICT,
        )


class DriverCapacityExceededException(AppException):
    def __init__(self, message: str = "Total portions exceed maximum vehicle capacity.") -> None:
        super().__init__(
            code=ErrorCode.DRIVER_CAPACITY_EXCEEDED,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class RateLimitedException(AppException):
    def __init__(
        self, message: str = "Too many requests. Please wait a minute before retrying."
    ) -> None:
        super().__init__(
            code=ErrorCode.RATE_LIMITED,
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


def format_error_response(
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    request_id: str = "",
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "request_id": request_id,
        }
    }


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "")
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            code=exc.code,
            message=exc.message,
            details=exc.details,
            request_id=request_id,
        ),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "")
    # Format readable validation errors
    errors = exc.errors()
    first_msg = errors[0].get("msg", "Validation error") if errors else "Validation error"
    field = ".".join(str(loc) for loc in errors[0].get("loc", [])) if errors else ""
    user_msg = f"Invalid input for {field}: {first_msg}" if field else first_msg

    status_code = getattr(
        status, "HTTP_422_UNPROCESSABLE_CONTENT", status.HTTP_422_UNPROCESSABLE_ENTITY
    )
    return JSONResponse(
        status_code=status_code,
        content=format_error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message=user_msg,
            details={"errors": errors},
            request_id=request_id,
        ),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "")
    code = ErrorCode.INTERNAL
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        code = ErrorCode.UNAUTHENTICATED
    elif exc.status_code == status.HTTP_403_FORBIDDEN:
        code = ErrorCode.FORBIDDEN
    elif exc.status_code == status.HTTP_404_NOT_FOUND:
        code = ErrorCode.NOT_FOUND
    elif exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        code = ErrorCode.RATE_LIMITED

    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            code=code,
            message=str(exc.detail),
            details={},
            request_id=request_id,
        ),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=format_error_response(
            code=ErrorCode.INTERNAL,
            message="An unexpected server error occurred. Please try again shortly.",
            details={},
            request_id=request_id,
        ),
    )
