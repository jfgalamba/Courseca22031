# import sqlalchemy.ext.declarative
from sqlalchemy.orm import declarative_base, DeclarativeMeta
from sqlalchemy.engine import Engine


SqlAlchemyBase = declarative_base()

def create_metadata(engine: Engine):
    SqlAlchemyBase.metadata.drop_all(bind=engine)    # type: ignore
    SqlAlchemyBase.metadata.create_all(bind=engine)  # type: ignore
    # NOTE: Pylance doesn't recognize the 'metadata' attribute
#: