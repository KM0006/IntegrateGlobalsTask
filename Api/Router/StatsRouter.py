
from typing import List
from redis.asyncio import Redis
from Api.Services import StatsServices
from datetime import datetime, timezone
from Models.DailyAggregate import DailyAggregate
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import APIRouter, Request, Query, Depends
from HelperMethods import GetRedis, GetMongoDb, GetDayDateFormat
from Exceptions.Exceptions import InvalidQueryParameterApiException 
from Api.Models.ApiDailyAggregateResponse import ApiDailyAggregateResponse

StatsRouter = APIRouter \
(
	prefix = "/stats"
)

@StatsRouter.get("/")
async def GetStatsByDataRange \
	(
		ApiRequest : Request,
		From : str = Query(..., pattern = r'^\d{4}-\d{2}-\d{2}$', description = "Start date (YYYY-MM-DD)", alias = "from_date"),
		To : str = Query(..., pattern = r'^\d{4}-\d{2}-\d{2}$', description = "End date (YYYY-MM-DD)", alias = "to_date"),
		Redis : Redis = Depends(GetRedis),
		MongoDb : AsyncIOMotorDatabase = Depends(GetMongoDb),
	):
	
	FromDate = datetime.strptime(From, GetDayDateFormat()).replace(tzinfo = timezone.utc)
	ToDate = datetime.strptime(To, GetDayDateFormat()).replace(tzinfo = timezone.utc)
	
	if FromDate > ToDate:

		raise InvalidQueryParameterApiException(status_code = 400, detail = "From parameter must be before or equal to To")

	Result : List[DailyAggregate]= await StatsServices.GetStats(Redis, MongoDb, FromDate, ToDate)

	ApiResponse : ApiDailyAggregateResponse = ApiDailyAggregateResponse.MapFromDailyAggregateList(Result)

	return ApiResponse.model_dump()
