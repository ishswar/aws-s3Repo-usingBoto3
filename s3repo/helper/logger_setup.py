import logging
import sys

LOG_LEVEL = logging.DEBUG
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

# create a file handler
handler = logging.FileHandler('s3repo/logs/s3repo.log')
handler.setLevel(LOG_LEVEL)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)s - %(funcName)10s() ] '
                              '- %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)

consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setLevel(LOG_LEVEL)
consoleHandler.setFormatter(formatter)
logging.getLogger().addHandler(consoleHandler)
