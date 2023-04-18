from hashlib import sha512
from typing import Any
from fastapi import FastAPI, HTTPException

from fastapi.requests import Request
from fastapi.responses import Response
from fastapi import status
from starlette.middleware.sessions import SessionMiddleware

from config_settings import config_value
from data.models import Student
from services import students_service
from common.fastapi_utils import global_request


__all__ = (
    'requires_authentication',
    'requires_unauthentication',
    'get_session',
    'get_current_user',
    'set_current_user',
    'remove_current_user',
)


SESSION_COOKIE_NAME = config_value('SESSION_COOKIE_NAME')
SESSION_SECRET_KEY = config_value('SESSION_SECRET_KEY')
SESSION_COOKIE_HTTPONLY = config_value('SESSION_COOKIE_HTTPONLY')
SESSION_COOKIE_SECURE = config_value('SESSION_COOKIE_SECURE')
SESSION_COOKIE_SAMESITE = config_value('SESSION_COOKIE_SAMESITE')
SESSION_COOKIE_MAX_AGE = config_value('SESSION_COOKIE_MAX_AGE')
SESSION_ID_LEN = 64   # in chars

# SESSION_COOKIE_MAX_AGE = 86400_00    # in seconds (~100 days)
# SESSION_COOKIE_MAX_AGE = 30    # in seconds


# NOTE: These classes won't be suffixed with 'Exception' or 'Error',
# because they aren't necessarily exceptions/errors. They are used for
# control flow. Yes, exceptions shouldn't be used for this, but there's
# no clean way to protect access to a view without raising an exception.
# Besides, using exceptions as a control flow mechanism is often used in
# Python built-ins and libraries (eg, StopIteration)

class HTTPUnauthorizedAccess(HTTPException):
    def __init__(self, *args, **kargs):
        super().__init__(status_code = status.HTTP_401_UNAUTHORIZED, *args, **kargs)
#:

class HTTPUnauthenticatedOnly(HTTPUnauthorizedAccess):
    pass
#:

def requires_authentication():
    if not get_current_user():
        raise HTTPUnauthorizedAccess(detail = 'This area requires authentication.')
#:

def requires_unauthentication():
    if get_current_user():
        raise HTTPUnauthenticatedOnly(detail = 'This is a public area only.')
#:

def add_session_middleware(app: FastAPI):
    app.add_middleware(
        SessionMiddleware,
        session_cookie = SESSION_COOKIE_NAME,
        secret_key = SESSION_SECRET_KEY,
        same_site = SESSION_COOKIE_SAMESITE,
        https_only = SESSION_COOKIE_SECURE,
        max_age = SESSION_COOKIE_MAX_AGE,
    )
#:

def get_session(session_attr = 'session') -> Any:
    request = global_request.get()
    return getattr(request, session_attr)
#:

def get_current_user(request: Request | None = None) -> Student | None:
    if request is None:
        request  = global_request.get()
    user_id = request.session.get('user_id')
    if isinstance(user_id, int):
        return students_service.get_student_by_id(user_id)
    return None
#:

def set_current_user(user_id: int):
    request = global_request.get()
    request.session['user_id'] = user_id
#:

def remove_current_user():
    request = global_request.get()
    del request.session['user_id']
#:
