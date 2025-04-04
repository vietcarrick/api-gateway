from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class APIError(HTTPException):
	"""Base exception for API errors."""
	
	def __init__(
		self,
		status_code: int,
		detail: Any = None,
		headers: Optional[Dict[str, str]] = None,
		error_code: str = "error",
	):
		super().__init__(status_code=status_code, detail=detail, headers=headers)
		self.error_code = error_code


class AuthenticationError(APIError):
	"""Exception for authentication errors."""
	
	def __init__(
		self,
		detail: Any = "Authentication failed",
		headers: Optional[Dict[str, str]] = None,
	):
		super().__init__(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail=detail,
			headers=headers or {"WWW-Authenticate": "Bearer"},
			error_code="authentication_error",
		)


class AuthorizationError(APIError):
	"""Exception for authorization errors."""
	
	def __init__(
		self,
		detail: Any = "Not authorized to perform this action",
		headers: Optional[Dict[str, str]] = None,
	):
		super().__init__(
			status_code=status.HTTP_403_FORBIDDEN,
			detail=detail,
			headers=headers,
			error_code="authorization_error",
		)


class RateLimitError(APIError):
	"""Exception for rate limit errors."""
	
	def __init__(
		self,
		detail: Any = "Rate limit exceeded",
		headers: Optional[Dict[str, str]] = None,
		retry_after: Optional[int] = None,
	):
		headers = headers or {}
		if retry_after:
			headers["Retry-After"] = str(retry_after)
		
		super().__init__(
			status_code=status.HTTP_429_TOO_MANY_REQUESTS,
			detail=detail,
			headers=headers,
			error_code="rate_limit_error",
		)


class ServiceNotFoundError(APIError):
	"""Exception for service not found errors."""
	
	def __init__(
		self,
		detail: Any = "Service not found",
		headers: Optional[Dict[str, str]] = None,
	):
		super().__init__(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=detail,
			headers=headers,
			error_code="service_not_found",
		)


class ServiceUnavailableError(APIError):
	"""Exception for service unavailable errors."""
	
	def __init__(
		self,
		detail: Any = "Service unavailable",
		headers: Optional[Dict[str, str]] = None,
	):
		super().__init__(
			status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
			detail=detail,
			headers=headers,
			error_code="service_unavailable",
		)


class ProxyError(APIError):
	"""Exception for proxy errors."""
	
	def __init__(
		self,
		detail: Any = "Error proxying request",
		headers: Optional[Dict[str, str]] = None,
		status_code: int = status.HTTP_502_BAD_GATEWAY,
	):
		super().__init__(
			status_code=status_code,
			detail=detail,
			headers=headers,
			error_code="proxy_error",
		)
