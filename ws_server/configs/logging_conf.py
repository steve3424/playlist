import os
from logging import Filter, LogRecord
from contextvars import ContextVar

IP_PORT: ContextVar[str] = ContextVar("ip_port", default="-")
BAND: ContextVar[str] = ContextVar("band", default="-")
USER_NAME: ContextVar[str] = ContextVar("user_name", default="-")

LOG_FILE_DIR = os.path.join(os.path.dirname(__file__), os.pardir, "logs")
LOG_FILE_NAME = os.path.join(LOG_FILE_DIR, "playlist.log")
os.makedirs(LOG_FILE_DIR, exist_ok=True)

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
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": { 
        "standard": { 
            "format": "[%(levelname)s] [%(ip_port)s][%(band)s][%(user_name)s] %(asctime)s %(name)s: %(message)s"
        },
    },
    "filters": {
        "trace_filter": {
          "()" : TraceFilter,
        }
    },
    "handlers": { 
        "stderr": { 
            "level": "DEBUG",
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
            "filters": ["trace_filter"]
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "standard",
            "filename": LOG_FILE_NAME,
            "mode": "a",
            "maxBytes": 1024*1024*10,
            "backupCount": 5,
            "filters": ["trace_filter"]
        },
    },
    "loggers": { 
        "playlist": {
            "handlers": [
                "stderr",
                "file"
            ],
            "level": "DEBUG",
            "propagate": False
        },
        "websockets.server": {
            "handlers": [
                "stderr",
                "file"
            ],
            "level": "INFO",
            "propagate": False
        },
    } 
}
