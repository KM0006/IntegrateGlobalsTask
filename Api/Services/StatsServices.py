
import asyncio

from typing import List
from redis.asyncio import Redis
from RedisHelper import RedisServices
from AppConfig import GetAppConfig, AppConfig
from Models.DailyAggregate import DailyAggregate
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta, date, time, timezone
from HelperMethods import GetRedisKeyDesignPattern, GetDayDateFormat
from Db.Repositories.DailyAggregatesRepository import DailyAggregatesRepository

async def GetStats(AppRedisClient : Redis, AppMongoDb : AsyncIOMotorDatabase, FromDate : datetime, ToDate : datetime) -> List[DailyAggregate]:
	
	async def FetchRedis(FromDate : datetime, ToDate : datetime, CutOffDate : datetime, AppRedisClient : Redis) -> List[DailyAggregate]:

		RedisKeySearchPatternList : List[str] = []
		
		# if ToDate >= CutOffDate, data from redis must be utilized
		if ToDate >= CutOffDate:
			DayIterator = max(CutOffDate, FromDate)

			while (DayIterator <= ToDate):

				StringDate = DayIterator.strftime(GetDayDateFormat())

				RedisKeySearchPatternList.append(GetRedisKeyDesignPattern(Day = StringDate))

				DayIterator += timedelta(days = 1)

		return await RedisServices.GetDailyAggregatesByRedisKeys(AppRedisClient, Pattern = RedisKeySearchPatternList)
	
	async def FetchMongoDb(FromDate : datetime, ToDate : datetime, CutOffDate : datetime, AppMongoDb : AsyncIOMotorDatabase) -> List[DailyAggregate]:

		StringFromDate = FromDate.strftime(GetDayDateFormat())

		StringToDate = min(ToDate, CutOffDate).strftime(GetDayDateFormat())

		DailyAggregatesRepo : DailyAggregatesRepository = DailyAggregatesRepository(AppMongoDb)

		return await DailyAggregatesRepo.GetByDateRange(From = StringFromDate, To = StringToDate)

	NowDate = datetime.combine(date.today(), time.min, tzinfo = timezone.utc)

	AppConfigSettings : AppConfig = GetAppConfig()
	
	CutOffDate = NowDate - timedelta(days = AppConfigSettings.CutOffDays, minutes = AppConfigSettings.CutOffMinutes, seconds = AppConfigSettings.CutOffSeconds) 

	FetchRedisTaskResult, FetchMongoDbTask = \
		await asyncio.gather \
			(
				FetchRedis(FromDate, ToDate, CutOffDate, AppRedisClient),
				FetchMongoDb(FromDate, ToDate, CutOffDate, AppMongoDb),
				return_exceptions = True
			)

	Result = []

	Result.extend([] if isinstance(FetchRedisTaskResult, Exception) else FetchRedisTaskResult)

	Result.extend([] if isinstance(FetchMongoDbTask, Exception) else FetchMongoDbTask)

	return Result
