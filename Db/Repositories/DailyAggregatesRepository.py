
from bson import ObjectId
from Db.Schema import MongoSchema
from datetime import datetime, timezone
from pymongo.operations import UpdateOne
from pymongo.results import BulkWriteResult
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from Db.Repositories.BaseRepository import BaseRepository
from Models.DailyAggregate import DailyAggregate, DailyAggregateDocumentKeyNames

class DailyAggregatesRepository(BaseRepository[DailyAggregate]):

	CollectionConfig = MongoSchema.DailyAggregates

	def __init__(self, Db : AsyncIOMotorDatabase):

		super().__init__(Db)

	async def UpsertDailyAggregate(self, StringDate : str, TransactionType : str, TotalAmountPerMethodDict : Dict[str, float]) -> bool:
		
		DailyAggregateDocument : DailyAggregate = DailyAggregate \
			(Date = StringDate, Type = TransactionType, TotalAmount = TotalAmountPerMethodDict, LastUpdated = datetime.now(timezone.utc))
		
		FilterQuery = \
		{
			DailyAggregateDocumentKeyNames.Date.value : StringDate,
			DailyAggregateDocumentKeyNames.Type.value: TransactionType
		}
		
		Result = await self.Replace \
		(
			Filter = FilterQuery,
			NewReplacement = DailyAggregateDocument.model_dump(),
			Upsert = True
		)
		
		return Result

	async def BulkUpsertDailyAggreates(self, DailyAggregateList : List[DailyAggregate], Upsert : bool) -> BulkWriteResult:
		
		Requests = \
		[
			UpdateOne \
			(
				filter = \
				{
					DailyAggregateDocumentKeyNames.Date.value : DailyAggregate.Date,
					DailyAggregateDocumentKeyNames.Type.value: DailyAggregate.Type
				},
				update = \
				{
					"$set":
					{
						DailyAggregateDocumentKeyNames.TotalAmount.value : DailyAggregate.TotalAmount,
						DailyAggregateDocumentKeyNames.LastUpdated.value : datetime.now(timezone.utc)
					}
				},
				upsert = Upsert
			)
			for DailyAggregate in DailyAggregateList
		]
		
		return await self.BulkWrite(Requests, False) 

	async def GetDailyAggregate(self, Filter: Dict[str, Any], Projection: Optional[Dict[str, Any]] = None) -> Optional[DailyAggregate]:

		Result = await self.Get(Filter = Filter, Projection = Projection)

		return DailyAggregate.CreateFromDict(Result) if Result else None
	
	async def GetDailyAggregateRange(self, Filter: Dict[str, Any] = None, Projection: Optional[Dict[str, Any]] = None, Limit: int = 0, Sort: Optional[List[tuple]] = None) -> List[DailyAggregate]:

		ResultList = await self.GetRange(Filter = Filter, Projection = Projection)

		if ResultList is None:

			return []

		return [DailyAggregate.CreateFromDict(Result) for Result in ResultList]

	async def GetByDate(self, StringDate: str) -> List[DailyAggregate]:
		
		return await self.GetDailyAggregateRange \
		(
			Filter = {DailyAggregateDocumentKeyNames.Date.value: StringDate},
			Sort = [(DailyAggregateDocumentKeyNames.Type.value, 1)]
		)

	async def GetByDateAndType(self, StringDate: str, TransactionType: str) -> Optional[DailyAggregate]:
		
		return await self.GetDailyAggregate \
		(
			Filter = \
			{
				DailyAggregateDocumentKeyNames.Date.value: StringDate,
				DailyAggregateDocumentKeyNames.Type.value: TransactionType
			}
		)

	async def GetByObjectId(self, ObjId: str | ObjectId) -> Optional[DailyAggregate]:
		
		if isinstance(ObjId, str):
			ObjId = ObjectId(ObjId)
		
		return await self.GetDailyAggregate(Filter = { DailyAggregateDocumentKeyNames.Id.value : ObjId })

	async def GetByDateRange(self, From : str, To : str) -> List[DailyAggregate]:
		
		return await self.GetDailyAggregateRange \
		(
			Filter = \
			{
				DailyAggregateDocumentKeyNames.Date.value:
				{
					"$gte": From,
					"$lt": To
				}
			},
			Sort = [(DailyAggregateDocumentKeyNames.Date.value, 1), (DailyAggregateDocumentKeyNames.Type.value, 1)]
		)

	async def DeleteBeforeDate(self, CutOffDate: str) -> int:
		
		DeletedCount = await self.DeleteRange(Filter = { DailyAggregateDocumentKeyNames.Date.value: {"$lt": CutOffDate} })
		
		return DeletedCount

	async def GetAllDates(self) -> List[str]:
		
		DistinctDates = await self.Distinct(DailyAggregateDocumentKeyNames.Date.value)

		return sorted(DistinctDates)

	async def GetPaymentMethodsByDate(self, StringDate: str, TransactionType: str) -> List[str]:
		
		Document = await self.GetByDateAndType(StringDate, TransactionType)
		
		if not Document or DailyAggregateDocumentKeyNames.TotalAmount.value not in Document:
			return []
		
		return list(Document[DailyAggregateDocumentKeyNames.TotalAmount.value].keys())

	async def GetTotalByPaymentMethod(self, PamentMethod: str, From: str, To: str, TransactionType: Optional[str] = None) -> float:
		
		FilterQuery = \
		{
			DailyAggregateDocumentKeyNames.Date.value: {"$gte": From, "$lte": To}
		}
		
		if TransactionType:
			FilterQuery[DailyAggregateDocumentKeyNames.Type.value] = TransactionType
		
		DocumentList = await self.GetRange(Filter = FilterQuery)
		
		Total = 0.0

		for Document in DocumentList:
			if PamentMethod in Document.get(DailyAggregateDocumentKeyNames.TotalAmount.value, {}):
				Total += Document[DailyAggregateDocumentKeyNames.TotalAmount.value][PamentMethod]
		
		return Total

	async def IncrementForPaymentMethod(self, StringDate: str, TransactionType: str, PaymentMethod: str, Amount: float) -> bool:
		
		FilterQuery = \
		{
			DailyAggregateDocumentKeyNames.Date.value: StringDate,
			DailyAggregateDocumentKeyNames.Type.value: TransactionType
		}
		
		UpdateObj = \
		{
			"$inc": {f"{DailyAggregateDocumentKeyNames.TotalAmount.value}.{PaymentMethod}": Amount},
			"$set": {f"{DailyAggregateDocumentKeyNames.LastUpdated.value}": datetime.now(timezone.utc)}
		}
		
		return await self.Update \
		(
			Filter = FilterQuery,
			UpdateDocumentDict = UpdateObj,
			Upsert = True
		)
