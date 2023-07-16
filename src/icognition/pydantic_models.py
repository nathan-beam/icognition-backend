from typing import Union
from pydantic import BaseModel
from datetime import datetime


class textBlob(BaseModel):
    source: Union[str, None] = None
    text: str


class Page(BaseModel):
    clean_url: Union[str, None] = None
    title: Union[str, None] = None
    clean_url: Union[str, None] = None
    paragraphs: Union[dict, None] = None
    full_text: Union[str, None] = None


class Bookmark(BaseModel):
    id: Union[int, None] = None
    url: Union[str, None] = None
    title: Union[str, None] = None
    update_at: Union[datetime, None] = None
    document_id: Union[int, None] = None

    class Config:
        orm_mode = True


class Document(BaseModel):
    id: Union[int, None] = None
    title: Union[str, None] = None
    url: Union[str, None] = None
    summary_generated: Union[str, None] = None
    publication_date: Union[str, None] = None
    authors: Union[list, None] = None

    class Config:
        orm_mode = True


class Keyphrase(BaseModel):
    id: Union[int, None] = None
    word: Union[str, None] = None
    start: Union[int, None] = None
    end: Union[int, None] = None
    score: Union[float, None] = None
    type: Union[str, None] = None
    entity_group: Union[str, None] = None
    context: Union[str, None] = None
    document_id: Union[int, None] = None

    class Config:
        orm_mode = True
