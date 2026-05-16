import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """Configure structured-enough logs for local and container use."""

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
