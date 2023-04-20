from contextvars import ContextVar
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi import UploadFile
from fastapi.datastructures import FormData
from starlette.datastructures import UploadFile as StarletteUploadFile


__all__ = (
    'global_request',
    'add_global_request_middleware',
    'form_field_as_str',
    'form_field_as_file',
    'upload_file_closing',
)


global_request : ContextVar[Request] = ContextVar("global_request")

def add_global_request_middleware(app: FastAPI):
    # https://fastapi.tiangolo.com/tutorial/middleware/#middleware
    @app.middleware('http')
    async def global_request_middleware(request: Request, call_next):
        global_request.set(request)
        response = await call_next(request)
        return response
    #:
#:

def form_field_as_str(form_data: FormData, field_name: str) -> str:
    field_value = form_data[field_name]
    if isinstance(field_value, str):
        return field_value
    raise TypeError(f'Form field {field_name} type is not str')
#:

def form_field_as_file(form_data: FormData, field_name: str) -> StarletteUploadFile:
    field_value = form_data[field_name]
    if isinstance(field_value, StarletteUploadFile):
        return field_value
    err_msg = f'Form field {field_name} type is not {StarletteUploadFile.__name__}'
    raise TypeError(err_msg)
#:

@asynccontextmanager
async def upload_file_closing(
    file_obj: UploadFile | StarletteUploadFile
) -> AsyncGenerator[UploadFile | StarletteUploadFile, None]:
    try:
        yield file_obj
    finally:
        await file_obj.close()
#:
