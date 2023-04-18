from datetime import date

from fastapi import (
    APIRouter,
    Request,
    Response,
    Depends,
    responses,
    status,
)
from fastapi import (
    responses,
    status,
)
from fastapi_chameleon import template

from config_settings import conf
from services import (
    students_service as sserv, 
    settings_service as setserv,
)
from common.viewmodel import ViewModel
from common.auth import (
    get_current_user,
    get_session,
    set_current_user,
    requires_authentication,
    requires_unauthentication,
    remove_current_user,
)
from common.fastapi_utils import form_field_as_str
from common.common import (
    is_valid_name,
    is_valid_email,
    is_valid_password,
    is_valid_iso_date,
    coalesce,
    find_first,
    all_except,
)


################################################################################
##
##  SETTINGS FOR THIS VIEW
##
################################################################################

GOOGLE_CLIENT_ID = conf('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = conf('GOOGLE_CLIENT_SECRET')
GOOGLE_AUTH_URI = conf('GOOGLE_AUTH_URI')
GOOGLE_TOKEN_URI = conf('GOOGLE_TOKEN_URI')
GOOGLE_REDIRECT_URI = conf('GOOGLE_REDIRECT_URI')
GOOGLE_SCOPE_REPLY = conf('GOOGLE_SCOPE_REPLY')
GOOGLE_DISCOVERY_DOC_URL = conf('GOOGLE_DISCOVERY_DOC_URL')
GOOGLE_GRANT_TYPE = conf('GOOGLE_GRANT_TYPE')
GOOGLE_JWKS_URI = conf('GOOGLE_JWKS_URI')
GOOGLE_ISS_URIS = conf('GOOGLE_ISS_URIS')

MIN_DATE = date.fromisoformat('1920-01-01')
# TODO: needs refactoring: there are duplicate definitions in models.py
ADDRESS_LINE_SIZE = 60
ZIP_CODE_SIZE = 20

################################################################################
##
##  SETUP FastAPI
##
################################################################################

router = APIRouter(prefix='/account')

################################################################################
##
##  REGISTER
##
################################################################################

@router.get(
    '/register',
    dependencies = (Depends(requires_unauthentication),)
)                    # type: ignore
@template()
async def register():
    return register_viewmodel()
#:

def register_viewmodel():
    name = get_session().get('name')
    email_addr = get_session().get('email_addr')
    return ViewModel(
        name = name,
        name_status = 'disabled' if name else '',
        email_addr = email_addr,
        email_addr_status = 'disabled' if email_addr else '',
        password = 'abc',
        birth_date = '2022-01-01',
        min_date = MIN_DATE,
        max_date = date.today(),
        checked = False,
    )
#:

@router.post(
    '/register',
    dependencies = (Depends(requires_unauthentication),)
)                   # type: ignore
@template(template_file='account/register.pt')
async def post_register(request: Request):
    vm = await post_register_viewmodel(request)

    if vm.error:
        return vm

    return exec_login(vm.new_student_id)
#:

async def post_register_viewmodel(request: Request) -> ViewModel:
    def is_valid_birth_date(birth_date: str) ->  bool:
        return (is_valid_iso_date(birth_date) 
                and date.fromisoformat(birth_date) >= MIN_DATE)
    #:

    name = get_session().get('name')
    email_addr = get_session().get('email_addr')
    form_data = await request.form()

    vm = ViewModel(
        name = name if name else form_field_as_str(form_data, 'name'),
        name_status = 'disabled' if name else '',
        email_addr = email_addr if email_addr else form_field_as_str(form_data, 'email_addr'),
        email_addr_status = 'disabled' if email_addr else '',
        password = form_field_as_str(form_data, 'password'),
        birth_date = form_field_as_str(form_data, 'birth_date'),
        new_student_id = None,
        min_date = MIN_DATE,
        max_date = date.today(),
        checked = False,
    )
    if not is_valid_name(vm.name):
        vm.error, vm.error_msg = True, 'Nome inválido!'
    #:
    elif not is_valid_email(vm.email_addr):
        vm.error, vm.error_msg = True, 'Endereço de email inválido!'
    #:
    elif not is_valid_password(vm.password):
        vm.error, vm.error_msg = True, 'Senha inválida!'
    #:
    elif not is_valid_birth_date(vm.birth_date):
        vm.error, vm.error_msg = True, 'Invalid birth date!'
    #:
    elif sserv.get_student_by_email(vm.email_addr):
        vm.error, vm.error_msg = True, f'Endereço de email {vm.email_addr} já existe!'
    #:
    else:
        vm.error, vm.error_msg = False, ''
    #:

    if not vm.error:
        vm.new_student_id = sserv.create_student_account(
            vm.name,
            vm.email_addr,
            vm.password,
            date.fromisoformat(vm.birth_date),
        ).user_id
    #:

    return vm
#:

################################################################################
##
##  UPDATE ACCOUNT
##
################################################################################

@router.get('/',
    dependencies = (Depends(requires_authentication),)
)                     # type: ignore
@template()
async def account():
    return account_viewmodel()
#:

def account_viewmodel() -> ViewModel:
    student = get_current_user()
     # Current user must exist because we're in an authenticated
     # view context.
    assert student is not None

    country_iso_code = coalesce(student.country_iso_code, '')
    return ViewModel(
        name = student.fullname,
        email_addr = student.email_addr,
        address_line1 = coalesce(student.address_line1, ''),
        address_line2 = coalesce(student.address_line2, ''),
        address_line_maxlength = ADDRESS_LINE_SIZE,
        zip_code = coalesce(student.zip_code, ''),
        zip_code_maxlength = ZIP_CODE_SIZE,
        **country_viewmodel_info(country_iso_code),
    )
#:

@router.post(
    '/',
    dependencies = (Depends(requires_authentication),)
)  # type: ignore
@template(template_file='account/account.pt')
async def update_account(request: Request):
    vm = await update_account_viewmodel(request)

    if vm.error:
        return vm

    return responses.RedirectResponse(url = '/', status_code = status.HTTP_302_FOUND)
#:

async def update_account_viewmodel(request: Request):
    def new_or_none(form_field: str) -> str | None:
        old = getattr(student, form_field)
        new = form_field_as_str(form_data, form_field).strip()
        if new is None or new == old:
            return None
        return new
    #:

    student = get_current_user()
    assert student is not None
    form_data = await request.form()

    country_iso_code = form_field_as_str(form_data, 'country_iso_code')

    vm = ViewModel(
        error_msg = '',
        name = student.fullname,
        email_addr = form_field_as_str(form_data, 'email_addr').strip(),
        address_line1 = form_field_as_str(form_data, 'address_line1').strip(),
        address_line2 = form_field_as_str(form_data, 'address_line2').strip(),
        address_line_maxlength = ADDRESS_LINE_SIZE,
        zip_code = form_field_as_str(form_data, 'zip_code').strip(),
        zip_code_maxlength = ZIP_CODE_SIZE,
        **country_viewmodel_info(country_iso_code),
    )

    current_password = form_field_as_str(form_data, 'current_password').strip()
    new_password = form_field_as_str(form_data, 'new_password').strip() or None
    new_email_addr = new_or_none('email_addr')
    new_address_line1 = new_or_none('address_line1')
    new_address_line2 = new_or_none('address_line2')
    new_zip_code = new_or_none('zip_code')
    new_country_iso_code = new_or_none('country_iso_code')

    if not sserv.student_password_matches(student, current_password):
        vm.error_msg = 'Senha inválida!'
    #:
    elif new_email_addr and not is_valid_email(new_email_addr):
        vm.error_msg = f'Endereço de email {new_email_addr} inválido!'
    #:
    elif new_email_addr and sserv.get_student_by_email(new_email_addr):
        vm.error_msg = f'Endereço de email {new_email_addr} já existe!'
    #:
    elif new_password and not is_valid_password(new_password):
        vm.error_msg = 'Nova senha inválida!'
    #:
    elif new_password and new_password == current_password:
        vm.error_msg = 'Nova senha é igual à anterior!'
    #:

    vm.error = bool(vm.error_msg)
    if not vm.error:
        sserv.update_student_account(
            student.user_id,      # type: ignore
            current_password,
            new_email_addr,
            new_password,
            new_address_line1,
            new_address_line2,
            new_zip_code,
            new_country_iso_code,
        )
    return vm
#:

def country_viewmodel_info(selected_iso_code: str) -> dict:
    all_countries = setserv.get_accepted_countries()
    key = lambda c: c.iso_code
    selected_country = find_first(all_countries, selected_iso_code, key = key)
    if selected_iso_code != '' and not selected_country:
        raise ValueError(f"Selected ISO code {selected_iso_code} not found")
    other_countries = all_except(all_countries, selected_iso_code, key = key)

    return dict(
        selected_country_iso_code = selected_iso_code,
        selected_country_name = selected_country.name if selected_country else '',
        other_countries = other_countries,
    )
#:

################################################################################
##
##  LOGIN & LOGOUT
##
################################################################################

@router.get(
    '/login',
    dependencies = (Depends(requires_unauthentication),)
)                   # type: ignore
@template()
async def login():
    return login_viewmodel()
#:

def login_viewmodel() -> ViewModel:
    return ViewModel(
        email_addr = 'alberto.antunes.alb@gmail.com',
        password = 'abc',
        external_auth_providers = setserv.get_external_auth_providers(),
    )
#:

@router.post(
    '/login',
    dependencies = (Depends(requires_unauthentication),)
)                   # type: ignore
@template(template_file='account/login.pt')
async def post_login(request: Request):
    vm = await post_login_viewmodel(request)

    if vm.error:
        return vm

    return exec_login(vm.student_id)
#:

async def post_login_viewmodel(request: Request) -> ViewModel:
    form_data = await request.form()
    vm = ViewModel(
        email_addr = form_field_as_str(form_data, 'email_addr'),
        password = form_field_as_str(form_data, 'password'),
        student_id = None,
        external_auth_providers = setserv.get_external_auth_providers(),
    )
    if not is_valid_email(vm.email_addr):
        vm.error_msg = 'Endereço de email inválido!'
    #:
    elif not is_valid_password(vm.password):
        vm.error_msg = 'Senha inválida!'
    #:
    elif not (student := 
            sserv.authenticate_student_by_email(vm.email_addr, vm.password)):
        vm.error_msg = 'Utilizador ou senha inválida!'
    #:
    else:
        vm.error_msg = ''
        vm.student_id = student.user_id
    #:

    vm.error = bool(vm.error_msg)
    return vm
#:

def exec_login(user_id: int) -> Response:
    response = responses.RedirectResponse(url = '/', status_code = status.HTTP_302_FOUND)
    set_current_user(user_id)
    return response
#:

@router.get('/logout',
    dependencies = (Depends(requires_authentication),)
)                     # type: ignore
async def logout():
    response = responses.RedirectResponse(url = '/', status_code=status.HTTP_302_FOUND)
    remove_current_user()
    return response
#:
