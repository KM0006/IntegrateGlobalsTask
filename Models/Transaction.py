
from typing import Self
from datetime import datetime
from pydantic import BaseModel
from Exceptions.Exceptions import CsvFileParsingException

class Transaction(BaseModel):

	Timestamp : datetime
	Type : str
	PaymentMethod : str
	Amount : float

	@classmethod
	def CreateFromStringList(self, StringList : list[str]) -> tuple[Self, int]:

		try:

			return self \
			(
				Timestamp = StringList[0].strip(),
				Type = StringList[1].strip(),
				PaymentMethod = StringList[2].strip(),
				Amount = StringList[3].strip(),
			), int(StringList[4].strip())
		
		except Exception as e:

			raise CsvFileParsingException()

class ImportedTransaction(Transaction):

	SleepTime : int
