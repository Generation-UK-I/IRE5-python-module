import ollama
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import requests
from bs4 import BeautifulSoup

# Configuration constants
QDRANT_HOST = "http://localhost:6333"
OLLAMA_HOST = "http://localhost:11434"
COLLECTION_NAME = "enterprise_knowledge"
EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "llama3.2"

# Initialize clients (check_compatibility=False silences version mismatch warnings)
qdrant_client = QdrantClient(url=QDRANT_HOST, check_compatibility=False)
ollama_client = ollama.Client(host=OLLAMA_HOST)

def init_vector_db():
    """Creates the Qdrant collection if it does not exist."""
    if not qdrant_client.collection_exists(COLLECTION_NAME):
        print(f"Creating collection: {COLLECTION_NAME}")
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )

def fetch_webpage(url: str) -> str:
    headers = {
        "User-Agent": "RAG-Demo/1.0 (Educational Project)"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for script in soup(["script", "style"]):
        script.decompose()

    return soup.get_text(separator=" ", strip=True)

def ingest_documents(docs: list[str]):
    """Embeds raw text documents and inserts them into Qdrant."""
    init_vector_db()
    
    for idx, doc_text in enumerate(docs):
        response = ollama_client.embed(model=EMBED_MODEL, input=doc_text)
        vector = response['embeddings'][0]
        
        point = PointStruct(
            id=idx,
            vector=vector,
            payload={"text": doc_text}
        )
        
        qdrant_client.upsert(collection_name=COLLECTION_NAME, points=[point])
    print(f"Successfully ingested {len(docs)} document chunks.")

def chunk_text(text: str, chunk_size=500):
    """Splits large text into smaller chunks."""
    
    words = text.split()
    
    chunks = [
        " ".join(words[i:i + chunk_size])
        for i in range(0, len(words), chunk_size)
    ]
    
    return chunks

def query_rag(user_question: str) -> str:
    """Retrieves context from Qdrant and prompts the LLM for an answer."""
    # Step 1: Embed query
    query_vector = ollama_client.embed(model=EMBED_MODEL, input=user_question)['embeddings'][0]
    
    # Step 2: Query Qdrant using the updated query_points API
    search_results = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=2
    )
    
    # Step 3: Extract payload from search_results.points
    retrieved_contexts = [point.payload["text"] for point in search_results.points]
    context_block = "\n---\n".join(retrieved_contexts)
    
    # Step 4: Construct system prompt
    system_prompt = (
        "You are a helpful assistant. Use ONLY the provided Context below to answer the Question.\n"
        "If the context does not contain the answer, say 'I cannot find that in the local database.'\n\n"
        f"Context:\n{context_block}"
    )
    
    # Step 5: Generate response
    output = ollama_client.generate(
        model=LLM_MODEL,
        system=system_prompt,
        prompt=user_question
    )
    return output['response']

def reset_collection():
    if qdrant_client.collection_exists(COLLECTION_NAME):
        qdrant_client.delete_collection(COLLECTION_NAME)

    init_vector_db()

if __name__ == "__main__":

    url = input("Enter a URL: ")

    print("\nDownloading webpage...")
    page_text = fetch_webpage(url)
    print("\nPreview of downloaded content:")
    print(page_text[:500])

    print("Chunking content...")
    chunks = chunk_text(page_text)

    print(f"Created {len(chunks)} chunks")

    reset_collection()
    ingest_documents(chunks)

    while True:
        question = input("\nAsk a question (or 'quit'): ")

        if question.lower() == "quit":
            break

        answer = query_rag(question)

        print(f"\nAnswer: {answer}")