from pgvector.sqlalchemy import Vector
from sqlmodel import SQLModel, Field, ARRAY, Float, Integer, String
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import TEXT
from typing import Optional, List
from datetime import datetime


class Bookmark(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str
    update_at: datetime = Field(
        default_factory=datetime.utcnow, nullable=False)
    document_id: Optional[int] = Field(default=None, nullable=True)


class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(default=None)
    url: str
    authors: List[float] = Field(sa_column=Column(ARRAY(Float)))
    summary_generated: str = Field(default=None)
    publication_date: datetime = Field(default=None)


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
    description: Optional[str] = Field(default=None)
    wikipedia_page_id: Optional[int] = Field(default=None)
    views: Optional[int] = Field(default=None)
    links: Optional[int] = Field(default=None)


class WD_Alias(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    alias: Optional[str] = Field(default=None)
    lcase_alias: Optional[str] = Field(default=None)


class WD_ItemVector(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: Optional[str] = Field(default=None)
    wikidata_id: Optional[int] = Field(default=None)
    text_vec: List[float] = Field(sa_column=Column(Vector(384)))
    update_at: datetime = Field(
        default_factory=datetime.utcnow, nullable=False)
