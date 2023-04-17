@router.get('/account/register')                    # type: ignore
@template()
async def register():
    return RegisterViewModel()
#:

@router.post('/account/register')                   # type: ignore
@template(template_file='account/register.pt')
async def post_register(request: Request) -> ViewModel | Response:
    vm = RegisterViewModel()
    await vm.load(request)

    if vm.error:
        return vm

    response = responses.RedirectResponse(url='/', status_code=status.HTTP_302_FOUND)
    set_auth_cookie(response, vm.new_student_id)
    return response
#:

class RegisterViewModel(ViewModel):
    MIN_DATE = date.fromisoformat('1920-01-01')

    def __init__(self, *args, **kargs):
        super().__init__(self, *args, **kargs)
        self.name = ''
        self.email = ''
        self.password = ''
        self.birth_date = None
        self.min_date = RegisterViewModel.MIN_DATE
        self.max_date = date.today()
        self.checked = False
        self.new_student_id = -1

    async def load_from_request(self, request: Request):
        def is_valid_birth_date(birth_date: str) ->  bool:
            return (is_valid_iso_date(birth_date) 
                    and date.fromisoformat(birth_date) >= RegisterViewModel.MIN_DATE)
        #:
        form_data = await request.form()
        self.name = form_field_as_str(form_data, 'name')
        self.email = form_field_as_str(form_data, 'email')
        self.password = form_field_as_str(form_data, 'password')
        self.birth_date = form_field_as_str(form_data, 'birth_date')
        self.new_student_id = -1

        if not is_valid_name(self.name):
            error, error_msg = True, 'Nome inválido!'
        #:
        elif not is_valid_email(self.email):
            error, error_msg = True, 'Endereço de email inválido!'
        #:
        elif not is_valid_password(self.password):
            error, error_msg = True, 'Senha inválida!'
        #:
        elif not is_valid_birth_date(self.birth_date):
            error, error_msg = True, 'Invalid birth date!'
        #:
        elif student_service.get_student_by_email(self.email):
            error, error_msg = True, f'Endereço de email {self.email} já existe!'
        #:
        else:
            error, error_msg = False, ''
        #:

        if not error:
            self.new_student_id = student_service.create_account(
                self.name,
                self.email,
                self.password,
                date.fromisoformat(self.birth_date),
            ).id
        #: 
        self.error, self.error_msg = error, error_msg
#:

@router.get('/account/login')                            # type: ignore
@template()
async def login() -> ViewModel:
    return login_viewmodel()
#:

def login_viewmodel() -> ViewModel:
    return ViewModel(
        email = '',
        password = '',
    )
#:

@router.post('/account/login')                            # type: ignore
@template(template_file='account/login.pt')
async def post_login(request: Request):  # TODO: tipo 
    vm = await post_login_viewmodel(request)

    if vm.error:
        return vm

    response = responses.RedirectResponse(url='/', status_code=status.HTTP_302_FOUND)
    set_auth_cookie(response, vm.student_id)
    return response
#:

class LoginViewModel(ViewModel):
    def load(self, request: Request | None = None):
        if not request:
            request = global_request.get()
        form_data = await request.form()
        email = form_field_as_str(form_data, 'email')
        password = form_field_as_str(form_data, 'password')
        student_id = None

        if not is_valid_email(email):
            error, error_msg = True, 'Invalid user or password!'
        #:
        elif not is_valid_password(password):
            error, error_msg = True, 'Invalid password!'
        #:
        elif not (student := student_service.authenticate_student_by_email(email, password)):
            error, error_msg = True, 'User not found!'
        #:
        else:
            error, error_msg = False, ''
            student_id = student.id
        #:

        return ViewModel(
            error = error,
            error_msg = error_msg,
            email = email,
            password = password,
            student_id = student_id,
        )
#:

