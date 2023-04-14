import enum

from sqlalchemy import (
    CheckConstraint,
    Column,
    Boolean,
    Date,
    ForeignKey,
    Identity,
    Integer,
    # Numeric,
    String,
    DateTime,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import (
    relationship,
    Session,
)

from data.model_base import SqlAlchemyBase

################################################################################
##
##      ENUM TABLES
##      NOTE: This module first needs to be generated/compiled.
##
################################################################################

from data.enum_tables import *

################################################################################
##
##      CONSTANTS
##
################################################################################

URL_SIZE = 300

EXTERNAL_PROVIDER_NAME_SIZE = 20
USER_EXTERNAL_ID_TOKEN_MAX_SIZE = 255

EMAIL_REGEXP = r"[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
NAME_REGEXP = r'^[^\W_0-9]{2,}(\s[^\W_0-9]{2,})+$'
FULLNAME_SIZE = 100
ADDRESS_LINE_SIZE = 60
ZIP_CODE_SIZE = 20
PASSWORD_HASH_SIZE = 130

COUNTRY_OFFICIAL_NAME_MAX_SIZE = 80  # largest country name has 56 chars...
COUNTRY_COMMON_NAME_MAX_SIZE = 80  # largest country name has 56 chars...
COUNTRY_NAME_MIN_SIZE = 3   # shortest country name has 4 chars...
COUNTRY_ISO_CODE_SIZE = 2   # ISO 3166-1 alpha 2 (2 letters)

TESTIMONIAL_TEXT_SIZE = 200

COURSE_TITLE_SIZE = 30
COURSE_SUMMARY_SIZE = 500
COURSE_DESC_SIZE = 1500

CATEGORY_NAME_SIZE = 30
CATEGORY_NAME_DESC = 100

LANGUAGE_ISO_CODE_SIZE = 2    # ISO 639 alpha 2 (2 letters)
LANGUAGE_NAME_MIN_SIZE = 2
LANGUAGE_NAME_SIZE = 20

################################################################################
##
##      DATA MODEL: User/Login/Acount Related Stuff
##
################################################################################

# NOTE: For now only Google is supported as an ExternalProvider and most
# of the parameters come from the server configuration (a Python file).
# This table contains only basic information about the provider

class ExternalProvider(SqlAlchemyBase):
    __tablename__ = 'ExternalProvider'

    id = Column(Integer, Identity(start = 30000), primary_key = True)
    name = Column(String(EXTERNAL_PROVIDER_NAME_SIZE), unique = True, nullable = False)
    end_point_url = Column(String(URL_SIZE), unique = True, nullable = False)
    active = Column(Boolean, nullable = False, server_default = '1')

    users_using = relationship(
        'UserLoginDataExternal', 
        back_populates = 'external_provider'
    )
#:

class UserLoginDataExternal(SqlAlchemyBase):
    __tablename__ = 'UserLoginDataExternal'

    id = Column(Integer, Identity(start = 20000), primary_key = True)
    user_id = Column(
        Integer, 
        ForeignKey('UserAccount.user_id'), 
        nullable = False
    )
    external_provider_id = Column(
        Integer, 
        ForeignKey('ExternalProvider.id'), 
        nullable = False
    )
    external_user_id = Column(
        String(USER_EXTERNAL_ID_TOKEN_MAX_SIZE),
        unique = True,
        nullable = False,
    )
    date_created =  Column(Date, nullable = False, server_default = func.current_date())

    external_provider = relationship('ExternalProvider', back_populates = 'users_using')
    user_account = relationship('UserAccount', back_populates = 'external_login_data')

    UniqueConstraint('user_id', 'external_provider_id', name = 'UserExternalProviderIDX')
#:

# As weird as it looks, we're actually adding the extra field(s) to the 
# superclass, and not just creating a subclass that extends the superclass.
# So we don't need the subclass name
class _(HashAlgo):
    date = Column(Date, nullable = False, server_default = func.current_date())
#:

class UserLoginData(SqlAlchemyBase, EmailAddrStatusMixin, HashAlgoMixin):
    __tablename__ = 'UserLoginData'
    
    user_id = Column(Integer, ForeignKey('UserAccount.user_id'), primary_key = True)
    password_hash = Column(String(PASSWORD_HASH_SIZE), nullable = False)
    email_addr = Column(String, unique = True, nullable = False)
    last_login = Column(DateTime)

    user_account = relationship(
        'UserAccount', 
        back_populates = 'user_login_data',
    )

    @property
    def fullname(self) -> str:
        return self.user_account.fullname
    #:

    __table_args__ = (
        CheckConstraint(
            # f'regexp("{EMAIL_REGEXP}", email_addr)', 
            f'email_addr REGEXP "{EMAIL_REGEXP}"', 
            name = 'EmailCK'
        ),
    )
#:

class UserAccount(SqlAlchemyBase, UserAccountStatusMixin):
    __tablename__ = 'UserAccount'

    user_id = Column(Integer, Identity(always = True, start = 5000), primary_key = True)
    type = Column(String(50))
    fullname = Column(String(FULLNAME_SIZE), nullable = False)
    birth_date = Column(Date, nullable = False)
    profile_image_url = Column(String(URL_SIZE), unique = True)
    address_line1 = Column(String(ADDRESS_LINE_SIZE))
    address_line2 = Column(String(ADDRESS_LINE_SIZE))
    zip_code = Column(String(ZIP_CODE_SIZE))
    country_iso_code = Column(String(COUNTRY_ISO_CODE_SIZE), ForeignKey('AcceptedCountry.iso_code'))
    date_created =  Column(Date, nullable = False, server_default = func.current_date())

    @property
    def firstname(self) -> str:
        return self.fullname.partition(' ')[0]
    #:

    @property
    def email_addr(self) -> str:
        return self.user_login_data.email_addr

    @email_addr.setter
    def email_addr(self, new_email_addr: str):
        self.user_login_data.email_addr = new_email_addr    # type: ignore

    @property
    def password_hash(self) -> str:
        return self.user_login_data.password_hash

    @password_hash.setter
    def password_hash(self, password_hash: str):
        self.user_login_data.password_hash = password_hash   # type: ignore

    @property
    def twitter(self) -> str | None:
        return self.social_network_addr('twitter')
    #:

    @property
    def facebook(self) -> str | None:
        return self.social_network_addr('facebook')
    #:

    @property
    def instagram(self) -> str | None:
        return self.social_network_addr('instagram')
    #:

    @property
    def linkedin(self) -> str | None:
            return self.social_network_addr('linkedin')
    #:

    def social_network_addr(self, type_: str) -> str | None:
        sn_enum = SocialNetworkEnum[type_]
        for sn_addr in self.social_network_addrs:  # type: ignore
            if sn_addr.social_network_type_id == sn_enum.id:
                return sn_addr.addr
        return None
    #:

    @property
    def country_name(self) -> str:
        if self.country:
            return self.country.name
        return ''
    #:

    # 'uselist = False' turns what was previously a one-to-many 
    # UserAccount.user_login_data relationship into a one-to-one
    user_login_data = relationship(
        'UserLoginData', 
        back_populates = 'user_account', 
        uselist = False,
        lazy = 'immediate',
    )
    external_login_data = relationship(
        'UserLoginDataExternal', 
        back_populates = 'user_account',
        # lazy = 'joined',
        lazy = 'immediate',
    )
    country = relationship(
        'AcceptedCountry', 
        back_populates = 'user_accounts',
        # lazy = 'joined',
        lazy = 'immediate',
    )
    social_network_addrs = relationship(
        'SocialNetworkAddr', 
        back_populates = 'user_account',
        # lazy = 'joined',
        lazy = 'immediate',
    )

    __table_args__ = (
        CheckConstraint(
            f'fullname REGEXP "{NAME_REGEXP}"', 
            name = 'NameCK'
        ),
    )

    __mapper_args__ = {
        'polymorphic_identity': 'UserAccount',
        'polymorphic_on': type,
    }
#:

class AcceptedCountry(SqlAlchemyBase):
    __tablename__ = 'AcceptedCountry'

    iso_code = Column(String(COUNTRY_ISO_CODE_SIZE), nullable = False, primary_key = True)
    name = Column(
        String(COUNTRY_COMMON_NAME_MAX_SIZE), nullable = False, unique = True,
        comment = 'Common name for this country'
    )
    official_name = Column(
        String(COUNTRY_OFFICIAL_NAME_MAX_SIZE), nullable = False, unique = True
    )

    user_accounts = relationship('UserAccount', back_populates = 'country')

    __table_args__ = (
        CheckConstraint(
            func.char_length(name) > COUNTRY_NAME_MIN_SIZE,
            name = 'NameLenCK'
        ),
        CheckConstraint(
            func.char_length(iso_code) == COUNTRY_ISO_CODE_SIZE,
            name = 'ISOCodeLenCK'
        ),
    )
#:

class SocialNetworkAddr(SqlAlchemyBase, SocialNetworkAddrMixin):
    __tablename__ = 'SocialNetworkAddr'

    id = Column(Integer, primary_key = True, autoincrement = 'auto')
    # type = Column(Enum(SocialNetworkType), nullable = False)
    addr = Column(String, nullable = False)
    user_id = Column(Integer, ForeignKey("UserAccount.user_id"))

    user_account = relationship('UserAccount', back_populates = 'social_network_addrs')
    UniqueConstraint('social_network_type_id', 'user_id', name = 'TypeUserIDIDX')
#:

class Student(UserAccount):
    __tablename__ = 'Student'

    user_id = Column(Integer, ForeignKey("UserAccount.user_id"), primary_key = True)

    testimonials = relationship(
        'Testimonial',
        back_populates = 'student',
    )
    courses = relationship(
        'Enrollment',
        back_populates = 'student',
    )

    __mapper_args__ = {
        'polymorphic_identity': 'Student',
    }
#:

class Testimonial(SqlAlchemyBase):
    __tablename__ = 'Testimonial'

    id = Column(Integer, primary_key = True, autoincrement = 'auto')
    text = Column(String(TESTIMONIAL_TEXT_SIZE), nullable = False)
    user_occupation = Column(String(50), nullable = False)
    date_created = Column(Date, nullable = False, server_default = func.current_date())
    user_id = Column(Integer, ForeignKey("Student.user_id"), nullable = False, unique = True)
    image_url = Column(String(URL_SIZE), unique = True, nullable = False)

    @property
    def user_name(self) -> str:
        return self.student.fullname
    #:

    student = relationship(
        'Student', 
        back_populates = 'testimonials',
        lazy = 'immediate',
    )
#:

class Instructor(UserAccount):
    __tablename__ = 'Instructor'

    user_id = Column(Integer, ForeignKey("UserAccount.user_id"), primary_key = True)
    presentation_image_url = Column(String(URL_SIZE), unique = True)
    presentation = Column(String, nullable = False)
    expertise_id = Column(Integer, ForeignKey("InstructorExpertise.id"), nullable = False)

    @property
    def expertise_title(self) -> str:
        return self.expertise.name
    #:

    expertise = relationship(
        'InstructorExpertise', 
        back_populates = 'instructors',
        # lazy = 'joined',
        lazy = 'immediate',
    )
    courses = relationship(
        'Course', 
        back_populates = 'instructor'
    )

    __mapper_args__ = {
        'polymorphic_identity': 'Instructor',
    }
#:

class InstructorExpertise(SqlAlchemyBase):
    __tablename__ = 'InstructorExpertise'

    id = Column(Integer, primary_key = True, autoincrement = 'auto')
    name = Column(String, nullable = False, unique = True)

    instructors = relationship('Instructor', back_populates = 'expertise')
#:

################################################################################
##
##      DATA MODEL: Course and Related Tables
##
################################################################################

class Category(SqlAlchemyBase):
    __tablename__ = 'Category'

    id = Column(Integer, Identity(start = 10001), primary_key = True)
    name = Column(String(CATEGORY_NAME_SIZE), unique = True, nullable = False)
    description = Column(String(CATEGORY_NAME_DESC), nullable = False)

    subcategories = relationship('SubCategory', back_populates = 'category')

    # UniqueConstraint('name', name = 'NameCatIDX')
#:

class SubCategory(SqlAlchemyBase):
    __tablename__ = 'SubCategory'

    id = Column(Integer, Identity(start = 20001), primary_key = True)
    name = Column(String(CATEGORY_NAME_SIZE), nullable = False)
    description = Column(String(CATEGORY_NAME_DESC), nullable = False)
    category_id = Column(Integer, ForeignKey("Category.id"), nullable = False)

    @property
    def category_name(self) -> str:
        return self.category.name
    #:

    category = relationship(
        'Category', 
        back_populates = 'subcategories',
        lazy = 'immediate',
    )
    courses = relationship(
        'Course', 
        back_populates = 'subcategory'
    )

    UniqueConstraint('name', 'category_id', name = 'NameSubCatIDX')
#:

class Course(SqlAlchemyBase, CourseStatusMixin):
    __tablename__ = 'Course'

    # id = Column(Integer, primary_key = True, autoincrement='auto')
    id = Column(Integer, Identity(start = 3001), primary_key = True)
    title = Column(String(COURSE_TITLE_SIZE), nullable = False)
    summary = Column(String(COURSE_SUMMARY_SIZE), nullable = False)
    description = Column(String(COURSE_DESC_SIZE), nullable = False)
    main_image_url = Column(String(URL_SIZE), nullable = False, unique = True)
    date_created =  Column(Date, nullable = False, server_default = func.current_date())
    last_updated_date =  Column(Date, nullable = False, server_default = func.current_date())
    # price = Column(Numeric(10,2), default=dec(0), nullable = False)
    price = Column(String(20), server_default='0.00', nullable = False)   # just for SQLite

    subcategory_id = Column(
        Integer,
        ForeignKey("SubCategory.id"),
        nullable = False,
    )
    instructor_id = Column(
        Integer,
        ForeignKey("Instructor.user_id"),
        nullable = False,
    )
    language_id = Column(
        Integer, 
        ForeignKey('AcceptedLanguage.iso_code'), 
        nullable = False,
        server_default = 'pt',
    )

    @property
    def subcategory_name(self) -> str:
        return self.subcategory.name
    #:

    @property
    def category_name(self) -> str:
        return self.subcategory.category_name
    #:

    @property
    def instructor_name(self) -> str:
        return self.instructor.fullname
    #:

    @property
    def instructor_presentation_image_url(self) -> str:
        return self.instructor.presentation_image_url
    #:

    subcategory = relationship(
        'SubCategory', 
        back_populates = 'courses', 
        innerjoin = True,
        # lazy = 'joined',
        lazy = 'immediate',
    )
    instructor = relationship(
        'Instructor',
        back_populates = 'courses',
        innerjoin = True,
        # lazy = 'joined',
        lazy = 'immediate',
    )
    language = relationship(
        'AcceptedLanguage',
        back_populates = 'courses',
        # lazy = 'joined',
        lazy = 'immediate',
    )
    students = relationship(
        'Enrollment',
        back_populates = 'course',
    )

    __table_args__ = (
        CheckConstraint(
            f'price >= 0',
            name = 'PriceCK'
        ),
    )
#:

class AcceptedLanguage(SqlAlchemyBase):
    __tablename__ = 'AcceptedLanguage'

    iso_code = Column(String(LANGUAGE_ISO_CODE_SIZE), primary_key = True)
    name = Column(String(LANGUAGE_NAME_SIZE), unique = True, nullable = False)

    courses = relationship('Course', back_populates = 'language')

    __table_args__ = (
        CheckConstraint(
            func.char_length(name) > LANGUAGE_NAME_MIN_SIZE,
            name = 'NameLenCK'
        ),
        CheckConstraint(
            func.char_length(iso_code) == LANGUAGE_ISO_CODE_SIZE,
            name = 'ISOCodeLenCK'
        ),
    )

#:

class Enrollment(SqlAlchemyBase):
    __tablename__ = "Enrollment"

    id = Column(Integer, Identity(start = 13001), primary_key = True)
    student_id = Column(ForeignKey('Student.user_id'), nullable = False)
    course_id = Column(ForeignKey('Course.id'), nullable = False)
    start_date =  Column(Date, nullable = False, server_default = func.current_date())
    end_date =  Column(Date, nullable = True)

    student = relationship('Student', back_populates = 'courses')
    course = relationship('Course', back_populates = 'students')

    UniqueConstraint('student_id', 'course_id', name = 'StudentCourseIDX')
#:

################################################################################
##
##      METADATA: Populate tables with initial metadata
##
################################################################################

def populate_metadata(db_session: Session):
    populate_enum_tables(db_session)
#: