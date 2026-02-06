
from redis.asyncio import Redis
from typing import List, Optional
from datetime import datetime, timezone
from Models.DailyAggregate import DailyAggregate

async def ScanRedisKeys(Redis : Redis, Pattern : List[str]) -> List[bytes]:

	if Pattern == []:

		return []

	KeysList = []
	
	for SearchPattern in Pattern:

		Cursor = 0

		while True:
			
			Cursor, keys = await Redis.scan \
			(
				cursor = Cursor,
				match = SearchPattern,
			)

			KeysList.extend(keys)
			
			if Cursor == 0:

				break

	return KeysList

async def GetDailyAggregatesByRedisKeys(Redis : Redis, *, KeyList : Optional[List[bytes]] = None, Pattern : Optional[List[str]] = None) -> List[DailyAggregate]:

	if (KeyList is None) and (Pattern is None):

		raise Exception("KeysList or Pattern parameters must be provided and not non none")

	RedisKeyList = KeyList if KeyList else await ScanRedisKeys(Redis, Pattern)

	if (RedisKeyList == []):

		return []

	RedisKeyList = [Key.decode('utf-8') for Key in RedisKeyList]

	DailyAggregateList = []

	async with Redis.pipeline() as pipe:
		
		for key in RedisKeyList:
			pipe.hgetall(key)
		
		DailyAggregateDictList = await pipe.execute()

	for Key, DailyAggregateDict in zip(RedisKeyList, DailyAggregateDictList):

		StringKeySegments = Key.split(':')

		if len(StringKeySegments) != 3:

			continue

		_, StringDate, TransactionType = StringKeySegments


		if not DailyAggregateDict:

			continue
		
		TotalAmountPerMethodDict = \
		{
			PaymentMethod.decode('utf-8') : float(Amount.decode('utf-8'))
			for PaymentMethod, Amount in DailyAggregateDict.items()
		}

		DailyAggregateList.append \
		(
			DailyAggregate \
			(
				Date = StringDate,
				Type = TransactionType,
				TotalAmount = TotalAmountPerMethodDict,
				LastUpdated = datetime.now(timezone.utc)
			)
		)

	return DailyAggregateList