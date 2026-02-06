
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from Models.DailyAggregate import DailyAggregateDocumentKeyNames

@dataclass
class IndexConfig:
    
	Keys : str | List[tuple[str, int]]
	Unique : bool = False
	Sparse : bool = False
	TTLSeconds : Optional[int] = None  # For TTL indexes
	Name : Optional[str] = None


@dataclass
class CollectionConfig:
    
	Name : str
	Indices : List[IndexConfig] = field(default_factory = list)
	Validator : Optional[Dict[str, Any]] = None
	Description : str = ""
    
	async def CreateIndices(self, Db : AsyncIOMotorDatabase):
		
		collection = Db[self.Name]
		
		for IndexConfig in self.Indices:
			
			if isinstance(IndexConfig.Keys, str):
			
				IndexKeys = [(IndexConfig.Keys, 1)]
			
			else:
			
				IndexKeys = IndexConfig.Keys
			
			# Building Index Options
			Options = {}
			
			if IndexConfig.Unique:
			
				Options['unique'] = True
			
			if IndexConfig.Sparse:
			
				Options['sparse'] = True
			
			if IndexConfig.TTLSeconds is not None:
			
				Options['expireAfterSeconds'] = IndexConfig.TTLSeconds
			
			if IndexConfig.Name:
			
				Options['name'] = IndexConfig.Name
			
			# Create index
			await collection.create_index(IndexKeys, **Options)
			

class MongoSchema:

	DailyAggregates = CollectionConfig \
	(
		Name = "DailyAggregates",
		Description = "Daily transaction aggregates by payment method",
		Indices = \
		[
			IndexConfig \
			(
				Keys = DailyAggregateDocumentKeyNames.Date.value,
				Name = "idx_date"
			),

			IndexConfig \
			(
				Keys = DailyAggregateDocumentKeyNames.Type.value,
				Name = "idx_type"
			),

			IndexConfig \
			(
				Keys = [(DailyAggregateDocumentKeyNames.Date.value, 1), (DailyAggregateDocumentKeyNames.Type.value, 1)],
				Name = "idx_date_type",
				Unique = True
			),
		],

		Validator = \
		{
			"$jsonSchema":
			{
				"bsonType": "object",
				"required": [DailyAggregateDocumentKeyNames.Date.value, DailyAggregateDocumentKeyNames.Type.value, DailyAggregateDocumentKeyNames.TotalAmount.value],
				"properties":
				{
					DailyAggregateDocumentKeyNames.Id.value:
					{
						"bsonType": "string",
						"description": "Composite key: date:type"
					},
					DailyAggregateDocumentKeyNames.Date.value:
					{
						"bsonType": "string",
						"pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
						"description": "Date in YYYY-MM-DD format"
					},
					DailyAggregateDocumentKeyNames.Type.value:
					{
						"bsonType": "string",
						"enum": ["deposits", "withdrawals"],
						"description": "Transaction type"
					},
					DailyAggregateDocumentKeyNames.TotalAmount.value:
					{
						"bsonType": "object",
						"description": "Payment method -> sum mapping",
						"additionalProperties":
						{
							"bsonType": "double"
						}
					},
					DailyAggregateDocumentKeyNames.LastUpdated.value:
					{
						"bsonType": "date",
						"description": "When this aggregate was last synced"
					}
				}
			}
		}
	)
    

async def InitializeSchema(Db: AsyncIOMotorDatabase):

	CollectionConfigs = \
	[
		MongoSchema.DailyAggregates,
	]

	for Config in CollectionConfigs:

		await Config.CreateIndices(Db)
