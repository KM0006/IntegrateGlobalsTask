
from pydantic import BaseModel
from Db.Schema import CollectionConfig
from pymongo.results import BulkWriteResult
from typing import Dict, List, Any, Optional, Generic, TypeVar
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection

DocumentType = TypeVar('DocumentType', bound = BaseModel)

class BaseRepository(Generic[DocumentType]):

	# Subclasses must override this
	CollectionConfig : CollectionConfig = None

	def __init__(self, Db: AsyncIOMotorDatabase):
		
		if self.CollectionConfig is None:
			
			raise ValueError \
			(
				f"{self.__class__.__name__} must define Configuration for the Collection."
			)
		
		self.Db = Db
		self.Config = self.CollectionConfig
		self.Collection: AsyncIOMotorCollection = Db[self.Config.Name]

	async def Initialize(self):
		
		await self.Config.CreateIndices(self.Db)
		
	async def Insert(self, Document: DocumentType) -> str:
		
		InsertResult = await self.Collection.insert_one(Document.model_dump())
		
		return str(InsertResult.inserted_id)

	async def InsertRange(self, Documents: List[DocumentType]) -> List[str]:
		
		if not Documents:
			return []
		
		InsertedResult = await self.Collection.bulk_write(Documents)
		
		return [str(Id) for Id in InsertedResult.inserted_ids]

	async def Get(self, Filter: Dict[str, Any], Projection: Optional[Dict[str, Any]] = None) -> Optional[DocumentType]:
		
		return await self.Collection.find_one(Filter, Projection)

	async def GetRange(self, Filter: Dict[str, Any] = None, Projection: Optional[Dict[str, Any]] = None, Limit: int = 0, Sort: Optional[List[tuple]] = None) -> List[DocumentType]:
		
		Filter = Filter or {}
		Cursor = self.Collection.find(Filter, Projection)
		
		if Sort:
			Cursor = Cursor.sort(Sort)
		
		if Limit > 0:
			Cursor = Cursor.limit(Limit)
		
		return await Cursor.to_list(length = None)

	async def Update(self, Filter: Dict[str, Any], UpdateDocumentDict: Dict[str, Any], Upsert: bool = False) -> bool:
		
		Result = await self.Collection.update_one(Filter, UpdateDocumentDict, upsert = Upsert)
		
		return Result.modified_count > 0 or Result.upserted_id is not None
	
	async def BulkWrite(self, Requests, InOrder : bool) -> BulkWriteResult:

		return await self.Collection.bulk_write(Requests, InOrder)

	async def Replace(self, Filter: Dict[str, Any], NewReplacement : DocumentType, Upsert: bool = False) -> bool:
		
		Result = await self.Collection.replace_one(Filter, NewReplacement, upsert = Upsert)

		return Result.modified_count > 0 or Result.upserted_id is not None

	async def Delete(self, Filter: Dict[str, Any]) -> bool:
		
		Result = await self.Collection.delete_one(Filter)
		
		return Result.deleted_count > 0

	async def DeleteRange(self, Filter: Dict[str, Any]) -> int:
		
		Result = await self.Collection.delete_many(Filter)
		
		return Result.deleted_count

	async def Count(self, Filter: Dict[str, Any] = None) -> int:
		
		Filter = Filter or {}
		
		return await self.Collection.count_documents(Filter)

	async def Distinct(self, Field: str, Filter: Dict[str, Any] = None) -> List[Any]:
		
		Filter = Filter or {}
		
		return await self.Collection.distinct(Field, Filter)