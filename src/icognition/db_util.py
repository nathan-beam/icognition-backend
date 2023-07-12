from pgvector.sqlalchemy import Vector
from sqlalchemy import MetaData, create_engine, Integer, String, func
from typing import Optional
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.dialects.postgresql import TEXT, DATE, TIME, TIMESTAMP, FLOAT, ARRAY
from sqlalchemy.sql.schema import ForeignKey

Base = declarative_base()
metadata_obj = MetaData()


class Item(Base):
    __tablename__ = "items"
    __table_args__ = {"schema": "wikidata", 'extend_existing': True}
    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(), nullable=False)
    description = mapped_column(TEXT)
    wikipedia_page_id: Mapped[Optional[int]]
    views: Mapped[Optional[int]]
    links: Mapped[Optional[int]]

    def __repr__(self) -> str:
        return f"Items(id={self.id!r}, label={self.label!r}, description={self.description!r})"


class Alias(Base):
    __tablename__ = "aliases"
    __table_args__ = {"schema": "wikidata", 'extend_existing': True}
    id = mapped_column(Integer, primary_key=True)
    alias = mapped_column(String(), nullable=False)
    lcase_alias = mapped_column(String(), nullable=False)

    def __repr__(self) -> str:
        return f"Aliases(id={self.id!r}, alias={self.alias!r})"


class ItemVector(Base):
    __tablename__ = "items_vectors"
    __table_args__ = {"schema": "wikidata", 'extend_existing': True}
    id = mapped_column(Integer, primary_key=True)
    text = mapped_column(String())
    wikidata_id = mapped_column(Integer)
    text_vec = mapped_column(Vector(384))
    update_at = mapped_column(TIMESTAMP, onupdate=func.now())


class Bookmark(Base):
    # TODO Add user_id to Bookmark
    __tablename__ = "bookmarks"
    __table_args__ = {"schema": "bmks", "extend_existing": True}
    id = mapped_column(Integer, primary_key=True)
    url = mapped_column(String(255))
    update_at = mapped_column(TIMESTAMP, onupdate=func.now())
    document_id = mapped_column(Integer)


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = {"schema": "bmks", "extend_existing": True}
    id = mapped_column(Integer, primary_key=True)
    title = mapped_column(String(255))
    url = mapped_column(String(255))
    authors = mapped_column(ARRAY(String, dimensions=1))
    summary_generated = mapped_column(TEXT)
    publication_date = mapped_column(DATE())


class Keyphrase(Base):
    __tablename__ = "keyphrases"
    __table_args__ = {"schema": "bmks", "extend_existing": True}
    id = mapped_column(Integer, primary_key=True)
    word = mapped_column(String())
    word_vec = mapped_column(Vector(384))
    start = mapped_column(Integer)
    end = mapped_column(Integer)
    score = mapped_column(FLOAT)
    type = mapped_column(String())
    entity_group = mapped_column(String(50))
    context = mapped_column(String(255))
    context_vec = mapped_column(Vector(384))
    document_id = mapped_column(Integer)


engine = create_engine('postgresql+psycopg2://app:2214@localhost/icognition')
