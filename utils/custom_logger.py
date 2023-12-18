import logging
import threading


class SingletonMeta(type):
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
            return cls._instances[cls]


class Logger(metaclass=SingletonMeta):
    def __init__(self):
        self.logger = logging.getLogger("Loggy-The-Logger")
        self.logger.setLevel(logging.DEBUG)

        # Create handlers (e.g., console and file handlers)
        console_handler = logging.StreamHandler()
        file_handler = logging.FileHandler("logs/dump.log")

        # Create formatters and add it to handlers
        formatter = logging.Formatter(
            "%(asctime)s | %(name)s [%(levelname)s] - %(message)s"
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # Add handlers to the logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def get_logger(self):
        return self.logger

    @staticmethod
    def set_level(level: int):
        logging.getLogger("Loggy-The-Logger").setLevel(level)
