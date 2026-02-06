
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppConfig(BaseSettings):
    
	model_config = SettingsConfigDict \
	(
		env_file = ".env",
		env_file_encoding = "utf-8",
		case_sensitive = False,
		extra = "ignore"
	)
		
	RedisHost : str
	RedisPort : str
	RedisTransactionQueueKeyName : str

	CsvFilePath : str

	MongoDbUri : str

	TransactionCkeckTimeout : float

	GracefulShutDownTimeout : int

	ForceShutDownTimeout : int

	CutOffSeconds : int
	
	CutOffMinutes : int

	CutOffDays : int

	DumperTaskScheduleInterval : int

	MongoDbName : str = "TransactionsDb"

@lru_cache()
def GetAppConfig() -> AppConfig:
	return AppConfig()

