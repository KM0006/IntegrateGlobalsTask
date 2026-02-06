
from redis.asyncio import Redis
from Models.Transaction import Transaction
from HelperMethods import GetRedisKeyDesign, GetDayDateFormat
from BackgroundTask.CriticalTaskDecorator import CriticalTask
from BackgroundTask.CancellationToken import CancellationToken

class DataAggregator:

	@staticmethod
	@CriticalTask()
	async def AggregateData(Redis : Redis, TransactionQueueKey : str, TransactionCkeckTimeout : float, CancellationToken : CancellationToken):

		while (not CancellationToken.IsCancelled()):
				
			RedisStoredTransaction = await Redis.brpop(TransactionQueueKey, timeout = TransactionCkeckTimeout)
			
			if RedisStoredTransaction is None:
				
				continue
			
			_, TransactionJson = RedisStoredTransaction
			TransactionModel : Transaction = Transaction.model_validate_json(TransactionJson)
			
			Day = TransactionModel.Timestamp.strftime(GetDayDateFormat())
			TransactionType = TransactionModel.Type
			PaymentMethod = TransactionModel.PaymentMethod
			Amount = float(TransactionModel.Amount)

			RedisKey = GetRedisKeyDesign(Day, TransactionType)
			
			await Redis.hincrbyfloat(RedisKey, PaymentMethod, Amount)
