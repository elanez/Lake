'''
DEBUG: These are used to give Detailed information, typically of interest only when diagnosing problems.
INFO: These are used to confirm that things are working as expected
WARNING: These are used an indication that something unexpected happened, or is indicative of some problem 
in the near future
ERROR: This tells that due to a more serious problem, the software has not been able to perform some function
CRITICAL: his tells serious error, indicating that the program itself may be unable to continue running
'''

import logging

logger = logging.getLogger('logs')
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('debug.log')
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

def getLogger():
    return logger