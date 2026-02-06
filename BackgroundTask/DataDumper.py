
import asyncio
import logging

from typing import List
from redis.asyncio import Redis
from pymongo.results import BulkWriteResult
from Models.DailyAggregate import DailyAggregate
from motor.motor_asyncio import AsyncIOMotorDatabase

from RedisHelper import RedisServices
from HelperMethods import GetRedisKeyDesignPattern
from BackgroundTask.CriticalTaskDecorator import CriticalTask
from BackgroundTask.CancellationToken import CancellationToken
from Db.Repositories.DailyAggregatesRepository import DailyAggregatesRepository

logger = logging.getLogger("uvicorn")

class DataDumper:

	@staticmethod
	@CriticalTask()
	async def DumpData(Redis : Redis, MongoDb : AsyncIOMotorDatabase, DumperTaskScheduleInterval : int, CancellationToken : CancellationToken):
		
		DailyAggregatesRepo : DailyAggregatesRepository = DailyAggregatesRepository(MongoDb)

		await DailyAggregatesRepo.Initialize()

		while(not CancellationToken.IsCancelled()):

			RedisKeysList = await RedisServices.ScanRedisKeys(Redis = Redis, Pattern = GetRedisKeyDesignPattern())
			
			if RedisKeysList == []:

				continue

			RedisDailyAggregateList : List[DailyAggregate] = await RedisServices.GetDailyAggregatesByRedisKeys(Redis, KeyList = RedisKeysList)

			DumpOperationResult : BulkWriteResult =  await DailyAggregatesRepo.BulkUpsertDailyAggreates(RedisDailyAggregateList, Upsert = True)
			
			StringDumpOperationResult = '' \
			f'Dumped {len(RedisDailyAggregateList)} record in Database:' \
			f'  - Inserted Documents {DumpOperationResult.inserted_count}' \
			f'  - Upserted Documents {DumpOperationResult.upserted_count}' \
			f'  - Matched Documents {DumpOperationResult.matched_count}' \
			f'  - Removed Documents {DumpOperationResult.deleted_count}'

			logger.info(StringDumpOperationResult)

			await asyncio.sleep(DumperTaskScheduleInterval)
