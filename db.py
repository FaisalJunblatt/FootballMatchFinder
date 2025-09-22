from sqlmodel import create_engine, SQLModel, Session

DB_URL = "sqlite:///app.db" # where the database is stored
engine = create_engine(DB_URL, echo=False) # if not there then create it

def init_db(): # create tables if they dont exist
    SQLModel.metadata.create_all(engine)


def get_session():  # like a notebook for each request
    with Session(engine) as session:
        yield session


