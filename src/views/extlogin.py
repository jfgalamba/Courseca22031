from urllib.parse import quote_plus as quote

from fastapi import (
    APIRouter,
    Request,
    Depends,
    responses,
    status,
)
from fastapi import (
    responses,
    status,
    HTTPException,
)
from pydantic import BaseModel
import aiohttp
from jose import jwt

from config_settings import conf
from views.account import exec_login
from services import (
    students_service as sserv, 
    settings_service as setserv,
)
from common.auth import (
    get_session,
    requires_unauthentication,
)
from common.common import (
    is_ascii,
    secure_random_str,
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

################################################################################
##
##  SETUP FastAPI
##
################################################################################

router = APIRouter(prefix='/extlogin')

################################################################################
##
##  EXTERNAL LOGIN
##
################################################################################

class ExternalLoginError(HTTPException):
    def __init__(self, *args, **kargs):
        super().__init__(status_code = status.HTTP_401_UNAUTHORIZED, *args, **kargs)
#:

class ExchangeTokens(BaseModel):
    access_token: str
    expires_in: int
    id_token: str
#:

class DecodedIDToken(BaseModel):
    provider_id: int
    external_id: str
    email_addr: str
#:

@router.get(
    '/start/{external_provider_id}',
    dependencies = (Depends(requires_unauthentication),)
)
async def external_login(external_provider_id: int, request: Request):
    """
    Get the external provider id (only Google accepted for now), and
    then let's start OAuth2/OpenID Connect's server flow (*). All steps
    needed are listed here:

        1. Create an anti-forgery state token
        2. Send an authentication request to Google
        3. Confirm the anti-forgery state token
        4. Exchange code for access token and ID token
        5. Obtain user information from the ID token
        6. Authenticate the user

    See:
    https://developers.google.com/identity/openid-connect/openid-connect
    https://developers.google.com/identity/openid-connect/openid-connect#server-flow
    https://developers.google.com/identity/openid-connect/openid-connect#authenticationuriparameters

    First two steps are executed by this view.

    (*) - The server flow allows the back-end server of an application
    to verify the identity of the person using a browser or mobile
    device. The implicit flow is used when a client-side application
    (typically a JavaScript app running in the browser) needs to access
    APIs directly instead of via its back-end server.
    """
    external_provider = setserv.get_external_provider_by_id(external_provider_id)
    if not external_provider:
        err_msg = f"Unknown external provider id {external_provider_id}"
        raise ExternalLoginError(err_msg)
    url = create_authentication_request(request, external_provider_id)
    return responses.RedirectResponse(url)
#:

def create_authentication_request(
        request: Request,
        external_provider_id: int,
) -> str:
    """
    1. Create an anti-forgery state token
    https://developers.google.com/identity/openid-connect/openid-connect#createxsrftoken

    2. Send an authentication request to Google
    https://developers.google.com/identity/openid-connect/openid-connect#sendauthrequest
    """
    state = f'token:{secure_random_str(64)}.provider_id:{external_provider_id}'
    request.session['state'] = state

    nonce = secure_random_str(64)
    request.session['nonce'] = nonce

    query_params = dict(
        response_type = 'code',
        client_id = GOOGLE_CLIENT_ID,
        redirect_uri = GOOGLE_REDIRECT_URI,
        scope = 'openid email',
        state = state,
        nonce = nonce,
    )
    query_str = '&'.join(
        f'{param}={quote(value)}' for param, value in query_params.items()
    )
    return f"{GOOGLE_AUTH_URI}?{query_str}"
#:

@router.get(
    '/continue',
    dependencies = (Depends(requires_unauthentication),)
)    # type: ignore
async def external_login_response(
        request: Request,
        state = '', 
        code = '',
        scope = '',
):
    """
    Google responded. Now will proceed from here, and resume the
    process on step 3 (which is 'Confirm anti-forgery state token').
    From here on, this server will become a HTTPS client when talking
    to the OAuth2/OpenID Connect provider).
    """
    print(f"[+] Request coming from {request.client}")
    external_provider_id = validate_state_token(state)

    async with aiohttp.ClientSession() as http_session:
        tokens = await exchange_code_for_tokens(http_session, code)
        decoded_id_token = await decode_and_validate_id_token(
            http_session, 
            external_provider_id,
            tokens,
        )

    if student_id := authenticate_student(decoded_id_token):
        return exec_login(student_id)
    return register_after_external_authentication(decoded_id_token)
#:

def validate_state_token(state: str) -> int:
    """
    3. Confirm anti-forgery state token
    https://developers.google.com/identity/openid-connect/openid-connect#sendauthrequest
    """
    session = get_session()
    error_msg = ''
    external_provider_id = ''

    if not (session_state := session.get('state')):
        error_msg = f"State token not in session for current request "
    #:
    elif state != session_state:
        error_msg = f"State mismatch: {state}"
    #:
    elif state.count('provider_id:') != 1:
        error_msg = f"State error: {state}. Shouldn't have more than one provider."
    #:
    elif (external_provider_id := state.rpartition('provider_id:')[-1].strip()) \
         and not external_provider_id.isdigit():
        error_msg = f"Invalid 'external_provider_id': {external_provider_id}."
    #:

    if error_msg:
        raise ExternalLoginError(detail = error_msg)

    print(f"[+] State toke is valid")
    return int(external_provider_id)
#:

async def exchange_code_for_tokens(
        http_session: aiohttp.ClientSession,
        code: str,
) -> ExchangeTokens:
    """
    4. Exchange code for access token and ID token
    https://developers.google.com/identity/openid-connect/openid-connect#confirmxsrftoken
    """
    req_data = dict(
        code = code,
        client_id = GOOGLE_CLIENT_ID,
        redirect_uri = GOOGLE_REDIRECT_URI,
        client_secret = GOOGLE_CLIENT_SECRET,
        grant_type = GOOGLE_GRANT_TYPE,
    )
    async with http_session.post(GOOGLE_TOKEN_URI, data = req_data) as resp:
        resp_data = await resp.json()

    return ExchangeTokens (
        access_token = resp_data['access_token'], 
        expires_in = resp_data['expires_in'], 
        id_token = resp_data['id_token'],
    )
#:

async def decode_and_validate_id_token(
        http_session: aiohttp.ClientSession,
        provider_id: int,
        tokens: ExchangeTokens,
) -> DecodedIDToken:
    """
    Decode and validate the access token response. This response
    contains and id_token which is a JWT with information about the
    user. The following validations will be performed on this 
    id_token.

    This corresponds to step 5:

    5. Obtain user information from the ID token
    https://developers.google.com/identity/openid-connect/openid-connect#obtainuserinfo

    Validation of an ID token requires several steps:

    1. Verify that the ID token is properly signed by the issuer.
       Google-issued tokens are signed using one of the certificates
       found at the URI specified in the jwks_uri metadata value of the
       Discovery document.

    2. Verify that the value of the iss claim in the ID token is equal
       to https://accounts.google.com or accounts.google.com.

    3. Verify that the value of the aud claim in the ID token is equal
       to your app's client ID.

    4. Verify that the expiry time (exp claim) of the ID token has 
       not passed.

    5. If you specified a hd parameter value in the request, verify
       that the ID token has a hd claim that matches an accepted 
       domain associated with a Google Cloud organization.

    (next steps added by me...)

    6. Validate if the nonce is the one which was originally sent in 
       the first step.

    7. Validate if the Google user id in the 'sub' field/claim is
       the correct format: at most 255 ascii characteres
 
    See:
    https://developers.google.com/identity/openid-connect/openid-connect#validatinganidtoken
    """
    # Get public key from jwks uri
    async with http_session.get(GOOGLE_JWKS_URI) as resp:
        # Gives the set of jwks keys.the keys has to be passed as it is 
        # to jwt.decode() for signature verification.
        key = await resp.json()

        # Get the algorithm type from the request header
        algorithm = jwt.get_unverified_header(tokens.id_token).get('alg')

        # This simultaneously validates steps 1, 3, 4 and decodes the token
        decoded_token = jwt.decode(
            token = tokens.id_token,
            key = key,
            algorithms = algorithm,
            audience = GOOGLE_CLIENT_ID,
            access_token = tokens.access_token,
        )

        # Validate step 2
        iss = decoded_token['iss']
        if iss not in GOOGLE_ISS_URIS:
            raise ExternalLoginError(f"Invalid 'iss' key '{iss}' in id_token")

        # Validate step 6
        session = get_session()
        expected_nonce = session['nonce']
        received_nonce = decoded_token['nonce']
        if received_nonce != expected_nonce:
            raise ExternalLoginError(f"Nonce missing or invalid: {received_nonce}")
        del session['nonce']    # one time use, so better get rid of it

        # Validate step 7
        sub = decoded_token['sub']
        if len(sub) > 255 or not is_ascii(sub):
            raise ExternalLoginError(f"Invalid 'sub': {sub}")

        print(f"[+] id_token (JWT) is valid!")
        return DecodedIDToken(
            external_id = sub,
            email_addr = decoded_token['email'],
            provider_id = provider_id,
        )
#:

def authenticate_student(id_token: DecodedIDToken) -> int | None:
    """
    6. Authenticate the user
    https://developers.google.com/identity/openid-connect/openid-connect#authuser

    We have three possible scenarios here:
    1. User is a registered user and has authenticated before with this 
       external provider
    2. User is a registered user but it's the first time it authenticates 
       with this external provider
    3. User is an unregistered user
    """
    student_id: int | None = None
    if user := sserv.get_student_by_email(id_token.email_addr):
        student_id = user.user_id   # type: ignore
        get = sserv.get_student_by_external_id
        if not get(id_token.provider_id, id_token.external_id):
            add = sserv.add_student_external_login
            add(user, id_token.provider_id, id_token.external_id)
    return student_id
#:

def register_after_external_authentication(decoded_id_token: DecodedIDToken):
    register_url = f"/account/register"
    session = get_session()
    session['email_addr'] = decoded_id_token.email_addr
    session['name'] = ''
    return responses.RedirectResponse(url = register_url)
#:

# async def get_discovery_document(client: aiohttp.ClientSession) -> dict:
#     async with client.get(GOOGLE_DISCOVERY_DOC_URL) as resp:
#         return await resp.json()
# #:

# {
#   "keys": [
#     {
#       "use": "sig",
#       "kty": "RSA",
#       "kid": "acda360fb36cd15ff83af83e173f47ffc36d111c",
#       "n": "r54td3hTv87IwUNhdc-bYLIny4tBVcasvdSd7lbJILg58C4DJ0RJPczXd_rlfzzYGvgpt3Okf_anJd5aah196P3bqwVDdelcDYAhuajBzn40QjOBPefvdD5zSo18i7OtG7nhAhRSEGe6Pjzpck3wAogqYcDgkF1BzTsRB-DkxprsYhp5pmL5RnX-6EYP5t2m9jJ-_oP9v1yvZkT5UPb2IwOk5GDllRPbvp-aJW_RM18ITU3qIbkwSTs1gJGFWO7jwnxT0QBaFD8a8aev1tmR50ehK-Sz2ORtvuWBxbzTqXXL39qgNJaYwZyW-2040vvuZnaGribcxT83t3cJlQdMxw",
#       "e": "AQAB",
#       "alg": "RS256"
#     },
#     {
#       "use": "sig",
#       "kty": "RSA",
#       "kid": "96971808796829a972e79a9d1a9fff11cd61b1e3",
#       "n": "vfBbH3bcgTzYXomo5hmimATzkEF0QIuhMYmwx0IrpdKT6M15b6KBVhZsPfwbRNoui3iBe8xLON2VHarDgXRzrHec6-oLx8Sh4R4B47MdASURoiIOBiSOiJ3BjKQexNXT4wO0ZLSEMTVt_h24fgIerASU6w2XQOeGb7bbgZnJX3a0NAjsfrxCeG0PacWK2TE2R00mZoeAYWtCuAsE-Xz0hkGqEsg7HqIMYeLjQ-NFkGBErGAi5Cd_k3_D7rv0IEdoB1GkJpIdMLqnI-MR_OxsQNZGpC12OaLXCqgkFAgW69QLAG3YMaTFgPi-Us1i2idc4SPADYijiPml---jCap9yw"
#       "e": "AQAB",
#       "alg": "RS256",
#     }
#   ]
# }
