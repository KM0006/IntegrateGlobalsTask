
import asyncio
import logging
import aiofiles

from redis.asyncio import Redis
from Models.Transaction import Transaction
from BackgroundTask.CriticalTaskDecorator import CriticalTask

logger = logging.getLogger('uvicorn')

class DataImporter:

	@staticmethod
	@CriticalTask()
	async def ImportData(Redis : Redis, FilePath : str, QueueListKey : str):

		Line = None

		async with aiofiles.open(FilePath, "r") as CsvTransactionsFile:

			# Skip first line of csv file (Column Names)
			await CsvTransactionsFile.readline()
			
			while(True):

				Line = await CsvTransactionsFile.readline()

				if (not Line):

					break

				TransactionString = Line.split(',')
				
				TransactionData, SleepTime = Transaction.CreateFromStringList(TransactionString)

				await Redis.lpush(QueueListKey, TransactionData.model_dump_json())

				await asyncio.sleep(SleepTime / 1000)

		logger("✅ Data Imported Successfully from CSV File")
