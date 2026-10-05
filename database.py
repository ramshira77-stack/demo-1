from sqlmodel import SQLModel,create_engine,Session,select , Field
from config import settings
from typing import List, Optional
from datetime import datetime , timezone

class users(SQLModel,table = True):
    u_id : Optional[int] = Field(default=None, primary_key=True)
    username : str = Field(nullable=False, unique=True)
    password : str = Field(nullable=False)

class messages(SQLModel,table = True):
    m_id : Optional[int] = Field(default=None, primary_key=True)
    u_id : int = Field(foreign_key="users.u_id")
    role : str
    content : str = Field(nullable=False)
    timestamp : datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


engine = create_engine(settings.dev_db_url)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

#Initialize DB
create_db_and_tables()