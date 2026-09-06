import streamlit as st
import chromadb
import anthropic
import pypdf

st.set_page_config(page_title="Applied Photonics Assistant", page_icon="📚", layout="wide")
st.title("Applied Photonics — AI Study Assistant")
st.markdown("*Based on* **Applied Photonics** *by Prof. Mustafa A.G. Abushagur, Springer 2025*")
st.divider()

with st.sidebar:
    st.header("Setup")
    api_key = st.text_input("Anthropic API Key", type="password", placeholder="sk-ant-api03-...")
    st.markdown("---")
    st.header("Chapter Filter")
    chapters = {
        "All chapters": (1, 576),
        "Ch 2 — Geometrical Optics": (9, 42),
        "Ch 3 — Physical Optics": (43, 104),
        "Ch 4 — Fourier Optics": (105, 154),
        "Ch 7 — Optical Waveguides": (225, 258),
        "Ch 8 — Optical Fibers": (259, 294),
        "Ch 15 — Fiber Communication": (519, 576),
    }
    selected_chapter = st.selectbox("Search in:", list(chapters.keys()))
    page_min, page_max = chapters[selected_chapter]
    st.markdown("---")
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()

@st.cache_resource
def load_book_and_index():
    pdf_path = "Applied_Photonics_Book.pdf"
    reader = pypdf.PdfReader(pdf_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and len(text.strip()) > 50:
            pages.append({"page_num": i + 1, "text": text.strip()})
    chunks = []
    for page in pages:
        words = page["text"].split()
        page_num = page["page_num"]
        start = 0
        while start < len(words):
            chunk_text = " ".join(words[start:start+500])
            if len(chunk_text.strip()) > 100:
                chunks.append({"chunk_id": f"page{page_num}_chunk{len(chunks)}", "page_num": page_num, "text": chunk_text})
            start += 450
    chroma_client = chromadb.Client()
    try:
        collection = chroma_client.create_collection("applied_photonics")
        for i in range(0, len(chunks), 50):
            batch = chunks[i:i+50]
            collection.add(ids=[c["chunk_id"] for c in batch], documents=[c["text"] for c in batch], metadatas=[{"page_num": c["page_num"]} for c in batch])
    except Exception:
        collection = chroma_client.get_collection("applied_photonics")
    return collection

def ask_book(question, collection, api_key, history, page_min, page_max):
    where_filter = None
    if page_min > 1 or page_max < 576:
        where_filter = {"$and": [{"page_num": {"$gte": page_min}}, {"page_num": {"$lte": page_max}}]}
    query_params = {"query_texts": [question], "n_results": 3}
    if where_filter:
        query_params["where"] = where_filter
    results = collection.query(**query_params)
    retrieved_chunks = results["documents"][0]
    page_numbers = [m["page_num"] for m in results["metadatas"][0]]
    context = ""
    for chunk, page in zip(retrieved_chunks, page_numbers):
        context += f"\n--- Excerpt from page {page} ---\n{chunk}\n"
    system_prompt = """You are an expert teaching assistant for Applied Photonics by Prof. Mustafa A.G. Abushagur (Springer 2025). Answer using ONLY the excerpts provided. Be precise and technical. Reference page numbers. Render equations in LaTeX using $$ for display equations."""
    messages = list(history)
    messages.append({"role": "user", "content": f"Book excerpts:\n{context}\n\nQuestion: {question}"})
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(model="claude-sonnet-4-6", max_tokens=1024, system=system_prompt, messages=messages)
    return message.content[0].text, page_numbers

if "messages" not in st.session_state:
    st.session_state.messages = []

if not api_key:
    st.info("Please enter your Anthropic API key in the sidebar to begin.")
else:
    with st.spinner("Loading Applied Photonics..."):
        collection = load_book_and_index()
    st.success(f"Book loaded — {collection.count()} passages indexed")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    if question := st.chat_input("Ask a question about Applied Photonics..."):
        with st.chat_message("user"):
            st.markdown(question)
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("assistant"):
            with st.spinner("Searching your book..."):
                try:
                    answer, pages = ask_book(question, collection, api_key, st.session_state.messages[:-1], page_min, page_max)
                    st.markdown(answer)
                    st.markdown(f"*Pages referenced: {pages}*")
                    col1, col2, col3 = st.columns([1, 1, 8])
                    with col1:
                        if st.button("👍", key=f"up_{len(st.session_state.messages)}"):
                            with open("feedback_log.txt", "a") as f:
                                f.write(f"HELPFUL | {question}\n")
                            st.success("Thanks!")
                    with col2:
                        if st.button("👎", key=f"down_{len(st.session_state.messages)}"):
                            with open("feedback_log.txt", "a") as f:
                                f.write(f"UNHELPFUL | {question}\n")
                            st.warning("Noted.")
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"Error: {e}")
    st.markdown("---")
    st.markdown("### Example questions")
    examples = ["What is Brewsters angle?", "Explain the V-number", "How does a Fabry-Perot cavity work?", "What is WDM?", "How does a semiconductor laser work?", "What is total internal reflection?"]
    cols = st.columns(3)
    for i, example in enumerate(examples):
        with cols[i % 3]:
            st.button(example, key=f"ex_{i}")
