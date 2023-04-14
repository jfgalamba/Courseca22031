"""
This modules handles database connection and session creation aspects
of the app.

The SQLAlchemy Object Relational Mapper presents a method of associating
user-defined Python classes with database tables, and instances of those
classes (objects) with rows in their corresponding tables. It includes a
system that transparently synchronizes all changes in state between
objects and their related rows, called a unit of work, as well as a
system for expressing database queries in terms of the user defined
classes and their defined relationships between each other.

Links:
    https://fastapi.tiangolo.com/tutorial/sql-databases/#import-the-sqlalchemy-parts
"""

from contextlib import contextmanager
from typing import Callable

from sqlalchemy.orm import (
    sessionmaker,
    Session,
)

from data.database_provider import DBProvider
from data.model_base import create_metadata


SessionFactory: Callable[[], Session] | None = None;


def db_init(
        db_provider: DBProvider,
        create_datamodel = False,
        populate_metadata = False,
):
    global SessionFactory

    if not create_datamodel and populate_metadata:
        raise ValueError("'populate_with_metadata' implies 'create_datamodel'")

    engine = db_provider.create_engine()
    SessionFactory = sessionmaker(
        autocommit = False, 
        autoflush = False, 
        bind = engine
    )

    if create_datamodel:
        import data.models
        create_metadata(engine)

        if populate_metadata:
            with database_session() as db_session:
                data.models.populate_metadata(db_session)
#:

def get_db_session() -> Session:
    if not SessionFactory:
        msg = f'Database not initialized. Did you call {db_init.__name__}?'
        raise DatabaseConfigException(msg)
    return SessionFactory()
#:

@contextmanager
def database_session(db_session: Session | None = None):
    manage_session = False
    if db_session is None:
        db_session = get_db_session()
        manage_session = True
    try:
        yield db_session
    finally:
        if manage_session:
            db_session.close()
#:

class DatabaseConfigException(Exception):
    pass
#:
