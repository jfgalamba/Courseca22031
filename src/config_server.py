import os

from fastapi import (
    FastAPI, 
    responses,
    status,
)
from fastapi.staticfiles import StaticFiles

from fastapi_chameleon import global_init
from chameleon import PageTemplateFile

from config_settings import (
    config_value,
    set_config_level,
)
from common.fastapi_utils import (
    add_global_request_middleware,
)
from common.auth import (
    HTTPUnauthenticatedOnly,
    HTTPUnauthorizedAccess,
    add_session_middleware,
)
from common.viewmodel import ViewModel
from views import (
    home,
    courses,
    account,
)
from data.database import (
    db_init,
    DBProvider,
)


def config_instance(config_level: str | None = None) -> FastAPI:
    print(f"[+] Configuring server...")
    app = FastAPI()
    config_config_level(config_level)
    config_middleware(app)
    config_templates()
    config_database()
    config_exception_handlers(app)
    config_routes(app)
    print("[+] ...done configuring server")
    return app
#:

def config_config_level(config_level: str | None = None):
    if config_level:
        via = 'parameter'
    elif config_level := os.environ.get('CONFIG_LEVEL'):
        via = 'os.environ'
    else:
        via = 'default'
        config_level = 'PROD'
    set_config_level(config_level)
    print(f"[+] ...configuration level set to '{config_level}' ('{via}')")
#:

def config_middleware(app: FastAPI):
    add_global_request_middleware(app)
    add_session_middleware(app)
    print("[+] ...middleware configured")
#:

def config_templates(): 
    global_init(config_value('TEMPLATES_PATH'))
    print("[+] ...templates configured")
#:

def config_database(): 
    print(f"[+] ...DB Provider is '{config_value('DATABASE_PROVIDER')}'.")
    db_init(DBProvider.from_settings(
        provider = config_value('DATABASE_PROVIDER'),
        database = config_value('DATABASE'),
        host = config_value('DATABASE_HOST'),
        user = config_value('DATABASE_USER'),
        password = config_value('DATABASE_PASSWORD'),
    ))
    print("[+] ...database initialized")
#:

def config_exception_handlers(app: FastAPI):

    async def unauthorized_access_handler(*_, **__):
        error_template_path = config_value('ERROR_TEMPLATE_PATH')
        template = PageTemplateFile(f'{error_template_path}/404.pt')
        content = template(**ViewModel())
        return responses.HTMLResponse(content, status_code = status.HTTP_404_NOT_FOUND)
    #:

    async def unauthenticated_only_area_handler(*_, **__):
        return responses.RedirectResponse(url = '/', status_code = status.HTTP_302_FOUND)
    #:

    for exception_type in (HTTPUnauthorizedAccess, status.HTTP_404_NOT_FOUND):
        app.add_exception_handler(exception_type, unauthorized_access_handler)
    app.add_exception_handler(HTTPUnauthenticatedOnly, unauthenticated_only_area_handler)
    print("[+] ...exception handlers configured")
#:

def config_routes(app: FastAPI):
    static_path = config_value('STATIC_PATH')
    app.mount(static_path, StaticFiles(directory='static'), name='static')
    for view in (home, courses, account):
        app.include_router(view.router)
    print("[+] ...routes configured")
#:

app: FastAPI = config_instance()
