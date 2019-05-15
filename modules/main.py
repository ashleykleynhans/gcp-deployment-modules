"""Deploy the selected module."""
import importlib
import logging
import sys

LOGGER = logging.getLogger(__name__)


if __name__ == "__main__":
    module_number = sys.argv[1]

    LOGGER.info(f'importing module: {module_number}')

    module_name = f'module_{module_number}.module'

    file_module = importlib.import_module(module_name)

    try:
        module_class = getattr(file_module, f'Module')

        instance = module_class()

    except AttributeError as exc:
        LOGGER.error(f'Could not load module {module_name}')
