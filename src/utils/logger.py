import logging

def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger once with handlers/formatters."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if not root_logger.hasHandlers():
        ch = logging.StreamHandler()
        ch.setLevel(level)

        formatter = logging.Formatter("[%(name)s] %(levelname)s: %(message)s")
        ch.setFormatter(formatter)

        root_logger.addHandler(ch)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)
