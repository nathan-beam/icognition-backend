from app.process_exacted_info import ProcessConcepts, ProcessEntities
from app import app_logic
from app.models import Entity


def test_concept_processor():
    docs_ids = app_logic.get_documents_ids()
    process_concepts = ProcessConcepts()

    for id in docs_ids:
        concepts = process_concepts(id)

        for concept in concepts:
            assert concept.document_id is not None
            assert concept.name is not None
            assert type(concept.name) == str
            assert len(concept.name) > 0
            if concept.description:
                assert type(concept.description) == str
                assert len(concept.description) > 0


async def test_entities_processor():
    docs_ids = app_logic.get_documents_ids()
    process_entities = ProcessEntities()

    for id in docs_ids:
        entities = await process_entities(id)
        for entity in entities:
            assert type(entity) == Entity
            assert len(entity.name) > 0
