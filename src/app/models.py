from pgvector.sqlalchemy import Vector
from sqlmodel import SQLModel, Field, ARRAY, Float, Integer, String
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import TEXT
from typing import Optional, List
from datetime import datetime


class Bookmark(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str
    update_at: datetime.datetime = Field(
        default_factory=datetime.utcnow, nullable=False)
    document_id: Optional[int] = Field(default=None, nullable=True)


class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    url: str
    authors: List[float] = Field(sa_column=Column(ARRAY(Float)))
    summary_generated: str
    publication_date: datetime.datetime


class Keyphrase(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    word: str
    word_vec: List[float] = Field(sa_column=Column(Vector(384)))
    start: Optional[int] = Field(default=None)
    end: Optional[int] = Field(default=None)
    score: Optional[float] = Field(default=None)
    type: Optional[str] = Field(default=None)
    entity_group: Optional[str] = Field(default=None)
    context: Optional[str] = Field(default=None)
    context_vec: List[float] = Field(sa_column=Column(Vector(384)))
    document_id: Optional[int] = Field(default=None)


class WD_Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    label: Optional[str] = Field(default=None)
    description = Optional[TEXT] = Field(default=None)
    wikipedia_page_id: Optional[int]
    views: Optional[int]
    links: Optional[int]


class WD_Alias(SQLModel, table=True):
    id = Optional[int] = Field(default=None, primary_key=True)
    alias = Optional[str] = Field(default=None)
    lcase_alias = Optional[str] = Field(default=None)

# engine = create_engine('postgresql+psycopg2://app:2214@localhost/icognition')
