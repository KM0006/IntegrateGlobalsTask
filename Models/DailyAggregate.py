
from enum import Enum
from bson import ObjectId
from typing import Dict, Self
from datetime import datetime
from pydantic import BaseModel

class RedisDailyAggregate(BaseModel):

	_id: ObjectId
	Date: str
	Type: str
	TotalAmount: Dict[str, float]

	def CreateFromDict(Dict : dict) -> Self:

		return RedisDailyAggregate(**Dict)
	
class DailyAggregate(RedisDailyAggregate):

	LastUpdated : datetime | None

	def CreateFromDict(Dict : dict) -> Self:

		return DailyAggregate(**Dict)

class DailyAggregateDocumentKeyNames(Enum):
    
	Id = "_id"
	Date = "Date"
	Type = "Type"
	TotalAmount = "TotalAmount"
	LastUpdated = "LastUpdated"
