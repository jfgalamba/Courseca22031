from sqlalchemy import func, select
from sqlalchemy.orm import Session

# https://passlib.readthedocs.io/en/stable/narr/quickstart.html
# https://passlib.readthedocs.io/en/stable/lib/passlib.hash.pbkdf2_digest.html#passlib.hash.pbkdf2_sha512
# https://passlib.readthedocs.io/en/stable/lib/passlib.ifc.html#passlib.ifc.PasswordHash.hash

import passlib.hash as passlib_hash

from data.database import database_session
from data.models import (
    UserLoginData,
    UserAccount,
    HashAlgoEnum,
    ExternalProvider,
    UserLoginDataExternal,
)
from common.common import (
    is_valid_email,
    find_first,
)


__all__ = (
    'InvalidUserAttribute',
    'UserNotFound',
    'InvalidAuthentication',
    'user_count',
    'authenticate_user_by_email_addr',
    'get_user_by_email',
    'get_user_by_id',
    'get_user_by_external_id',
    'add_external_login',
    'password_matches',
    'DEFAULT_HASH_ALGO',
)


KNOWN_HASHERS = {
    HashAlgoEnum.PBKDF2_SHA256: passlib_hash.pbkdf2_sha256,
    HashAlgoEnum.PBKDF2_SHA512: passlib_hash.pbkdf2_sha512,
    HashAlgoEnum.ARGON2: passlib_hash.argon2,
}
DEFAULT_HASH_ALGO = HashAlgoEnum.PBKDF2_SHA512


class InvalidUserAttribute(ValueError):
    pass

class UserNotFound(Exception):
    pass

class InvalidAuthentication(Exception):
    pass


def user_count(
        concrete_type = UserAccount,
        db_session: Session | None = None,
) -> int:
    with database_session(db_session) as db_session:
        select_stm = select(func.count()).select_from(concrete_type)
        return db_session.execute(select_stm).scalar_one()
#:

def authenticate_user_by_email_addr(
        email_addr: str,
        password: str,
        db_session: Session | None = None,
) -> UserAccount | None:
    with database_session(db_session) as db_session:
        if not is_valid_email(email_addr):
            raise UserNotFound(f'Invalid email address: {email_addr}')
        if user := get_user_by_email(email_addr, db_session):
            if password_matches(user, password):
                return user
        return None
#:

def get_user_by_email(
        email_addr: str,
        db_session: Session | None = None,
) -> UserAccount | None:
    with database_session(db_session) as db_session:
        if not is_valid_email(email_addr):
            raise ValueError(f'Invalid email: {email_addr}')
        select_stmt = (
            select(UserAccount)
            .join(UserLoginData)
            .where(UserLoginData.email_addr == email_addr)
        )
        return db_session.execute(select_stmt).scalar_one_or_none()
#:

def get_user_by_id(
        user_id: int,
        db_session: Session | None = None,
) -> UserAccount | None:
    with database_session(db_session) as db_session:
        select_stmt = (
            select(UserAccount)
            .join(UserLoginData)
            .where(UserAccount.user_id == user_id)
        )
        return db_session.execute(select_stmt).scalar_one_or_none()
#:

def get_user_by_external_id(
        external_provider_id: int,
        external_user_id: str,
        db_session: Session | None = None,
) -> UserAccount | None:
    with database_session(db_session) as db_session:
        select_stmt = (
            select(UserAccount)
            .join(UserLoginDataExternal)
            .join(ExternalProvider)
            .where(UserLoginDataExternal.external_user_id == external_user_id)
            .where(ExternalProvider.id == external_provider_id)
        )
        return db_session.execute(select_stmt).scalar_one_or_none()
#:

def add_external_login(
        user: UserAccount,
        external_provider_id: int,
        external_user_id: str,
        db_session: Session | None = None,
) -> UserLoginDataExternal | None:
    with database_session(db_session) as db_session:
        if find_first(
                user.external_login_data,  # type: ignore
                external_provider_id, 
                key = lambda row: row.external_provider_id
        ):
            err_msg = f'User has already been registered with external provider {external_provider_id}'
            raise InvalidUserAttribute(err_msg)
        db_session.add(
            external_login_data := UserLoginDataExternal(
                user_id = user.user_id,
                external_provider_id = external_provider_id,
                external_user_id =  external_user_id,
            )
        )
        db_session.commit()
        db_session.refresh(external_login_data)
        return external_login_data
#:

def password_matches(user: UserAccount, password: str) -> bool:
    hash_algo = user.user_login_data.hash_algo
    hasher = KNOWN_HASHERS[hash_algo]
    return hasher.verify(password, user.password_hash)
#:

def hash_password(password: str, hash_algo: HashAlgoEnum = DEFAULT_HASH_ALGO) -> str:
    return KNOWN_HASHERS[hash_algo].hash(password)
#:

def ensure_user_is(
        user_or_id: UserAccount | int,
        concrete_user_type: UserAccount,
        db_session: Session | None = None, 
) -> UserAccount:
    with database_session(db_session) as db_session:
        if isinstance(user_or_id, concrete_user_type):
            user =  user_or_id
        else:
            if not (user := get_user_by_id(user_or_id, db_session)):
                raise ValueError(f'Invalid id {id}.')

            if not isinstance(user, concrete_user_type):
                msg = (f'Invalid type for user {user.user_id}: expecting'
                    f'{concrete_user_type.__name__} but got {type(user).__name__}')
                raise TypeError(msg)
        return user
#:
