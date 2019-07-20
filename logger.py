import os
import yaml
import json
import logging
import logging.config

default_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {name} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {name} {message}',
            'style': '{',
        },
    },
    'filters': {
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': [],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        }
    },
    'root': {
        'propagate': True,
        'handlers': ['console'],
        'level': 'INFO',
    }
}

def get_logging_config(
        config_path='logging.yaml',
        config_format='YAML',
        default_level=logging.INFO, 
        env_key='LOG_CFG',
        *args,
        **kw):
    
    if os.path.exists(config_path):
        with open(config_path, 'rt') as f:
            try:
                if config_format.upper() == 'YAML':
                    return yaml.safe_load(f.read())
                elif config_format.upper() == 'JSON':
                    return json.loads(f.read())  
            except Exception as e:
                print(e)
                print('Error in logging configuration file: {file} Using default configs'.format(file=config_path))
                return default_config
    else:
        return default_config
    
def configure_logging(*args, **kw):
    logging.config.dictConfig(get_logging_config(*args, **kw))
    
    
    
