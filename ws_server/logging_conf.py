from logging import Filter, LogRecord
from contextvars import ContextVar

IP_PORT: ContextVar[str] = ContextVar("ip_port", default="-")
BAND: ContextVar[str] = ContextVar("band", default="-")
USER_NAME: ContextVar[str] = ContextVar("user_name", default="-")

class TraceFilter(Filter):
    def __init__(self):
        super().__init__()

    def filter(self, log_record: LogRecord) -> bool:
        global IP_PORT
        global BAND
        global USER_NAME
        log_record.ip_port = IP_PORT.get()
        log_record.band = BAND.get()
        log_record.user_name = USER_NAME.get()
        return True

LOGGING_CONFIG = { 
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': { 
        'standard': { 
            'format': '[%(ip_port)s][%(band)s][%(user_name)s] [%(levelname)s] %(asctime)s %(name)s: %(message)s'
        },
    },
    'filters': {
        'trace_filter': {
          '()' : TraceFilter,
        }
    },
    'handlers': { 
        'stderr': { 
            'level': 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stderr',
            'filters': ['trace_filter']
        },
    },
    'loggers': { 
        'ws_server': {
            'handlers': [
                'stderr'
            ],
            'level': 'DEBUG',
            'propagate': False
        },
        'websockets.server': {
            'handlers': [
                'stderr'
            ],
            'level': 'INFO',
            'propagate': False
        },
    } 
}
