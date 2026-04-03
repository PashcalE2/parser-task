from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..settings import settings
from .models import Base

engine = create_engine(url=settings.DB_URI, pool_pre_ping=True)
DBSession = sessionmaker(bind=engine)


def create_all():
    Base.metadata.create_all(engine)
