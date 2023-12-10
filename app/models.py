from pgvector.sqlalchemy import Vector
from sqlmodel import SQLModel, Field, ARRAY, Float, JSON
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import TEXT
from typing import Optional, List, Dict
from datetime import datetime


class URL(SQLModel, table=False):
    url: Optional[str] = Field(default=None)


class DocRequest(SQLModel, table=False):
    url: Optional[str] = Field(default=None, nullable=True)
    bookmark_id: Optional[int] = Field(default=None, nullable=True)
    document_id: Optional[int] = Field(default=None, nullable=True)


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
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(default=None)
    url: str = Field(default=None)
    original_text: str = Field(default=None, nullable=True)
    authors: List[float] = Field(sa_column=Column(ARRAY(Float)), default=None)
    summary_generated: str = Field(default=None)
    concepts_generated: str = Field(default=None)
    summary_bullet_points: str = Field(default=None)
    llama2_entities_raw: str = Field(default=None)
    spacy_entities_json: List = Field(default=[], sa_column=Column(JSON))
    publication_date: datetime = Field(default=None)
    update_at: datetime = Field(default_factory=datetime.utcnow, nullable=True)
    status: str = Field(default="Pending", nullable=True)


class DocArtifact(SQLModel, table=False):
    id: Optional[int] = Field(default=None, primary_key=True)


class Concept(DocArtifact, table=True):
    name: Optional[str] = Field(nullable=False)
    description: Optional[str] = Field(nullable=True)
    concept_vector: Optional[List[float]] = Field(
        sa_column=Column(Vector(384)), default=None, nullable=True
    )
    description_vector: Optional[List[float]] = Field(
        sa_column=Column(Vector(384)), default=None, nullable=True
    )
    history_json: Optional[List] = Field(default=[], sa_column=Column(JSON))


class ConceptDoc(SQLModel, table=True):
    concept_id: Optional[int] = Field(primary_key=True)
    document_id: Optional[int] = Field(primary_key=True)


class TLDR(DocArtifact, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    description: Optional[str] = Field(nullable=False)
    description_vector: Optional[List[float]] = Field(
        sa_column=Column(Vector(384)), default=None, nullable=True
    )


class TLDRDoc(SQLModel, table=True):
    tldr_id: Optional[int] = Field(primary_key=True)
    document_id: Optional[int] = Field(primary_key=True)


class Entity(DocArtifact, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(nullable=False)
    type: Optional[str] = Field(nullable=False)
    wikidata_id: Optional[str] = Field(nullable=True)
    description: Optional[str] = Field(nullable=True)


class EntitytDoc(SQLModel, table=True):
    entity_id: Optional[int] = Field(primary_key=True)
    document_id: Optional[int] = Field(primary_key=True)


class Keyphrase(DocArtifact, table=True):
    id: Optional[int] = Field(primary_key=True)
    word: str
    word_vec: List[float] = Field(sa_column=Column(Vector(384)), default=None)
    start: Optional[int] = Field(default=None)
    end: Optional[int] = Field(default=None)
    score: Optional[float] = Field(default=None)
    type: Optional[str] = Field(default=None)
    entity_group: Optional[str] = Field(default=None)
    context: Optional[str] = Field(default=None)
    context_vec: List[float] = Field(sa_column=Column(Vector(384)), default=None)


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
    update_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
