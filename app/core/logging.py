import logging
import sys
from loguru import logger
from app.core.config import settings


class InterceptHandler(logging.Handler):
	"""
	Interceptor handler to route standard logging to loguru
	"""
	
	def emit(
		self,
		record
	):
		# Get corresponding Loguru level if it exists
		try:
			level = logger.level(record.levelname).name
		except ValueError:
			level = record.levelno
		
		# Find caller from where originated the logged message
		frame, depth = logging.currentframe(), 2
		while frame.f_code.co_filename == logging.__file__:
			frame = frame.f_back
			depth += 1
		
		logger.opt(depth=depth, exception=record.exc_info).log(
			level, record.getMessage()
		)


def setup_logging():
	"""Configure logging with loguru"""
	# Remove all existing handlers
	logging.root.handlers = []
	
	# Set minimum level
	logging.root.setLevel(settings.LOG_LEVEL)
	
	# Add intercept handler
	logging.root.addHandler(InterceptHandler())
	
	# Configure loguru
	logger.configure(
		handlers=[
			{
				"sink": sys.stdout,
				"format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
				"level": settings.LOG_LEVEL,
			}
		]
	)
	
	# Intercept everything at the root logger
	for name in logging.root.manager.loggerDict.keys():
		logging.getLogger(name).handlers = []
		logging.getLogger(name).propagate = True
