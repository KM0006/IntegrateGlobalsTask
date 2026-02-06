
import sys
import asyncio
import logging

from fastapi import FastAPI
from AppConfig import AppConfig
from redis.asyncio import Redis
from motor.motor_asyncio import AsyncIOMotorDatabase
from AppBuilder.AppStateBuilder import AppStateBuilder
from BackgroundTask.CancellationToken import CancellationToken

logger = logging.getLogger("uvicorn")

class AppBuilder():

	@staticmethod
	async def Initialize(App : FastAPI, AppConfig : AppConfig, CancellationToken : CancellationToken):

		AppStateBuilder().BuildAppState(App, AppConfig = AppConfig, CancellationToken = CancellationToken)


	@staticmethod
	async def GracefulShutdown(App : FastAPI, AppConfig : AppConfig):
		
		await asyncio.gather \
		(
			AppBuilder.GracefulBackGroundTasksShutDown(App, AppConfig),
			AppBuilder.GracefulRedisShutDown(App, AppConfig),
			AppBuilder.GracefulMongoDbShutDown(App, AppConfig)
		)


	@staticmethod
	async def ForceShutdown(App : FastAPI, AppConfig : AppConfig):

		await asyncio.gather \
		(
			AppBuilder.ForceBackGroundTasksShutDown(App, AppConfig),
			AppBuilder.ForceRedisShutDown(App, AppConfig),
			AppBuilder.ForceMongoDbShutDown(App, AppConfig)
		)

	@staticmethod
	async def GracefulBackGroundTasksShutDown(App : FastAPI, AppConfig : AppConfig):

		# Cancel all tasks
		# Method designed to be called after calling CancellationToken.Cancel(), which cancels all schecduled tasks forcing the task to be done

		BackgroundTaskList = App.state.BackgroundTasks

		if not BackgroundTaskList:

			return


		for Task in BackgroundTaskList:

			if not Task.done():
			
				Task.cancel()
		
		try:

			# Wait for cancellation to complete
			Results = await asyncio.wait_for(asyncio.gather(*BackgroundTaskList, return_exceptions = True), timeout = AppConfig.GracefulShutDownTimeout)

			for Task, Result in zip(BackgroundTaskList, Results):

				if isinstance(Result, asyncio.CancelledError):

					logger.info(f"✅ {Task.get_name()} was Cancelled.")

				elif isinstance(Result, Exception):

					logger.info(f"⚠️ {Task.get_name()} error: {Result}.")

				else:

					logger.info(f"✅ {Task.get_name()} Finished and shutdown completely.")

		except asyncio.TimeoutError:

			return

	@staticmethod
	async def GracefulRedisShutDown(App : FastAPI, AppConfig : AppConfig):

		Redis : Redis = App.state.Redis

		if Redis is None:

			return

		try:
		
			await asyncio.wait_for(Redis.close(), timeout = AppConfig.GracefulShutDownTimeout)
			
			logger.info("✅ Redis connection closed")
		
		except Exception as e:
			
			logger.info(f"⚠️ Error closing Redis: {e}")

	@staticmethod
	async def GracefulMongoDbShutDown(App : FastAPI, AppConfig : AppConfig):

		MongoDb : AsyncIOMotorDatabase = App.state.MongoDb

		if MongoDb is None:

			return

		try:
		
			# MongoDb close method is synchronous
			MongoDb.client.close()
			
			logger.info("✅ MongoDb connection closed")
		
		except Exception as e:
			
			logger.info(f"⚠️  MongoDb closing failed: {e}")

	@staticmethod
	async def ForceBackGroundTasksShutDown(BackgroundTasks : list[asyncio.Task], AppConfig : AppConfig):

		for Task in BackgroundTasks:

			if not Task.done():
				
				Task.cancel()

		sys.exit(1)

	@staticmethod
	async def ForceRedisShutDown(App : FastAPI, AppConfig : AppConfig):

		Redis : Redis = App.state.Redis

		if Redis is None:

			return

		try:
		
			await Redis.close()
			
			logger.info("✅ Redis connection closed")
		
		except Exception as e:
			
			logger.info(f"⚠️ Error closing Redis: {e}")
			sys.exit(1)

	@staticmethod
	async def ForceMongoDbShutDown(App : FastAPI, AppConfig : AppConfig):

		MongoDb : AsyncIOMotorDatabase = App.state.MongoDb

		if Redis is None:

			return

		try:
		
			MongoDb.client.close()
			
			logger.info("✅ MongoDb connection closed")
		
		except Exception as e:
			
			logger.info(f"⚠️ Error closing MongoDb: {e}")
			sys.exit(1)

		
 