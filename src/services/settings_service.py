from sqlalchemy import select
from sqlalchemy.orm import Session

from data.database import database_session
from data.models import (
    AcceptedCountry,
    AcceptedLanguage,
    Category,
    SubCategory,
    ExternalProvider,
)


__all__ = (
    'accept_country',
    'accept_language',
    'create_category',
    'create_subcategory',
    'accept_external_auth_provider',
    'get_external_auth_providers',
)


def accept_country(
        iso_code: str,
        name: str,
        official_name: str,
        db_session: Session | None = None,
) -> AcceptedCountry:
    with database_session(db_session) as db_session:
        db_session.add(
            country := AcceptedCountry(
                iso_code = iso_code,
                name = name,
                official_name = official_name,
            )
        )
        db_session.commit()
        return country
#:

def get_accepted_countries(
        db_session: Session | None = None,
) -> list[AcceptedCountry]:
    with database_session(db_session) as db_session:
        select_stmt = select(AcceptedCountry)
        return db_session.execute(select_stmt).scalars().all()
#:

def accept_language(
        iso_code: str,
        name: str,
        db_session: Session | None = None,
) -> AcceptedLanguage:
    with database_session(db_session) as db_session:
        db_session.add(
            language := AcceptedLanguage(
                iso_code = iso_code,
                name = name,
            )
        )
        db_session.commit()
        db_session.refresh(language)
        return language
#:

def create_category(
        name: str,
        description: str,
        db_session: Session | None = None,
) -> Category:
    with database_session(db_session) as db_session:
        db_session.add(
            cat := Category(
                name = name,
                description = description,
            )
        )
        db_session.commit()
        db_session.refresh(cat)
        return cat
#:

def create_subcategory(
        name: str,
        description: str,
        category_id: int,
        db_session: Session | None = None,
) -> SubCategory:
    with database_session(db_session) as db_session:
        db_session.add(
            subcat := SubCategory(
                name = name,
                description = description,
                category_id = category_id,
            )
        )
        db_session.commit()
        db_session.refresh(subcat)
        return subcat
#:

def accept_external_auth_provider(
        name: str,
        end_point_url: str,
        db_session: Session | None = None,
) -> AcceptedCountry:
    with database_session(db_session) as db_session:
        db_session.add(
            eap := ExternalProvider(
                name = name,
                end_point_url = end_point_url,
            )
        )
        db_session.commit()
        db_session.refresh(eap)
        return eap
#:

def get_external_auth_providers(
    db_session: Session | None = None,
) -> list[ExternalProvider]:
    with database_session(db_session) as db_session:
        select_stmt = select(ExternalProvider).where(ExternalProvider.active == True)
        return db_session.execute(select_stmt).scalars().all()
#:

def get_external_provider_by_id(
    external_provider_id: int,
    db_session: Session | None = None,
) -> ExternalProvider | None:
    with database_session(db_session) as db_session:
        select_stmt = (
            select(ExternalProvider)
            .where(ExternalProvider.id == external_provider_id)
            .where(ExternalProvider.active == True)
        )
        return db_session.execute(select_stmt).scalar_one_or_none()
#:

def get_external_provider_by_name(
    name: str,
    db_session: Session | None = None,
) -> ExternalProvider | None:
    with database_session(db_session) as db_session:
        select_stmt = (
            select(ExternalProvider)
            .where(ExternalProvider.name == name)
            .where(ExternalProvider.active == True)
        )
        return db_session.execute(select_stmt).scalar_one_or_none()
#: