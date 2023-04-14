
from decimal import Decimal as dec
from random import sample

from sqlalchemy import (
    select,
    func,
)
from sqlalchemy.orm import Session

from data.database import database_session
from data.models import (
    Course,
    CourseStatusEnum,
)


__all__ = (
    'course_count',
    'create_course',
    'most_popular_courses',
    'available_courses',
    'get_course_by_id',
)


def course_count(db_session: Session | None = None) -> int:
    with database_session(db_session) as db_session:
        select_stm = select(func.count()).select_from(Course)
        return db_session.execute(select_stm).scalar_one()
#:

def create_course(
        title: str,
        summary: str,
        description: str,  
        main_image_url: str,
        subcategory_id: str,
        instructor_id: str,
        language_id: str,
        price: dec,
        status: CourseStatusEnum = CourseStatusEnum.Active,
        db_session: Session | None = None,
) -> Course:
    with database_session(db_session) as db_session:
        db_session.add(
            course := Course(
                title = title,
                summary = summary,
                description = description,
                main_image_url = main_image_url,
                subcategory_id = subcategory_id,
                instructor_id = instructor_id,
                language_id = language_id,
                price = str(price),
            )
        )
        course.status = status
        db_session.commit()
        return course
#:

def most_popular_courses(
        count: int, 
        db_session: Session | None = None,
) -> list[Course]:
    with database_session() as db_session:
        courses = available_courses(db_session = db_session, count = 0)
        return sample(courses, count) if len(courses) >= count > 0 else courses
#:

def available_courses(
        count: int = 0,
        db_session: Session | None = None,
) -> list[Course]:
    with database_session(db_session) as db_session:
        select_stmt = select(Course).where(Course.status_id == CourseStatusEnum.Active.id)
        if count > 0:
            select_stmt = select_stmt.limit(count)
        return db_session.execute(select_stmt).scalars().all()
#:

def get_course_by_id(
        course_id: int, 
        db_session: Session | None = None,
) -> Course | None:
    with database_session(db_session) as db_session:
        select_stmt = select(Course).where(Course.id == course_id)
        return db_session.execute(select_stmt).scalar_one_or_none()
#:
