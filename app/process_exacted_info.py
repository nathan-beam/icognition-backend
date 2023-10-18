import logging, re, sys, json
from app import app_logic
from app.models import Document, Concept, TLDR, Entity

from sqlalchemy import select, delete, create_engine, and_, Integer, String, func
from sqlalchemy.orm import Session
from dotenv import dotenv_values

logging.basicConfig(
    stream=sys.stdout,
    format="%(asctime)s - %(message)s",
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)


class ProcessConcepts:
    def __init__(self) -> None:
        self.regexs = [
            r"\d\.(.*?)[\:|\-](.*)",
            r"\d\..*?\<c>(.*?)<\/c>\<e>(.*?)<\/e>",
            r"\d\.(.*?)\<e>(.*)\<\/e>",
            r"\d\.(.*)\B",
        ]
        pass

    async def __call__(
        self, document_id: int = None, doc: Document = None
    ) -> list[Concept]:
        # if doc is None, use document_id to retrive document object
        if not doc and document_id:
            doc = app_logic.get_document_by_id(document_id)
        else:
            raise ValueError(
                "Niether document_id or Document were supplied to ProcessConcepts"
            )
        raw_concepts = doc.concepts_generated

        results = []
        for line in raw_concepts.splitlines():
            # Skip empyt and short lines
            if len(line) < 2:
                continue

            # For each regex, look for concepts and explanation
            for regex in self.regexs:
                match = re.match(regex, line)
                print(line)
                if match:
                    name = match.group(1).strip() if match.group(1) else None
                    desc = match.group(2).strip() if (len(match.groups()) > 1) else None
                    id = int(f"{document_id}{len(results)+1}")
                    con = Concept(
                        id=id, name=name, description=desc, document_id=document_id
                    )
                    results.append(con)
                    break  # stop testing different regex

        return results


class ProcessEntities:
    def __init__(self) -> None:
        self.regexs = [
            r"\d\.(.*?)[\:|\-](.*)",
        ]
        self.spacy_labels = [
            "ORG",
            "PERSON",
            "WORK_OF_ART",
            "NORP",
            "EVENT",
            "GPE",
            "LOC",
            "PRODUCT",
        ]
        pass

    async def __call__(
        self, document_id: int = None, doc: Document = None
    ) -> list[Entity]:
        if not doc and document_id:
            doc = app_logic.get_document_by_id(document_id)
        else:
            raise ValueError(
                "Niether document_id or Document were supplied to ProcessConcepts"
            )
        raw_spacy_entities = doc.spacy_entities_json

        spacy_ent = await self.spacy_entities(doc.id, raw_spacy_entities)

        return spacy_ent

    async def spacy_entities(self, document_id, entities) -> list[Entity]:
        results = []
        filtered = [e for e in entities if e["label"] in self.spacy_labels]
        for f in filtered:
            id = int(f"{document_id}{len(results)+1}")
            ent = Entity(
                id=id,
                document_id=document_id,
                name=f["text"],
                type=f["label"],
                wikidata_id=f["wikidata_id"],
                description=f["description"],
            )
            results.append(ent)

        return results
