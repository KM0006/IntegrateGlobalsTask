
from pydantic import BaseModel
from typing import Dict, Self, List
from Models.DailyAggregate import DailyAggregate

class ApiDailyAggregateResponse(BaseModel):

	data: Dict[str, Dict[str, Dict[str, float]]]

	def MapFromDailyAggregateList(DailyAggregateList : List[DailyAggregate]) -> Self:

		# DepositTotalAmount = Daily

		ApiDailyAggregateResponseDict = {}

		for DailyAggregateItem in DailyAggregateList:

			if DailyAggregateItem.Date not in ApiDailyAggregateResponseDict.keys():
			
				ApiDailyAggregateResponseDict[DailyAggregateItem.Date] = {}

			if DailyAggregateItem.Type not in ApiDailyAggregateResponseDict[DailyAggregateItem.Date].keys():

				ApiDailyAggregateResponseDict[DailyAggregateItem.Date][DailyAggregateItem.Type] = {}

			ApiDailyAggregateResponseDict[DailyAggregateItem.Date][DailyAggregateItem.Type] = DailyAggregateItem.TotalAmount

		return ApiDailyAggregateResponse(data = ApiDailyAggregateResponseDict)
			