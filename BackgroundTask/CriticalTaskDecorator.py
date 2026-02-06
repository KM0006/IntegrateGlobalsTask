
import sys
from typing import Callable, Any
from tenacity import retry, stop_after_attempt, wait_exponential

def CriticalTask(StopAttemptCount: int = 3, ExponentialWaitMultiplier: float = 1.0, MinWaitTimeSeconds: float = 1.0, MaxWaitTimeSeconds: float = 10.0):

	def decorator(func: Callable):
		@retry \
		(
			stop = stop_after_attempt(StopAttemptCount),
			wait = wait_exponential(multiplier = ExponentialWaitMultiplier, min = MinWaitTimeSeconds, max = MaxWaitTimeSeconds),
			reraise = True
		)
		async def AsyncWrapper(*args: Any, **kwargs: Any):
		
			return await func(*args, **kwargs)
		
		async def ExitAfterRetryWrapper(*args: Any, **kwargs: Any):
		
			try:
		
				return await AsyncWrapper(*args, **kwargs)
			
			except Exception as e:
				
				sys.exit(1)
		
		return ExitAfterRetryWrapper

	return decorator