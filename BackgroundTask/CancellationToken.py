
class CancellationToken:

	def __init__(self):

		self.__IsCancelled = False

	def IsCancelled(self):

		return self.__IsCancelled
	
	def Cancel(self):

		self.__IsCancelled = True