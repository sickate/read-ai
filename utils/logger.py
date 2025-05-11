import logging
import sys

class FileLineFormatter(logging.Formatter):
    def format(self, record):
        record.filename = record.filename if record.filename else 'N/A'
        record.lineno = record.lineno if record.lineno else 'N/A'
        return super().format(record)

# Set up logging
def setup_logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    formatter = FileLineFormatter('%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
    handler.setFormatter(formatter)
    logger.handlers = []  # Remove all existing handlers
    logger.addHandler(handler)  # Add the new handler
    return logger


def setup_logger_level(verbose):
    log_levels = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']
    log_level = log_levels[min(verbose, len(log_levels) - 1) + 3]
    logger = setup_logger('read-ai', level=log_level)
    logger.info(f'Logger level set to {log_level}')
    return logger

