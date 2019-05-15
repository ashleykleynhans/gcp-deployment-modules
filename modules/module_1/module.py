import logging

from module_base.module_base import ModuleBase

LOGGER = logging.getLogger(__name__)


class Module(ModuleBase):
    """Module class to do some lofic."""

    def __init__(self):
        print('Loading Module 1')
        super(Module, self).__init__()

    def do_some_processing(self):
        # TODO: Add some awesome logic here 
        return {
            "data": "some dummy data"        
        }
