LOGGING_CONFIG = { 
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': { 
        'standard': { 
            'format': '[%(levelname)s] %(asctime)s %(name)s: %(message)s'
        },
    },
    'handlers': { 
        'stderr': { 
            'level': 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stderr',
        },
    },
    'loggers': { 
        '__main__': {
            'handlers': [
                'stderr'
            ],
            'level': 'DEBUG',
            'propagate': False
        },
    } 
}