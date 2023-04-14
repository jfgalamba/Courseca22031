from hashlib import sha512
from typing import Any
from fastapi import FastAPI, HTTPException

from fastapi.requests import Request
from fastapi.responses import Response
from fastapi import status
# from starlette_session import SessionMiddleware
from starlette.middleware.sessions import SessionMiddleware

from config_settings import config_value
from data.models import Student
from services import students_service
from common.fastapi_utils import global_request
from common.common import secure_random_str


__all__ = (
    'requires_authentication',
    'requires_unauthentication',
    'get_current_user',
    'get_session',
    'session_cookie_set_user_id',
    'get_auth_from_cookie',
    'delete_auth_cookie',
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
        # cookie_name = SESSION_COOKIE_NAME,
        session_cookie = SESSION_COOKIE_NAME,
        secret_key = SESSION_SECRET_KEY,
        same_site = SESSION_COOKIE_SAMESITE,
        https_only = SESSION_COOKIE_SECURE,
        max_age = SESSION_COOKIE_MAX_AGE,
    )
#:

def get_current_user() -> Student | None:
    if student_id := get_auth_from_cookie(global_request.get()):
        return students_service.get_student_by_id(student_id)
    return None
#:

def get_session(session_attr = 'session') -> Any:
    request = global_request.get()
    return getattr(request, session_attr)
#:

def session_cookie_set_user_id(response: Response, user_id: int):
    request = global_request.get()
    request.session['user_id'] = user_id
    # request.session['user_id'] = str(user_id)
    # session_id = secure_random_str(SESSION_ID_LEN)
    # hash_token = hash_cookie_value(f'{user_id}{session_id}')
    # cookie_value = f'{user_id}:{session_id}:{hash_token}'
    # response.set_cookie(
    #     SESSION_COOKIE_NAME, 
    #     cookie_value, 
    #     secure = SESSION_COOKIE_SECURE, 
    #     httponly = SESSION_COOKIE_HTTPONLY, 
    #     samesite = SESSION_COOKIE_SAMESITE,
    #     max_age = SESSION_COOKIE_MAX_AGE,
    # )
#:

def get_auth_from_cookie(request: Request | None = None) -> int | None:
    if request is None:
        request  = global_request.get()
    user_id = request.session.get('user_id')
    if isinstance(user_id, int):
        return user_id
    return None

    # if parts := get_from_cookie(request):
    #     user_id_str = parts[0]
    #     if user_id_str.isdigit():
    #         return int(user_id_str)
    # return None
#:

#     if parts := get_from_cookie(request):
#         return parts[1]
#     return None
# #:

# def get_from_cookie(request: Request) -> list[str] | None:
#     if not (cookie_value := request.cookies.get(SESSION_COOKIE_NAME)):
#         return None

#     parts = cookie_value.split(':')
#     if len(parts) != 3:
#         return None

#     user_id, session_id, hash_value = parts
#     hash_value_check = hash_cookie_value(f'{user_id}{session_id}')
#     if hash_value != hash_value_check:
#         print("Warning: hash mismatch. Invalid cookie value!")
#         return None

#     return parts
# #:

def delete_auth_cookie(response: Response):
    request = global_request.get()
    del request.session['user_id']
    # response.delete_cookie(SESSION_COOKIE_NAME)
#:

def hash_cookie_value(value: str) -> str:
    return sha512(f'{value}{SESSION_SECRET_KEY}'.encode('utf-8')).hexdigest()
#:
