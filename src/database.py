from sqlmodel import Session, SQLModel, create_engine

from config import settings

db_url = settings.database_url

engine = create_engine(db_url, echo=True)


def create_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
