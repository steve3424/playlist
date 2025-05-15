from logging import Filter, LogRecord
from contextvars import ContextVar

IP_PORT: ContextVar[str] = ContextVar("ip_port", default="-")
BAND: ContextVar[str] = ContextVar("band", default="-")
USER_ID: ContextVar[str] = ContextVar("user_id", default="-")

class TraceFilter(Filter):
    def __init__(self):
        super().__init__()

    def filter(self, log_record: LogRecord) -> bool:
        global IP_PORT
        global BAND
        global USER_ID
        log_record.ip_port = IP_PORT.get()
        log_record.band = BAND.get()
        log_record.user_id = USER_ID.get()
        return True

LOGGING_CONFIG = { 
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': { 
        'standard': { 
            'format': '[%(ip_port)s][%(band)s][%(user_id)s] [%(levelname)s] %(asctime)s %(name)s: %(message)s'
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
