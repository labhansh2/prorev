import logging
import logging.handlers
import pathlib
import sys
import os


class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)-16s - %(levelname)-8s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logging(log_level=logging.WARNING):
    logger = logging.getLogger()
    logger.setLevel(log_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    if hasattr(sys, "_MEIPASS"):
        # Running as executable
        # base_path = sys._MEIPASS
        base_path = os.path.dirname(sys.executable)
        path = os.path.join(base_path, "logs")
        log_file_path = pathlib.Path(path)
        # print(log_file_path)
    else:
        # Running as script
        log_file_path = pathlib.Path(__file__).parent/f"../logs/"

    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file_path/'logfile.log', maxBytes=102400 * 2, backupCount=5)
    file_handler.setLevel(log_level)
    file_handler.namer = lambda name: name.replace(".log", "") + ".log"

    console_handler.setFormatter(CustomFormatter())
    file_handler.setFormatter(CustomFormatter())

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    included_loggers = [
        'prorev',
        '__main__',
        'data',
        'notification',
        'rev_model',
        'Notion'
    ]

    for logger_name in included_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)

    # Disable log messages from imported libraries
    excluded_loggers = [
        'notion_client',
        'httpcore',
        'httpx',
        'requests',
        'urllib3',
    ]

    for logger_name in excluded_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)
        logger.propagate = False
