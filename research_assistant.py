
import streamlit as st
import chromadb
import anthropic
import os
from pypdf import PdfReader

# Configuration
PAPERS_DIR = "/Users/mustafaabushagur/my_papers"
CHROMA_DIR = "/Users/mustafaabushagur/papers_chroma_db"
from dotenv import load_dotenv
load_dotenv("/Users/mustafaabushagur/.env")
api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()

# Page configuration
st.set_page_config(
    page_title="Prof. Abushagur Research Assistant",
    page_icon="🔬",
    layout="centered"
)

# Header
st.title("🔬 Research Assistant")
st.subheader("Professor Mustafa Abushagur — Photonics Research 1980–2021")
st.markdown("---")

# Smart incremental index update
def update_index(collection, papers_dir):
    existing = set()
    for m in collection.get()["metadatas"]:
        existing.add(m["source"])

    new_papers = 0
    for filename in os.listdir(papers_dir):
        if not filename.endswith(".pdf"):
            continue
        if filename in existing:
            continue
        filepath = os.path.join(papers_dir, filename)
        try:
            reader = PdfReader(filepath)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            if not text.strip():
                continue
            chunks = []
            start = 0
            while start < len(text):
                chunks.append(text[start:start+1000])
                start += 800
            ids = [f"{filename}_chunk_{i}" for i in range(len(chunks))]
            metas = [{"source": filename}] * len(chunks)
            for i in range(0, len(chunks), 100):
                collection.add(
                    documents=chunks[i:i+100],
                    ids=ids[i:i+100],
                    metadatas=metas[i:i+100]
                )
            new_papers += 1
            st.toast(f"Added: {filename}")
        except Exception as e:
            st.warning(f"Could not read {filename}: {e}")
    return new_papers

# Load ChromaDB
@st.cache_resource
def load_collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        return client.get_collection("papers")
    except:
        return client.create_collection("papers")

collection = load_collection()
total = collection.count()
st.success(f"✓ {total} chunks loaded from your papers")

# Sidebar
with st.sidebar:
    st.header("About")
    st.markdown("""
    This assistant searches Professor Abushagur's 
    published research papers to answer questions.

    **Coverage:** 1980 – 2021

    **Topics include:**
    - Fiber Bragg Grating sensors
    - Optical computing
    - Nanoplasmonic waveguides
    - WDM and fiber optics
    - Pattern recognition
    - Silicon photonics
    - Polarimetry
    """)

    st.markdown("---")

    if st.button("🔄 Update index with new papers"):
        with st.spinner("Checking for new papers..."):
            new = update_index(collection, PAPERS_DIR)
            if new > 0:
                st.success(f"Added {new} new papers!")
                st.rerun()
            else:
                st.info("No new papers found.")

    if st.button("🗑️ Clear conversation"):
        st.session_state.messages = []
        st.rerun()

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Question input
if question := st.chat_input("Ask about Professor Abushagur's research..."):

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching papers..."):

            results = collection.query(
                query_texts=[question],
                n_results=5
            )

            context = ""
            sources = set()
            for i, doc in enumerate(results["documents"][0]):
                source = results["metadatas"][0][i]["source"]
                sources.add(source)
                context += f"\n--- From: {source} ---\n{doc}\n"

            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": f"""You are a research assistant for Professor Mustafa Abushagur,
a photonics expert at RIT with papers spanning 1980-2021.
Answer based on his papers below. Cite the paper for each point.
Format clearly with sections if needed.

QUESTION: {question}

PAPERS:
{context}"""
                }]
            )

            answer = message.content[0].text
            source_list = "\n\n**Sources:** " + ", ".join(
                [s.replace(".pdf", "") for s in sources]
            )
            full_answer = answer + source_list
            st.markdown(full_answer)
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_answer
            })
