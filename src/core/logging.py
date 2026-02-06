import logging
import sys


class LoggerFactory:
    _initialized: bool = False
    _log_level: int = logging.INFO
    _log_format: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    _date_format: str = "%Y-%m-%d %H:%M:%S"

    @classmethod
    def configure(
        cls,
        level: int = logging.INFO,
        log_format: str | None = None,
        date_format: str | None = None,
    ) -> None:
        cls._log_level = level

        if log_format:
            cls._log_format = log_format

        if date_format:
            cls._date_format = date_format

        logging.basicConfig(
            level=cls._log_level,
            format=cls._log_format,
            datefmt=cls._date_format,
            handlers=[logging.StreamHandler(sys.stdout)],
        )
        cls._initialized = True

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        if not cls._initialized:
            cls.configure()

        logger = logging.getLogger(name)

        return logger


def get_logger(name: str) -> logging.Logger:
    return LoggerFactory.get_logger(name)
