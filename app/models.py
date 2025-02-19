from sqlmodel import SQLModel, Field, ARRAY, Float, JSON, Integer
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import TEXT, JSONB
from pgvector.sqlalchemy import Vector
from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel


"""
The SQLModel class is used to define the database schema (when table=True) or to define FastApi payload and response models (when table=False).    
"""


class PagePayload(SQLModel, table=False):
    """
    Represents the payload for a page, including its URL and HTML content.
    """

    url: Optional[str] = Field(default=None)
    html: Optional[str] = Field(default=None)
    user_id: str = Field(default=None, nullable=True)


class HTTPError(SQLModel, table=False):
    """
    Represents an HTTP error with a detail message.
    """

    detail: Optional[str] = Field(default=None)


class SearchPayload(SQLModel, table=False):
    """
    Represents the payload for a search, including the query and user ID.
    """

    query: Optional[str] = Field(default=None)
    user_id: Optional[str] = Field(default=None)


class Page(SQLModel, table=False):
    """
    Represents a web page with its clean URL, title, author, paragraphs, and full text.
    """

    clean_url: Optional[str] = Field(default=None)
    title: Optional[str] = Field(default=None)
    author: Optional[str] = Field(default=None)
    paragraphs: Optional[List[str]] = Field(default=None)
    full_text: Optional[str] = Field(default=None)


class Bookmark(SQLModel, table=True):
    """
    Represents a bookmark with its ID, URL, update timestamp, document ID, and user ID.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(nullable=False)
    update_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    document_id: Optional[int] = Field(default=None, nullable=True)
    user_id: Optional[str] = Field(nullable=False)
    cloned_documents: List[int] = Field(default=[], sa_column=Column(ARRAY(Integer)))


class Document(SQLModel, table=True):
    """
    Represents a document with its ID, title, URL, original text, authors, short summary, summary bullet points,
    raw answer, publication date, update timestamp, and status.
    """

    id: int = Field(default=None, primary_key=True)
    title: str = Field(default=None, nullable=True)
    url: str = Field(default=None, nullable=True)
    original_text: str = Field(default=None, nullable=True)
    authors: List[float] = Field(sa_column=Column(ARRAY(Float)), default=[])
    short_summary: str = Field(default=None, nullable=True)
    is_about: str = Field(default=None, nullable=True)
    summary_bullet_points: List[str] = Field(default=[], sa_column=Column(JSON))
    raw_answer: str = Field(default=None, nullable=True)
    publication_date: datetime = Field(default=None, nullable=True)
    update_at: datetime = Field(default_factory=datetime.utcnow, nullable=True)
    status: str = Field(default="Pending", nullable=True)
    llm_service_meta: Optional[Dict] = Field(default={}, sa_column=Column(JSONB))


class Document_Embeddings(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    document_id: int = Field(nullable=False)
    field: str = Field(default=None, nullable=True)
    embeddings: List[float] = Field(sa_column=Column(Vector(384)))


class DocArtifact(SQLModel, table=False):
    """
    Represents a document artifact with its ID.
    """

    id: Optional[int] = Field(default=None, primary_key=True)


class Entity(SQLModel, table=True):
    """
    Represents an entity with its ID, document ID, name, description, source, type, Wikidata ID, and score.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: Optional[int] = Field(default=None)
    name: str = Field(default=None)
    description: str = Field(default=None, nullable=True)
    source: str = Field(default=None, nullable=True)
    type: str = Field(default=None, nullable=True)
    wikidata_id: str = Field(default=None, nullable=True)
    score: Optional[float] = Field(default=None, nullable=True)


""" 
The pydantic class is used to give JSON Schema to the Together.AI API. See how it's being used in togeher_api_client.py 
Why I used Pydantic instead of SQLModel? Good question, in my testing I was not able to get a complete JSON Schema from SQLModel.
"""


class IdentifyEntity(BaseModel):
    name: Optional[str]
    type: Optional[str]
    explanation: Optional[str]


class DocumentJsonForLLMS(BaseModel):
    oneSentenceSummary: Optional[str]
    whatThisArticleIsAbout: Optional[str] 
    summaryInNumericBulletPoints: Optional[List[str]]
    entities_and_concepts: Optional[List[IdentifyEntity]]
    usage: Optional[str]


class DocumentDisplay(BaseModel):
    id: Optional[int]
    title: Optional[str]
    url: Optional[str] = None
    authors: Optional[List[str]] = None
    publicationDate: Optional[str] = None
    llmServiceMeta: Optional[Dict] = None
    status: Optional[str] = None
    updateAt: Optional[datetime] = None
    oneSentenceSummary: Optional[str] = None
    is_about: Optional[str] = None
    tldr: Optional[List[str]] = None
    entities_and_concepts: Optional[List[Entity]] = None
    usage: Optional[str] = None
    cosine_similarity: Optional[float] = None

    @classmethod
    def from_orm(cls, document: Document, entities: List[Entity] = None, cosine_similarity: float = None):
        return cls(
            id=document.id,
            title=document.title,
            url=document.url,
            authors=document.authors,
            tldr=document.summary_bullet_points,
            publicationDate=document.publication_date,
            llmServiceMeta=document.llm_service_meta,
            status=document.status,
            updateAt=document.update_at,
            oneSentenceSummary=document.short_summary,
            is_about=document.is_about,
            entities_and_concepts=entities,
            cosine_similarity=cosine_similarity,
        )
