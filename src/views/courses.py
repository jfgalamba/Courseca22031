from decimal import Decimal as dec

from fastapi import APIRouter
from fastapi_chameleon import template

from config_settings import conf
from common.viewmodel import ViewModel
from services import courses_service as cserv 

################################################################################
##
##  SETTINGS FOR THIS VIEW
##
################################################################################

AVAILABLE_COURSES_COUNT = 20

################################################################################
##
##  SETUP FastAPI
##
################################################################################

router = APIRouter(prefix = '/courses')

################################################################################
##
##  VIEWS COURSES & COURSE DETAILS
##
################################################################################

@router.get('/')                            # type: ignore
@template()
async def courses():
    return courses_viewmodel()
#:

def courses_viewmodel() -> ViewModel:
    return ViewModel(
        courses_images_url = conf('COURSES_IMAGES_URL'),
        instructors_images_url = conf('INSTRUCTORS_IMAGES_URL'),
        available_courses = cserv.available_courses(AVAILABLE_COURSES_COUNT)
    )
#:

@router.get('/{course_id}')                # type: ignore
@template()
async def course_details(course_id: int):
    return course_details_viewmodel(course_id)
#:

def course_details_viewmodel(course_id: int) -> ViewModel:
    if course := cserv.get_course_by_id(course_id):
        course_price = dec(course.price) # type: ignore
        return ViewModel(
            course = course,
            course_price = 'gratuito' if course_price == dec(0) else f'{course_price} €',
            images_url = conf('IMAGES_URL'),
            instructors_images_url = conf('INSTRUCTORS_IMAGES_URL'),
        )
    return ViewModel(
        error = True,
        error_msg = f'Course {id} not found',
    )
#:
