import os
import time
from pathlib import Path
import streamlit as st
import httpx
from sarvamai import SarvamAI

# -----------------------------------------------------------------------------
# 1. Environment & API Key Setup
# -----------------------------------------------------------------------------
def load_env():
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.is_file():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip())

load_env()
api_key = os.environ.get("SARVAM_API_KEY")

st.set_page_config(
    page_title="Kya Karna Hai? | Document Explainer",
    page_icon="📄",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. Sarvam Document AI & LLM Helpers
# -----------------------------------------------------------------------------
@st.cache_resource
def get_sarvam_client():
    if not api_key:
        return None
    return SarvamAI(api_subscription_key=api_key)

def digitise_document(uploaded_file, client: SarvamAI) -> str:
    """Uploads file to Sarvam Document AI, polls until done, and extracts text."""
    file_bytes = uploaded_file.getvalue()
    filename = uploaded_file.name
    mime_type = uploaded_file.type or "application/octet-stream"

    # Start digitization job
    job = client.doc_ai.digitise(
        file=[(filename, file_bytes, mime_type)]
    )
    job_id = job.job_id

    # Poll status
    max_retries = 30
    for _ in range(max_retries):
        time.sleep(2)
        status_resp = client.doc_ai.get_status(job_id=job_id)
        if status_resp.status in ["completed", "partially_completed"]:
            break
        elif status_resp.status in ["failed", "rejected"]:
            raise RuntimeError(f"Document processing failed with status: {status_resp.status}")
    else:
        raise TimeoutError("Document processing timed out.")

    # Fetch raw results JSON using authenticated httpx request
    results_url = f"https://api.sarvam.ai/doc-ai/v1/job/{job_id}/results"
    headers = {"api-subscription-key": api_key}
    resp = httpx.get(results_url, headers=headers, timeout=30.0)
    resp.raise_for_status()
    data = resp.json()

    # Extract ordered text blocks from all pages
    extracted_lines = []
    for doc in data.get("documents", []):
        for page in doc.get("pages", []):
            page_num = page.get("page_num", 1)
            blocks = page.get("blocks", [])
            sorted_blocks = sorted(blocks, key=lambda b: b.get("reading_order", 0))
            page_texts = [b.get("text", "").strip() for b in sorted_blocks if b.get("text")]
            if page_texts:
                extracted_lines.append(f"--- Page {page_num} ---")
                extracted_lines.extend(page_texts)

    if not extracted_lines:
        raise ValueError("Could not extract any readable text from this document.")

    return "\n".join(extracted_lines)

def analyze_document_with_sarvam(document_text: str, client: SarvamAI) -> str:
    """Calls sarvam-105b-conversations to generate the 5 essential answers."""
    prompt = f"""You are 'Kya Karna Hai?', a helpful and empathetic AI assistant built for Indian citizens to demystify complex, intimidating, or confusing real-world documents (such as electricity bills, water bills, traffic challans, government notices, legal letters, court summons, application forms, or insurance policies).

Based ONLY on the document text provided below, clearly explain the document by answering these 5 essential questions. Use simple, natural language (a friendly mix of English and Hinglish that anyone can easily understand):

### 1. 📄 What is this document?
Identify the exact document type and issuing authority/organization.

### 2. ⚡ What do I need to do?
Give clear, actionable, numbered steps on what the user must do next (e.g. pay online, visit office, fill a form).

### 3. ⏰ Is there a deadline?
Mention the exact due date or deadline. If no deadline is stated, say so clearly.

### 4. 💰 Is there an amount I need to pay?
State the exact amount due, late fee penalties if delayed, or say "₹0 / Not applicable" if no payment is needed.

### 5. ⚠️ What important things should I be aware of?
Highlight critical warnings, penalties, disconnection threats, or required documents to carry.

---
DOCUMENT CONTENT:
{document_text}
"""
    response = client.chat.completions(
        model="sarvam-105b-conversations",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content

# -----------------------------------------------------------------------------
# 3. Streamlit User Interface
# -----------------------------------------------------------------------------
st.title("Kya Karna Hai? 📄⚡")
st.caption("Upload any notice, bill, challan, or government letter — understand exactly what to do in seconds.")

if not api_key:
    st.error("SARVAM_API_KEY is not configured. Please add your key to `.env`.")
    st.stop()

client = get_sarvam_client()

# Session State Initialization
if "doc_text" not in st.session_state:
    st.session_state.doc_text = None
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "file_processed_name" not in st.session_state:
    st.session_state.file_processed_name = None

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("1. Upload Document")
    uploaded_file = st.file_uploader(
        "Upload a photo or PDF of the document",
        type=["png", "jpg", "jpeg", "pdf"],
        help="Upload notices, bills, challans, or forms in English or any Indian language."
    )

    if uploaded_file is not None:
        if uploaded_file.type.startswith("image"):
            st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)
        else:
            st.info(f"PDF uploaded: {uploaded_file.name} ({round(uploaded_file.size / 1024, 1)} KB)")

        process_button = st.button("🚀 Analyze Document", type="primary", use_container_width=True)

        if process_button:
            with st.spinner("Extracting text using Sarvam Document AI..."):
                try:
                    extracted_text = digitise_document(uploaded_file, client)
                    st.session_state.doc_text = extracted_text
                    st.session_state.file_processed_name = uploaded_file.name
                    st.session_state.chat_history = []  # Reset chat for new doc
                except Exception as e:
                    st.error(f"Failed to extract document: {e}")
                    st.stop()

            with st.spinner("Analyzing document with Sarvam 105B Conversations..."):
                try:
                    analysis = analyze_document_with_sarvam(st.session_state.doc_text, client)
                    st.session_state.analysis = analysis
                    st.success("Analysis complete!")
                except Exception as e:
                    st.error(f"Failed to analyze document: {e}")
                    st.stop()

    if st.session_state.doc_text:
        with st.expander("🔍 View Raw Extracted Text (Sarvam Doc AI)"):
            st.text(st.session_state.doc_text)

with col2:
    st.subheader("2. Kya Karna Hai? (Explanation)")
    if st.session_state.analysis:
        st.markdown(st.session_state.analysis)
    else:
        st.info("Upload a document on the left and click **'🚀 Analyze Document'** to get the 5-point explanation.")

st.divider()

# -----------------------------------------------------------------------------
# 4. Interactive Follow-up Chat
# -----------------------------------------------------------------------------
st.subheader("3. Ask Follow-up Questions (Hindi / Hinglish / English)")

if not st.session_state.doc_text:
    st.info("Upload and analyze a document first to ask follow-up questions.")
else:
    st.caption("Ask questions like: *'Late fees kitna lagega?'*, *'Payment online kaise karein?'*, *'Yeh notice fake toh nahi lag raha?'*")

    # Render previous conversation
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    user_query = st.chat_input("Apna sawal yahan poochein (Ask your question here)...")
    if user_query:
        # Display user query
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        # Build prompt messages for Sarvam 105B Conversations
        system_instruction = (
            "You are 'Kya Karna Hai?', an assistant helping the user understand their uploaded document.\n"
            "Answer the user's question accurately and simply based on the document text provided below.\n"
            "If the question is in Hindi or Hinglish, reply in friendly Hindi/Hinglish.\n\n"
            f"DOCUMENT CONTENT:\n{st.session_state.doc_text}"
        )

        llm_messages = [{"role": "system", "content": system_instruction}]
        for msg in st.session_state.chat_history:
            llm_messages.append({"role": msg["role"], "content": msg["content"]})

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    resp = client.chat.completions(
                        model="sarvam-105b-conversations",
                        messages=llm_messages,
                        temperature=0.3,
                    )
                    reply = resp.choices[0].message.content
                    st.markdown(reply)
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                except Exception as e:
                    st.error(f"Error getting reply from Sarvam: {e}")
