"""
FastAPI configurations for different stages of the project.

See:
    https://flask.palletsprojects.com/en/2.1.x/config/
    https://flask.palletsprojects.com/en/2.1.x/config/#builtin-configuration-values
    https://hackersandslackers.com/configure-flask-applications/

(c) Joao Galamba, 2023
$LICENSE(MIT)
"""

from os import environ
from logging import INFO, DEBUG as LOG_DEBUG, CRITICAL


__all__ = (
    'config_value',
    'conf',
    'ConfigError',
)


def strict_str_to_bool(value: str | None) -> bool:
    """
    Returns True only if value is 'TRUE' (*).
    Returns False only if value is 'FALSE' (*), '' or None.
    Raises a ConfigError for any other value.

    (*) - Accepts any case (eg, 'TRUE', 'tRuE', 'FALSE', 'fALsE', etc.)
    """
    if value is not None and value.upper() not in ('TRUE', 'FALSE', ''):
        raise ConfigError('Wrong boolean config value: {value}')
    return value is not None and value.upper() == 'TRUE'
#:

class Config:
    """
    Base config. Used just for defaults, which will be extracted from 
    environment variables and available via inheritance. Inspired on 
    the Flask documentation.

    See:
    https://flask.palletsprojects.com/en/2.1.x/quickstart/#sessions
    https://flask.palletsprojects.com/en/2.0.x/security/#security-cookie
    https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie
    """

    ENV = environ.get('ENV')
    TESTING = environ.get('TESTING')
    DEBUG = environ.get('DEBUG')
    LOG_LEVEL = environ.get('LOG_LEVEL')

    SESSION_SECRET_KEY = '8e10d234a1f8eb6f9dd6dfc3a325a0613ad2e620e5b8844cb011470492422bee'
    SESSION_COOKIE_NAME = 'session'
    SESSION_COOKIE_HTTPONLY = strict_str_to_bool(environ.get('SESSION_COOKIE_HTTPONLY'))
    SESSION_COOKIE_SECURE = strict_str_to_bool(environ.get('SESSION_COOKIE_SECURE'))
    SESSION_COOKIE_SAMESITE = environ.get('SESSION_COOKIE_SAMESITE')
    SESSION_COOKIE_MAX_AGE = int(
        60 if not environ.get('SESSION_COOKIE_MAX_AGE') else
        environ.get('SESSION_COOKIE_MAX_AGE')  # type: ignore
    )

    DATABASE_PROVIDER = environ.get('DATABASE_PROVIDER')
    DATABASE = environ.get('DATABASE')
    DATABASE_HOST = environ.get('DATABASE_HOST')
    DATABASE_USER = environ.get('DATABASE_USER')
    DATABASE_PASSWORD = environ.get('DATABASE_PASSWORD')

    STATIC_PATH = '/static'
    IMAGES_URL = f'{STATIC_PATH}/assets/img'
    INSTRUCTORS_IMAGES_URL = f'{IMAGES_URL}/instructors'
    COURSES_IMAGES_URL = f'{IMAGES_URL}/courses'

    TEMPLATES_PATH = './templates'
    ERROR_TEMPLATE_PATH = f'{TEMPLATES_PATH}/errors'

    GOOGLE_CLIENT_ID = environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_DISCOVERY_DOC_URL = 'https://accounts.google.com/.well-known/openid-configuration'
    GOOGLE_AUTH_URI = 'https://accounts.google.com/o/oauth2/auth'
    GOOGLE_TOKEN_URI = 'https://oauth2.googleapis.com/token'
    GOOGLE_SCOPE_REPLY = 'email openid https://www.googleapis.com/auth/userinfo.email'
    GOOGLE_JWKS_URI = 'https://www.googleapis.com/oauth2/v3/certs'
    GOOGLE_GRANT_TYPE =  'authorization_code'
    GOOGLE_ISS_URIS = ['https://accounts.google.com', 'accounts.google.com']
#:

class Development(Config):
    ENV = 'development'
    TESTING = True
    DEBUG = True
    LOG_LEVEL = LOG_DEBUG

    SESSION_COOKIE_NAME = 'devsession'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = 'lax'
    PERMANENT_SESSION_LIFETIME = 60

    DATABASE_PROVIDER = 'SQLite'
    DATABASE = 'data/courseca.db'

    # DATABASE = 'MySQL'
    # DATABASE = 'Courseca'
    # DATABASE_HOST = '192.168.56.104'
    # DATABASE_USER = 'admin'
    # DATABASE_PASSWORD = 'abc'

    GOOGLE_CLIENT_ID = '265995230960-fo60c2og6lrpqpm05aimk6c2q6a08vco.apps.googleusercontent.com'
    GOOGLE_CLIENT_SECRET = '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'
    GOOGLE_REDIRECT_URI = 'http://127.0.0.1:8000/extlogin/continue'
#:

class Production(Config):
    ENV = 'production'
    TESTING = False
    DEBUG = False
    LOG_LEVEL = INFO

    SESSION_COOKIE_NAME = 'prodsession'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'lax'
    PERMANENT_SESSION_LIFETIME = 86400_0  # in seconds (~10 days)

    # DATABASE = 'MySQL'
    # DATABASE = 'Courseca'
    # DATABASE_HOST = '192.168.56.104'
    # DATABASE_USER = 'admin'
    # DATABASE_PASSWORD = 'abc'

    # To be completed...
#:

_current_config = Development

def set_config_level(config_level: str):
    global _current_config
    _current_config = {
        'DEV': Development,
        'PROD': Production,
    }.get(config_level.upper())
    if not _current_config:
        raise ConfigError(f'Invalid configuration level {config_level}.')
    return _current_config
#:

def config_value(key: str):
    try:
        return getattr(_current_config, key)
    except AttributeError as ex:
        config_level = _current_config.__name__
        msg = f"Configuration parameter '{key}' not found in configuration '{config_level}'"
        raise ConfigError(msg) from ex
#:

conf = config_value

class ConfigError(Exception):
    pass
#;
