from qdrant_client import QdrantClient
from qdrant_client import models
import hashlib
import openai
from app.config import OPEN_AI_API_KEY, QDRANT_URL
from qdrant_client.http import models as http_models

client = QdrantClient(QDRANT_URL)

if "pdf_chunks" not in [c.name for c in client.get_collections().collections]:
    client.create_collection(
        collection_name="pdf_chunks", vectors_config={"size": 1536, "distance": "Cosine"}
    )
else:
    print("Collection already exists, skipping creation")

openai.api_key = OPEN_AI_API_KEY


def store_pdf_in_qdrant(text_pages, user_id):
    """
    Reads a PDF file (bytes), converts each page to text,
    generates embeddings for each page, and stores them
    as points in a Qdrant collection.
    """
    global client
    points = []
    print("Inside store_pdf_in_qdrant")

    for page_text in text_pages:
        page_id = hashlib.md5(page_text.encode("utf-8")).hexdigest()
        print(f"PageId: {page_id}")

        # Generate the embedding for this chunk of text
        resp = openai.Embedding.create(
            input=page_text, model="text-embedding-ada-002"  # returns 1536-dim vector
        )
        print(f"response for embeddings: {resp}")
        embedding = resp.data[0].embedding
        print(f"Printing embeddings: {embedding}")

        # Prepare a Qdrant "point" (vector + metadata)
        points.append(
            models.PointStruct(
                id=page_id,  # unique id for the point
                vector=embedding,  # the vector itself
                payload={"content": page_text, "user_id": user_id},  # metadata, e.g. raw text
            )
        )

    client.upsert(collection_name="pdf_chunks", points=points)

def search_context(query_text: str, user_id: str, top_k: int = 5):
    """
    Generate embedding for a user query and retrieve the top_k most similar PDF chunks
    belonging to the given user_id.
    """
    # Creating embedding for the query
    query_embedding = openai.Embedding.create(
        input=query_text,
        model="text-embedding-ada-002"
    ).data[0].embedding
    print(query_embedding)

    # Building a filter for user_id
    user_filter = http_models.Filter(
        must=[
            http_models.FieldCondition(
                key="user_id",
                match=http_models.MatchValue(value=user_id)
            )
        ]
    )

    # Searching in Qdrant
    search_results = client.search(
        collection_name="pdf_chunks",
        query_vector=query_embedding,
        limit=top_k,
        query_filter=user_filter
    )

    # Extracting the content chunks
    context_chunks = [hit.payload["content"] for hit in search_results]

    return context_chunks

"""
For Understanding
What is distance in a vector DB?

When you store embeddings (vectors), the database needs to know how to measure similarity between them when you run a search. This is what the distance parameter controls.

Vector search ≈ “find the nearest vectors to my query vector”.
But “nearest” depends on which metric you choose:
1. Cosine similarity (Distance.COSINE)
Looks at the angle between vectors. Ignores their length. 
Higher cosine similarity = more semantically similar.
NLP, embeddings from OpenAI, text/doc search

2. Dot product / Inner product (Distance.DOT)
Multiplies corresponding components and sums. Sensitive to magnitude (length) and direction. Works well when your model produces normalized vectors already.
Recommendation systems, some transformer embeddings

3. Euclidean distance (L2) (Distance.EUCLID)
Straight-line distance between points in high-dim space. Sensitive to vector magnitude.
Image embeddings, some metric learning tasks
"""