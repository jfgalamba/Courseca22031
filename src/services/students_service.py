from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from data.database import database_session
from data.models import (
    UserLoginData,
    UserAccountStatusEnum,
    Student,
    Testimonial,
    Course,
    Enrollment,
)
from services import users_service as userv
from services.users_service import (
    get_user_by_email as get_student_by_email,
    get_user_by_id as get_student_by_id,
    get_user_by_external_id as get_student_by_external_id,
    authenticate_user_by_email_addr as authenticate_student_by_email,
    password_matches as student_password_matches,
    add_external_login as add_student_external_login,
    add_profile_image as add_student_profile_image,
    InvalidUserAttribute,
)
from common.common import (
    is_valid_password,
    coalesce,
)


__all__ = (
    'InvalidUserAttribute',
    'InvalidEnrollment',
    'AlreadyEnrolled',
    'student_count',
    'create_student_account',
    'update_student_account',
    'get_student_by_email',
    'get_student_by_id',
    'get_student_by_external_id',
    'authenticate_student_by_email',
    'student_password_matches',
    'add_student_external_login',
    'add_student_profile_image',
    'create_testimonial',
    'get_testimonials',
    'is_enrolled_in_course',
    'enroll_student_in_course',
)


MAX_TESTIMONIALS = 10


class InvalidEnrollment(Exception):
    pass
#:

class AlreadyEnrolled(InvalidEnrollment):
    pass
#:

def student_count(db_session: Session | None = None) -> int:
    return userv.user_count(Student, db_session)
#:

def create_student_account(
        fullname: str,
        email_addr: str,
        password: str,  
        birth_date: date,
        address_line1: str | None = None,
        address_line2: str | None = None,
        zip_code: str | None = None,
        country_iso_code: int | None = None,
        status: UserAccountStatusEnum = UserAccountStatusEnum.Active,
        db_session: Session | None = None,
) -> Student:
    with database_session(db_session) as db_session:
        if get_student_by_email(email_addr, db_session):
            raise InvalidUserAttribute(f'Email already {email_addr} registered')

        db_session.add(
            student := Student(
                type = Student.__name__,
                fullname = fullname,
                birth_date = birth_date,
                address_line1 = address_line1,
                address_line2 = address_line2,
                zip_code = zip_code,
                country_iso_code = country_iso_code,
            )
        )
        student.status = status
        db_session.flush()

        db_session.add(
            UserLoginData(
                user_id = student.user_id,
                email_addr = email_addr,
                password_hash = userv.hash_password(password),
                hash_algo_id = userv.DEFAULT_HASH_ALGO.id,
            )
        )
        db_session.commit()
        db_session.refresh(student)
        return student
#:

def update_student_account(
        student_or_id: int | Student,
        current_password: str,
        new_email_addr: str | None = None,
        new_password: str | None = None,
        new_address_line1: str | None = None,
        new_address_line2: str | None = None,
        new_zip_code: str | None = None,
        new_country_iso_code: str | None = None,
        db_session: Session | None = None,
) -> Student:
    with database_session(db_session) as db_session:
        student = ensure_student(student_or_id, db_session)

        if not student_password_matches(student, current_password):
            raise ValueError(f"Password doesn't match.")

        if new_email_addr:
            if get_student_by_email(new_email_addr, db_session):
                raise InvalidUserAttribute(f'Email already {new_email_addr} registered')
            student.email_addr = new_email_addr

        if new_password:
            if not is_valid_password(new_password):
                raise InvalidUserAttribute(
                    f'Invalid new password for student {student.user_id}'
                )
            student.password_hash = userv.hash_password(new_password)

        student.address_line1 = coalesce(new_address_line1, student.address_line1)
        student.address_line2 = coalesce(new_address_line2, student.address_line2)
        student.zip_code = coalesce(new_zip_code, student.zip_code)
        student.country_iso_code = coalesce(new_country_iso_code, student.country_iso_code)

        db_session.commit()
        db_session.refresh(student)
        return student
#:

def ensure_student(
        student_or_id: Student | int,
        db_session: Session | None = None, 
) -> Student:
    student = userv.ensure_user_is(student_or_id, Student, db_session)
    assert isinstance(student, Student)
    return student
#:

def create_testimonial(
        user_id: int,
        user_occupation: str,
        text: str,
        image_url: str,
        db_session: Session | None = None,
) -> Testimonial:
    with database_session(db_session) as db_session:
        db_session.add(
            test := Testimonial(
                user_id = user_id,
                user_occupation = user_occupation,
                text = text,
                image_url = image_url,
            )
        )
        db_session.commit()
        db_session.refresh(test)
        return test
#:

def get_testimonials(
        count: int = 0,
        db_session: Session | None = None,
) -> list[Testimonial]:
    with database_session(db_session) as db_session:
        select_stmt = select(Testimonial)
        scalar_results = db_session.execute(select_stmt).scalars()
        return scalar_results.fetchmany(count) if count > 0 else scalar_results.all()
#:

def is_enrolled_in_course(
        student: Student,
        course: Course,
        db_session: Session | None = None,
) -> bool:
    with database_session(db_session) as db_session:
        select_stmt = (
            select(Enrollment)
            .where(Enrollment.student_id == student.user_id)
            .where(Enrollment.course_id == course.id)
        )
        return bool(db_session.execute(select_stmt).scalar_one_or_none())
#:

def enroll_student_in_course(
        student: Student,
        course: Course,
        db_session: Session | None = None,
) -> Enrollment:
    with database_session(db_session) as db_session:
        if is_enrolled_in_course(student, course, db_session):
            raise AlreadyEnrolled('Student {student.user_id} already enrolled in course {course.id}')
        #:

        enrollment = Enrollment()
        enrollment.course = course
        student.courses.append(enrollment)
        db_session.add(enrollment)
        db_session.commit()
        return enrollment
#: