import logging

logger = logging.getLogger('CTG')
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('ctg.log')
file_formatter = logging.Formatter(
    r'%(asctime)s\Function: %(funcName)s\Line: %(lineno)s\%(levelname)s\[file]\%(message)s',
)
file_handler.setFormatter(file_formatter)
file_handler.setLevel(logging.INFO)

logger.addHandler(file_handler)

std_handler = logging.StreamHandler()
std_formatter = logging.Formatter(
    r'%(asctime)s\%(levelname)s\%(message)s',
)
std_handler.setFormatter(std_formatter)
std_handler.setLevel(logging.DEBUG)

# logger.addHandler(std_handler)
