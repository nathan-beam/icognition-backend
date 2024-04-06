from sentence_transformers import SentenceTransformer
from app.models import Document, Entity, Document_Embeddings

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
model.encode("Encode this on startup to avoid latency")

def generate_embeddings(term: str) -> list[float]:
    return model.encode(term)


async def get_document_embeddings(
    documents: list[Document],
) -> list[Document_Embeddings]:

    results = []
    for document in documents:

        results.append(
            Document_Embeddings(
                document_id=document.id,
                field="title",
                embeddings=model.encode(document.title),
            )
        )
        results.append(
            Document_Embeddings(
                document_id=document.id,
                field="short_summary",
                embeddings=model.encode(document.short_summary),
            )
        )
        for bullet_point in document.summary_bullet_points:
            results.append(
                Document_Embeddings(
                    document_id=document.id,
                    field="summary_bullet_points",
                    embeddings=model.encode(bullet_point),
                )
            )

    return results
