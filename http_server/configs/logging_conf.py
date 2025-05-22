from logging import Filter, LogRecord
from contextvars import ContextVar

IP_ADDRESS: ContextVar[str] = ContextVar("ip_address", default="-")
ENDPOINT: ContextVar[str] = ContextVar("endpoint", default="-")
USER_NAME: ContextVar[str] = ContextVar("user_name", default="-")
REQUEST_ID: ContextVar[str] = ContextVar("request_id", default="-")

class TraceFilter(Filter):
    def __init__(self):
        super().__init__()

    def filter(self, log_record: LogRecord) -> bool:
        global IP_ADDRESS
        global ENDPOINT
        global USER_NAME
        log_record.ip_address = IP_ADDRESS.get()
        log_record.endpoint = ENDPOINT.get()
        log_record.user_name = USER_NAME.get()
        log_record.request_id = REQUEST_ID.get()
        return True

LOGGING_CONFIG = { 
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": { 
        "standard": { 
            "format": "[%(levelname)s] [%(ip_address)s][%(endpoint)s][%(user_name)s][%(request_id)s] %(asctime)s %(name)s: %(message)s"
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
    },
    "loggers": { 
        "playlist": {
            "handlers": [
                "stderr"
            ],
            "level": "DEBUG",
            "propagate": False
        },
        "uvicorn.error": {
            "handlers": [
                "stderr"
            ],
            "level": "INFO",
            "propagate": False
        },
    } 
}