
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

def CreateExceptionHandler(StatusCode: int, InitialErrorDetails: str):

	detail = {"message": InitialErrorDetails}

	async def ExceptionHandler(_: Request, Ex: Exception) -> JSONResponse:

		return JSONResponse \
		(
			status_code = StatusCode,
			content = { "detail": detail["message"] }
		)

	return ExceptionHandler

ErrorExceptionHandler = CreateExceptionHandler(status.HTTP_500_INTERNAL_SERVER_ERROR, "Unexpected error ocurred")
InvalidQueryParameterHandler = CreateExceptionHandler(status.HTTP_422_UNPROCESSABLE_CONTENT, "Invalid Query parameters")
RequestValidationErrorHandler = CreateExceptionHandler(status.HTTP_422_UNPROCESSABLE_CONTENT, "Incomplete Query")

ExceptionHandlerMap = \
[
	(ValueError, InvalidQueryParameterHandler),
	(RequestValidationError, RequestValidationErrorHandler),
	(Exception, ErrorExceptionHandler),
]