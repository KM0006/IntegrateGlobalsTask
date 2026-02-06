
import sys
import logging
import asyncio

from fastapi import FastAPI
from redis.asyncio import Redis
from AppConfig import AppConfig
from BackgroundTask.DataDumper import DataDumper
from BackgroundTask.DataImporter import DataImporter
from BackgroundTask.DataAggregator import DataAggregator
from BackgroundTask.CancellationToken import CancellationToken
from motor.motor_asyncio import AsyncIOMotorDatabase as MongoDb
from motor.motor_asyncio import AsyncIOMotorClient as MongoDbClient

class AppStateBuilder:

	def BuildAppState(self, App : FastAPI,  AppConfig : AppConfig, CancellationToken : CancellationToken):

		self.BuildRedis(App, AppConfig)

		self.BuildMongoDb(App, AppConfig)

		self.BuildBackgroundTasks(App, AppConfig, CancellationToken)

	def BuildRedis(self, App : FastAPI, AppConfig : AppConfig):

		App.state.Redis = Redis(host = AppConfig.RedisHost, port = AppConfig.RedisPort)

	def BuildMongoDb(self, App : FastAPI, AppConfig : AppConfig):

		App.state.MongoDb = MongoDb(MongoDbClient(AppConfig.MongoDbUri), name = AppConfig.MongoDbName)

	def BuildBackgroundTasks(self, App : FastAPI, AppConfig : AppConfig, CancellationToken : CancellationToken):

		App.state.BackgroundTasks = \
		[
			asyncio.create_task \
			(
				DataImporter.ImportData \
				(
					App.state.Redis,
					AppConfig.CsvFilePath,
					AppConfig.RedisTransactionQueueKeyName
				)
			),
			asyncio.create_task \
			(
				DataAggregator.AggregateData \
				(
					App.state.Redis,
					AppConfig.RedisTransactionQueueKeyName,
					AppConfig.TransactionCkeckTimeout,
					CancellationToken
				)
			),
			asyncio.create_task \
			(
				DataDumper.DumpData \
				(
					App.state.Redis,
					App.state.MongoDb,
					AppConfig.DumperTaskScheduleInterval,
					CancellationToken
				)
			)
		]

