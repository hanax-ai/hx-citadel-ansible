"""Database utilities"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def get_async_engine(database_url: str):
    """Create async database engine"""
    return create_async_engine(
        database_url,
        echo=False,
        future=True
    )


def get_async_session_maker(engine):
    """Create async session maker"""
    return sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
