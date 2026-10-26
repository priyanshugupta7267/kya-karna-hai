# Kya Karna Hai? 📄⚡

> **Demystifying confusing notices, bills, challans, and government letters for Indian citizens in seconds.**

"Kya Karna Hai?" is an AI-powered document explainer built for Indian citizens. When faced with confusing, dense, or intimidating real-world paperwork (such as electricity bills, water bills, traffic challans, municipal tax notices, court summons, or warranty cards), users simply upload a photo or PDF. The app breaks down the document into five clear, practical answers and offers interactive follow-up Q&A in Hindi, Hinglish, or English.

---

## 🌟 Features

1. **Upload Any Real-World Document**: Supports JPG, PNG, and PDF (scans, camera captures, and digital documents).
2. **5-Point Instant Breakdown**:
   - 📄 **What is this document?** (Document type and issuing authority)
   - ⚡ **What do I need to do?** (Actionable, step-by-step next actions)
   - ⏰ **Is there a deadline?** (Due dates, cutoff dates)
   - 💰 **Is there an amount I need to pay?** (Payable amounts, penalties)
   - ⚠️ **Key warnings & implications** (Disconnection threats, late fee escalations, legal consequences)
3. **Interactive Multilingual Chat**: Ask follow-up questions in natural Hindi, Hinglish, or English (e.g., *"Late fees kitna lagega agar late payment kiya toh?"*).

---

## 🤖 Sarvam AI Models & APIs Used

- **Sarvam Document Intelligence (`DocAiClient.digitise`)**:
  - Uses `sarvam-vision` to parse complex document layouts, tabular data, and Indic text across Indian languages and English.
- **Sarvam Chat Completions (`sarvam-105b-conversations`)**:
  - Powers the 5-point explanation engine and the conversational follow-up chat with deep awareness of Indian administrative and legal context.

---

## 🚀 Quick Setup & Run

### 1. Prerequisites
- Python 3.9+ installed
- Sarvam AI API Key (from [Sarvam AI Dashboard](https://dashboard.sarvam.ai))

### 2. Clone and Install Dependencies

```bash
git clone <your-repo-url>
cd "kya karna hai"
pip install -r requirements.txt
```

### 3. Configure API Key

Copy `.env.example` to `.env` and insert your Sarvam API key:

```bash
cp .env.example .env
```

Edit `.env`:
```env
SARVAM_API_KEY=your_sarvam_api_key_here
```

> **Note**: `.env` is ignored by git and will never be committed.

### 4. Run the Application

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## 📂 Project Structure

```text
├── app.py              # Streamlit web application & Sarvam AI workflow
├── main.py             # Minimal script to test Sarvam SDK connection
├── sample_notice.png   # Sample test electricity notice
├── requirements.txt    # Project dependencies
├── .env.example        # Environment variable template
├── .gitignore          # Git ignore rules (prevents .env leaks)
└── README.md           # Project documentation
```
