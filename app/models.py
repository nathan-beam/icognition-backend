from sqlmodel import SQLModel, Field, ARRAY, Float, JSON
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import TEXT
from typing import Optional, List, Dict
from datetime import datetime

### This is the code that will be used in the models.py file


class PagePayload(SQLModel, table=False):
    url: Optional[str] = Field(default=None)
    html: Optional[str] = Field(default=None)


class HTTPError(SQLModel, table=False):
    detail: Optional[str] = Field(default=None)


class Page(SQLModel, table=False):
    clean_url: Optional[str] = Field(default=None)
    title: Optional[str] = Field(default=None)
    author: Optional[str] = Field(default=None)
    paragraphs: Optional[List[str]] = Field(default=None)
    full_text: Optional[str] = Field(default=None)


class Bookmark(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(nullable=False)
    update_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    document_id: Optional[int] = Field(default=None, nullable=True)
    user_id: Optional[int] = Field(default=777, nullable=True)


class Document(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    title: str = Field(default=None)
    url: str = Field(default=None)
    original_text: str = Field(default=None, nullable=True)
    authors: List[float] = Field(sa_column=Column(ARRAY(Float)), default=None)
    short_summary: str = Field(default=None)
    summary_bullet_points: str = Field(default=[], sa_column=Column(JSON))
    raw_answer: str = Field(default=None)
    publication_date: datetime = Field(default=None)
    update_at: datetime = Field(default_factory=datetime.utcnow, nullable=True)
    status: str = Field(default="Pending", nullable=True)


class DocArtifact(SQLModel, table=False):
    id: Optional[int] = Field(default=None, primary_key=True)


# TODO: Add entities and concept tables
class Entity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: Optional[int] = Field(default=None)
    name: str = Field(default=None)
    description: str = Field(default=None)
    source: str = Field(default=None)
    type: str = Field(default=None)
    wikidata_id: str = Field(default=None)
    score: Optional[float] = Field(default=None)


class Concept(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: Optional[int] = Field(default=None)
    name: str = Field(default=None)
    description: str = Field(default=None)
    source: str = Field(default=None)


class DocumentPlus(SQLModel, table=False):
    document: Document
    concepts: Optional[List[Concept]]
    entities: Optional[List[Entity]]
