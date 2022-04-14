'''
DEBUG: These are used to give Detailed information, typically of interest only when diagnosing problems.
INFO: These are used to confirm that things are working as expected
WARNING: These are used an indication that something unexpected happened, or is indicative of some problem 
in the near future
ERROR: This tells that due to a more serious problem, the software has not been able to perform some function
CRITICAL: his tells serious error, indicating that the program itself may be unable to continue running
'''
import logging

class Logger:
    def __init__(self, name, file_name):
        self._logger = logging.getLogger(name)
        self._file_handler = logging.FileHandler(file_name)
        self._configure()
    
    def _configure(self):
        self._logger.setLevel(logging.INFO)
        self._file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self._file_handler.setFormatter(formatter)

        self._logger.addHandler(self._file_handler)

    '''
    LOG MESSAGE
    '''
    def log_debug(self, message):
        self._logger.debug(message)
    
    def log_info(self, message):
        self._logger.info(message)

    def log_warning(self, message):
        self._logger.warning(message)

    def log_error(self, message):
        self._logger.error(message)

    def log_critical(self, message):
        self._logger.critical(message)