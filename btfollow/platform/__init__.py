import sys
from loguru import logger
import importlib
from typing import Any


def get_interface() -> Any:
    module_path = f"{__name__}.{sys.platform}"
    logger.debug(f"Loading module: {module_path}")
    module = importlib.import_module(module_path)
    logger.debug(f"Module loaded: {module}")
    return module

