
from fastapi import HTTPException

RedisConnectionExceptionMessage = "Redis Connection Failed"
CsvFileParsingExceptionMessage = "Error occurred parsing CsvFile"

class AppException(Exception):

	def __init__(self, message : str):

		super().__init__(message)

class StatsApiException(HTTPException):

	def __init__(self, StatusCode : str, message : str):

		super().__init__(StatusCode, message)

class InvalidQueryParameterApiException(StatsApiException):

	def __init__(self, StatusCode : str, message : str):

		super().__init__(StatusCode, message)

class RedisConnectionException(AppException):

	def __init__(self, message : str = RedisConnectionExceptionMessage):

		super().__init__(message)

class CsvFileParsingException(AppException):

	def __init__(self, message : str = CsvFileParsingExceptionMessage):

		super().__init__(message)
		