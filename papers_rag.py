import os
import chromadb
import anthropic
from pypdf import PdfReader

# ── Configuration ──────────────────────────────────────────────
PAPERS_DIR = "/Users/mustafaabushagur/my_papers"
CHROMA_DIR = "/Users/mustafaabushagur/papers_chroma_db"
API_KEY     = os.environ.get("ANTHROPIC_API_KEY", "")

# ── Step 1: Read all PDFs ───────────────────────────────────────
def load_papers(papers_dir):
    documents = []
    for filename in os.listdir(papers_dir):
        if filename.endswith(".pdf"):
            filepath = os.path.join(papers_dir, filename)
            try:
                reader = PdfReader(filepath)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                if text.strip():
                    documents.append({
                        "filename": filename,
                        "text": text
                    })
                    print(f"  ✓ Loaded: {filename}")
                else:
                    print(f"  ✗ Empty (scanned?): {filename}")
            except Exception as e:
                print(f"  ✗ Error reading {filename}: {e}")
    return documents

# ── Step 2: Split text into chunks ─────────────────────────────
def chunk_text(text, chunk_size=1000, overlap=200):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

# ── Step 3: Build ChromaDB index ───────────────────────────────
def build_index(documents):
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    
    # Delete old collection if exists
    try:
        client.delete_collection("papers")
    except:
        pass
    
    collection = client.create_collection("papers")
    
    all_chunks = []
    all_ids    = []
    all_metas  = []
    
    chunk_id = 0
    for doc in documents:
        chunks = chunk_text(doc["text"])
        for chunk in chunks:
            all_chunks.append(chunk)
            all_ids.append(f"chunk_{chunk_id}")
            all_metas.append({"source": doc["filename"]})
            chunk_id += 1
    
    # Add in batches of 100
    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        collection.add(
            documents=all_chunks[i:i+batch_size],
            ids=all_ids[i:i+batch_size],
            metadatas=all_metas[i:i+batch_size]
        )
    
    print(f"\n✓ Indexed {chunk_id} chunks from {len(documents)} papers")
    return collection

# ── Step 4: Query + Answer ──────────────────────────────────────
def ask(question, collection, n_results=5):
    results = collection.query(
        query_texts=[question],
        n_results=n_results
    )
    
    context = ""
    sources = set()
    for i, doc in enumerate(results["documents"][0]):
        source = results["metadatas"][0][i]["source"]
        sources.add(source)
        context += f"\n--- From: {source} ---\n{doc}\n"
    
    client = anthropic.Anthropic(api_key=API_KEY)
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""You are a research assistant for Professor Mustafa Abushagur.
Answer the question based on his published papers provided below.
Be specific and cite which paper the information comes from.

QUESTION: {question}

PAPERS:
{context}"""
        }]
    )
    
    print(f"\n{'='*60}")
    print(f"Q: {question}")
    print(f"{'='*60}")
    print(message.content[0].text)
    print(f"\nSources: {', '.join(sources)}")

# ── Main ────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Loading papers...")
    documents = load_papers(PAPERS_DIR)
    
    print(f"\nBuilding index...")
    collection = build_index(documents)
    
    print("\n✓ Ready! Ask questions about your research.\n")
    
    while True:
        question = input("Your question (or 'quit'): ").strip()
        if question.lower() == "quit":
            break
        if question:
            ask(question, collection)
