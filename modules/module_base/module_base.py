import os
import logging
import time

LOGGER = logging.getLogger(__name__)

MODULE_NUMBER = os.environ.get('MODULE_NUMBER')


class ModuleBase(object):
    """Base class that will serve as bases for all module."""
    source_address = '127.0.0.1'
    keep_processing = True
    process_interval = 60  # Seconds
    
    def __init__(self):
        LOGGER.info('Loading module...')
        self.config()

        while self.keep_processing:
            LOGGER.info("Start processing")
            print(self.do_some_processing())

            LOGGER.info(f"Sleep for {self.process_interval} seconds")
            time.sleep(self.process_interval)

    def config(self):
        if not MODULE_NUMBER:
            raise Exception("Module number not specified.")

    def do_some_processing(self, **kwargs):
        pass
