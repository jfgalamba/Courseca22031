from fastapi import (
    APIRouter,
)
from fastapi_chameleon import template

from config_settings import conf
from services import (
    courses_service as cserv,
    students_service as sserv,
    instructors_service as iserv,
)
from common.viewmodel import ViewModel

################################################################################
##
##  SETTINGS FOR THIS VIEW
##
################################################################################

AVAILABLE_COURSES_COUNT = 20

POPULAR_COURSES_COUNT = 3
SELECTED_COURSES_COUNT = 3
SELECTED_INSTRUCTORS_COUNT = 3
TESTIMONIALS_COUNT = 5

################################################################################
##
##  SETUP FastAPI
##
################################################################################

router = APIRouter()

################################################################################
##
##  VIEWS / (indexz) & ABOUT
##
################################################################################

@router.get('/')                            # type: ignore
@template()
async def index():
    return index_viewmodel()
#:

def index_viewmodel() -> ViewModel:
    return ViewModel(
        courses_images_url = conf('COURSES_IMAGES_URL'),
        instructors_images_url = conf('INSTRUCTORS_IMAGES_URL'),
        num_courses = cserv.course_count(),
        num_students = sserv.student_count(),
        num_instructors = iserv.instructor_count(),
        num_events = 159,
        popular_courses = cserv.most_popular_courses(
            POPULAR_COURSES_COUNT,
        ),
        selected_instructors = iserv.selected_instructors(
            SELECTED_INSTRUCTORS_COUNT
        ),
    )
#:

@router.get('/about')                        # type: ignore
@template()
async def about():
    return about_viewmodel()
#:

def about_viewmodel() -> ViewModel:
    return ViewModel(
        images_url = conf('IMAGES_URL'),
        num_courses = cserv.course_count(),
        num_students = sserv.student_count(),
        num_instructors = iserv.instructor_count(),
        num_events = 159,
        testimonials = sserv.get_testimonials(TESTIMONIALS_COUNT)
    )
#:
