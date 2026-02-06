
from typing import Optional
from fastapi import Request

# Simple method to unify the redis key design usage
def GetRedisKeyDesign(Day : str, TransactionType : str) -> str:

	return f"agg:{Day}:{TransactionType}s"

# Simple method to unify the day date format
def GetDayDateFormat():

	return '%Y-%m-%d'

def GetRedisKeyDesignPattern(*, Day : Optional[str] = None, TransactionType : Optional[str] = None) -> str:

	DayString = Day if Day else "*"

	TransactionTypeString = TransactionType if TransactionType else "*"

	return f"agg:{DayString}:{TransactionTypeString}s" if Day else "agg:*"

def GetRedis(Apirequest : Request):

	return Apirequest.app.state.Redis

def GetMongoDb(Apirequest : Request):

	return Apirequest.app.state.MongoDb