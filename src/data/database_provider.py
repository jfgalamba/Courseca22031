"""
Abstracts SQLAlchemy engine creation for each of the different
SQL providers (MySQL, SQL server, etc.)
"""

from abc import ABC
from abc import ABC, abstractmethod

from sqlalchemy import (
    create_engine,
)
from sqlalchemy.engine import Engine

class DBProvider(ABC):
    @abstractmethod
    def __init__(self, sqlalchemy_db_url: str, **__):
        self.sqlalchemy_db_url = sqlalchemy_db_url
    #:

    @classmethod
    def from_settings(cls, provider: str, **kargs) -> 'DBProvider':
        for subcls in cls.__subclasses__():
            if subcls.__name__ == provider:
                return subcls(**kargs)
        raise TypeError(f"Unknown database provider '{provider}'.")
    #:

    @abstractmethod
    def create_engine(self) -> Engine:
        pass
    #:
#:

class SQLite(DBProvider):
    def __init__(self, *, database: str, **kargs):
        super().__init__(
            sqlalchemy_db_url = f"sqlite+pysqlite:///{database}", **kargs
        )
    #:

    def create_engine(self) -> Engine:
        import sqlite_regex
        engine = create_engine(
            self.sqlalchemy_db_url, connect_args = {"check_same_thread": False}
        )
        dbapi_connection = engine.raw_connection()
        # dbapi_connect is compatible with sqlite3.Connection
        dbapi_connection.enable_load_extension(True)  # type: ignore
        sqlite_regex.load(dbapi_connection)           # type: ignore
        print("[+] ...loaded regexp extension")
        return engine
    #:
#:

class MySQL(DBProvider):
    def __init__(self, *, database: str, user: str, passwd: str, server: str):
        super().__init__(
            f"mysql+pymysql://{user}:{passwd}@{server}/{database}?charset=utf8mb4"
        )
    #:
    def create_engine(self) -> Engine:
        engine = create_engine(self.sqlalchemy_db_url)
        return engine
    #:
#:
