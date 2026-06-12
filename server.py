import logging
import traceback

# Patch para ver el traceback completo
original_excepthook = None

class DetailedFormatter(logging.Formatter):
    def formatException(self, exc_info):
        return ''.join(traceback.format_exception(*exc_info))

logging.basicConfig(level=logging.DEBUG)
for handler in logging.root.handlers:
    handler.setFormatter(DetailedFormatter())
