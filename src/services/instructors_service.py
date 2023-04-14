from datetime import date
from random import sample

from sqlalchemy import (
    select,
) 
from sqlalchemy.orm import Session

from data.database import database_session
from data.models import (
    Instructor,
    InstructorExpertise,
    UserAccountStatusEnum,
    UserLoginData,
    SocialNetworkEnum,
    SocialNetworkType,
    SocialNetworkAddr,
)
from services import users_service as userv
from services.users_service import (
    get_user_by_email as get_instructor_by_email,
    get_user_by_id as get_instructor_by_id,
    authenticate_user_by_email_addr as authenticate_instructor_by_email,
    password_matches as instructor_password_matches,
)


__all__ = (
    'get_instructor_by_email',
    'get_instructor_by_id',
    'authenticate_instructor_by_email',
    'instructor_password_matches',
    'instructor_count',
    'selected_instructors',
    'create_expertise',
    'create_instructor_account',
)


def instructor_count(db_session: Session | None = None) -> int:
    return userv.user_count(Instructor, db_session)
#:

def selected_instructors(
        count: int,
        db_session: Session | None = None,
) -> list[Instructor]:
    with database_session(db_session) as db_session:
        select_stmt = (
            select(Instructor)
            .where(Instructor.status_id == UserAccountStatusEnum.Active.id)
        )
        instructors = db_session.execute(select_stmt).scalars().all()
        return sample(instructors, count) if count > 0 else instructors
#:

def create_expertise(
        name: str,
        db_session: Session | None = None,
) -> InstructorExpertise:
    with database_session(db_session) as db_session:
        db_session.add(
            exp := InstructorExpertise(name = name)
        )
        db_session.commit()
        return exp
#:

def create_instructor_account(
        fullname: str,
        email_addr: str,
        password: str,
        birth_date: date,
        address_line1: str,
        zip_code: str,
        country_iso_code: str,
        expertise_id: int,
        presentation: str,
        presentation_image_url: str = '',
        twitter_addr: str = '',
        facebook_addr: str = '',
        instagram_addr: str = '',
        linkedin_addr: str = '',
        address_line2: str = '',
        status: UserAccountStatusEnum = UserAccountStatusEnum.Active,
        db_session: Session | None = None,
) -> Instructor:
    with database_session(db_session) as db_session:
        db_session.add(
            instructor := Instructor(
                type = Instructor.__name__,
                fullname = fullname,
                birth_date = birth_date,
                address_line1 = address_line1,
                address_line2 = address_line2,
                zip_code = zip_code,
                country_iso_code = country_iso_code,
                expertise_id = expertise_id,
                presentation = presentation,
                presentation_image_url = presentation_image_url,
            )
        )
        instructor.status = status
        db_session.flush()

        db_session.add(
            UserLoginData(
                user_id = instructor.user_id,
                email_addr = email_addr,
                password_hash = userv.hash_password(password),
                hash_algo_id = userv.DEFAULT_HASH_ALGO.id,
            ),
        )

        def add_social_network_addr(addr, social_network_enum):
            if addr:
                db_session.add(
                    SocialNetworkAddr(
                        social_network_type_id = social_network_enum.id,
                        addr = addr,
                        user_id = instructor.user_id,
                    )
                )
        #:

        add_social_network_addr(twitter_addr, SocialNetworkEnum.twitter)
        add_social_network_addr(facebook_addr, SocialNetworkEnum.facebook)
        add_social_network_addr(instagram_addr, SocialNetworkEnum.instagram)
        add_social_network_addr(linkedin_addr, SocialNetworkEnum.linkedin)

        db_session.commit()
        return instructor
#:

def ensure_instructor(
        instructor_or_id: Instructor | int,
        db_session: Session | None = None, 
) -> Instructor:
    instructor = userv.ensure_user_is(instructor_or_id, Instructor, db_session)
    assert isinstance(instructor, Instructor)
    return instructor
#:
